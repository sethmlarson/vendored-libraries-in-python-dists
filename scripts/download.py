import asyncio
import hashlib
import pathlib
import sqlite3

import aiohttp
import aiohttp_retry

# Configuration
number_of_workers = 8
top_n_binary_wheel_packages = 100
chunk_size = 100 * 1024 * 1024
wheels_dir = (pathlib.Path(__file__).parent.parent / "dists").absolute()
wheels_dir.mkdir(exist_ok=True)

# Database
db = sqlite3.connect("../pypi.db")


async def fetch_dists_for_package(http: aiohttp.ClientSession, package: str) -> None:
    # Create the package's directory if it doesn't already exist.
    package_dir = wheels_dir / package
    package_dir.mkdir(parents=True, exist_ok=True)

    # Get the top-level list of downloadable files from PyPI.
    async with http.request("GET", f"https://pypi.org/pypi/{package}/json") as resp:
        assert resp.status == 200
        data = await resp.json()
        print(f"Downloading {package}...")

    for url in data["urls"]:
        # Grab all the data we need per-file.
        digest_sha256 = url["digests"]["sha256"]
        filename = url["filename"]
        download_url = url["url"]
        filepath = package_dir / filename

        # Check if the wheel file already exists, if it does
        # then we check that the digest to see that it isn't
        # a partial or corrupted download.
        if filepath.exists():
            if (
                hashlib.file_digest(filepath.open(mode="rb"), "sha256").hexdigest()
                == digest_sha256
            ):
                continue

        # Download the file.
        filepath.unlink(missing_ok=True)
        async with http.request("GET", download_url) as resp:
            print(f"Downloading {download_url}")
            assert resp.status == 200
            with filepath.open(mode="wb") as f:
                f.truncate()
                while chunk := await resp.content.read(chunk_size):
                    f.write(chunk)


async def main():
    # Get top packages which have a binary wheel.
    cur = db.execute(
        "SELECT name FROM packages WHERE has_binary_wheel ORDER BY downloads DESC LIMIT ?;",
        (top_n_binary_wheel_packages,),
    )
    packages = [x.lower() for x, in cur.fetchall()]

    # Configure an HTTP client that is resilient but won't overwhelm the host.
    connector = aiohttp.TCPConnector(limit=number_of_workers)
    session = aiohttp.ClientSession(connector=connector)
    options = aiohttp_retry.ExponentialRetry(
        attempts=10,
        exceptions={aiohttp.ClientTimeout},
        retry_all_server_errors=True,
    )
    async with aiohttp_retry.RetryClient(session, retry_options=options) as http:
        # Start downloading all the dists.
        futs = []
        for package in packages:
            futs.append(fetch_dists_for_package(http, package))
        await asyncio.gather(*futs)


if __name__ == "__main__":
    asyncio.run(main())
