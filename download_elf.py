#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests<3",
# ]
# ///

"""FactorDB/mersenne.ca aliquot sequence downloader.

This script downloads an ELF file for an aliquot sequence from FactorDB or mersenne.ca.
"""

import argparse
import sys

from elf_client.downloader import FactorDBElfDownloader, MersenneCAElfDownloader


def main() -> int:
    args = parse_args()
    if args.use_factordb:
        elf_downloader = FactorDBElfDownloader(args.sequence_base, args.sequence_power, args.validation_attempts, args.expected_length)
    else:
        elf_downloader = MersenneCAElfDownloader(args.sequence_base, args.sequence_power, args.validation_attempts)
    try:
        elf_downloader.download_and_write_elf()
    except RuntimeError as error:
        if isinstance(elf_downloader, MersenneCAElfDownloader):
            print(f'Could not download ELF file from mersenne.ca: {error}.')
            print('Attempting to download from FactorDB instead.')
            elf_downloader = FactorDBElfDownloader(args.sequence_base, args.sequence_power, args.validation_attempts, args.expected_length)
            elf_downloader.download_and_write_elf()
        else:
            raise RuntimeError('Failed to download from FactorDB') from error
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FactorDB/mersenne.ca aliquot sequence downloader")
    parser.add_argument(
        "sequence_base",
        type=int,
        help="The starting value of the sequence. If the start value is a perfect power, this is the base.",
    )
    parser.add_argument(
        "sequence_power",
        type=int,
        default=1,
        nargs='?',
        help="The starting value exponent for the sequence.",
    )
    parser.add_argument(
        "--expected-length",
        type=int,
        default=None,
        help="The expected length of the sequence. If the sequence is shorter, this script will try alternative download techniques until it matches.",
    )
    parser.add_argument(
        "--validation-attempts",
        type=int,
        default=3,
        help="The maximum number of attempts allowed to validate a sequence before the script will fail. Requires aliqueit to be configured.",
    )
    parser.add_argument(
        "--use-factordb",
        action='store_true',
        default=False,
        help="Use FactorDB instead of the cached files on mersenne.ca. FactorDB may be less reliable, but the data will always be current.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())
