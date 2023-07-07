# Vendored libraries in Python distributions

The data can be found in `packages-to-binaries.csv` which contains three rows:

- Package
- Binary
- Distribution (First encountered, may be more than one)

The data is captured for `.so`, `.pyd`, `.a`, and `.dll` files. All other files aren't captured in the dataset.

## How it works

- Query top packages that have binary distributions from `sethmlarson/pypi-data`
- Download all distributions for the latest release of those packages into `dists/`
- Extract the distributions one-by-one and perform an operation (like gathering binary filenames)

Downloading and extracting take a long time and space, if you don't absolutely need to reproduce the data
I recommend using the raw data under `packages-to-binaries.csv`. Much faster and resource-light that way!

## License

Apache-2.0
