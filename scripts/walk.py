import contextlib
import os.path
import pathlib
import re
import shutil
import tarfile
import tempfile
import zipfile

# Configuration
wheels_dir = (pathlib.Path(__file__).parent.parent / "dists").absolute()
wheels_dir.mkdir(exist_ok=True)
seen_keys = set()


def walk_extracted_dist(package: str, filename: str, extracted_filepath: str):
    global seen_keys
    for root, _, extracted_filenames in os.walk(extracted_filepath):
        for extracted_filename in extracted_filenames:
            if re.search(r"\.(?:so\.|\.so$|dll$|pyd$|a$)", extracted_filename):
                key = (package, extracted_filename)
                if key not in seen_keys:
                    print(f"{package},{extracted_filename},{filename}")
                    seen_keys.add(key)


@contextlib.contextmanager
def extract_to_filepath(filepath: str) -> str:
    # Create a temporary directory to unpack the files to.
    with tempfile.TemporaryDirectory() as tmp:
        # Wheels and eggs are zips
        if (
            filepath.endswith(".whl")
            or filepath.endswith(".zip")
            or filepath.endswith(".egg")
        ):
            with zipfile.ZipFile(filepath, "r") as zip:
                zip.extractall(tmp)
        elif filepath.endswith(".tar.gz") or filepath.endswith(".tgz"):
            with tarfile.open(filepath) as tar:
                tar.extractall(tmp)
        else:
            print(f"Unknown extension: {os.path.basename(filepath)}")

        yield tmp

    shutil.rmtree(tmp, ignore_errors=True)


def walk_filepaths():
    for package in sorted(os.listdir(wheels_dir)):
        package_dir = wheels_dir / package
        for filename in sorted(os.listdir(package_dir)):
            yield package, str(package_dir / filename)


def main():
    for package, filepath in walk_filepaths():
        try:
            with extract_to_filepath(filepath) as extracted_filepath:
                walk_extracted_dist(
                    package, os.path.basename(filepath), extracted_filepath
                )
        except (zipfile.BadZipfile, tarfile.TarError):
            continue


if __name__ == "__main__":
    main()
