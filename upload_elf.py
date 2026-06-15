#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests<3",
# ]
# ///

"""FactorDB/mersenne.ca aliquot sequence uploader.

This script uploads an ELF file for an aliquot sequence to FactorDB or mersenne.ca.
"""

import argparse
import sys

from elf_client.uploader import FactorDBElfUploader, MersenneCAElfUploader


def main() -> int:
    args = parse_args()
    if args.use_factordb:
        elf_uploader = FactorDBElfUploader(args.sequence_base, args.sequence_power, args.upload_attempts)
    else:
        elf_uploader = MersenneCAElfUploader(args.sequence_base, args.sequence_power, args.upload_attempts)
    elf_uploader.read_and_upload_elf()
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FactorDB/mersenne.ca aliquot sequence uploader")
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
        "--upload-attempts",
        type=int,
        default=3,
        help="The maximum number of attempts allowed to upload a sequence before the script will fail.",
    )
    parser.add_argument(
        "--use-factordb",
        action='store_true',
        default=False,
        help="Upload to FactorDB instead of mersenne.ca.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())
