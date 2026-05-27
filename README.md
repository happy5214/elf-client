# download-elf

This script is a Python-based downloader for `.elf`-format aliquot sequence
files. It can download files from either [FactorDB](https://factordb.com/)
or [James Heinrich's cache at mersenne.ca](https://www.mersenne.ca/factordb/elf/),
defaulting to the latter, more reliable option when possible.

## Requirements

- Python 3.10+ (it may work with older versions, but I have not tested this)
- [requests](https://pypi.org/project/requests/)

The requirements list is also embedded in the script for the benefit of script
runners like `uv`.

## Basic usage instructions

```
python3 download_elf.py <sequence_start>
```

For more detailed help, run the following:

```
python3 download_elf.py --help
```

## FactorDB login

Copy the `factordb_user.ini.example` file to `factordb_user.ini` and insert
your FactorDB username and password to use your FactorDB login when downloading
`.elf` files from that site. This is particularly relevant if you have an
account with higher data limits.

## License

This code is written by Alexander Jones (happy5214) and released under the MIT
License.
