"""FactorDB/mersenne.ca aliquot sequence downloader.

This module downloads an ELF file for an aliquot sequence from FactorDB or mersenne.ca.
"""

import itertools
import sys
import time

import requests

from .client import ElfClient, FactorDBElfClient


class ElfDownloader(ElfClient):
    """Base class for an ELF file downloader."""

    def download_and_write_elf(self) -> None:
        for i in range(self.attempts):
            self.download_elf()
            validated = self.write_elf()
            if validated:
                return
        print(f'Failed to validate ELF file after {self.attempts} attempts, stopping...', file=sys.stderr)

    def download_elf(self) -> list[tuple[int, str]]:
        raise NotImplementedError()

    def write_elf(self) -> bool:
        if not self.elf_contents:
            print('ELF file is empty, cannot validate...', file=sys.stderr)
            return False
        with open(f'alq_{self.actual_start_value}.elf', 'wt') as elf_file:
            for i, line in enumerate(self.elf_contents):
                print(f'{i} .   {line[0]} = {line[1]}', file=elf_file)
        try:
            self.validate_elf()
            return True
        except RuntimeError as error:
            print(error, file=sys.stderr)
            return False


class FactorDBElfDownloader(ElfDownloader, FactorDBElfClient):
    """A FactorDB ELF file downloader."""

    def __init__(self, sequence_base: int, sequence_power: int, attempts: int, expected_length: int):
        super().__init__(sequence_base, sequence_power, attempts)
        self.expected_length = expected_length
        self.elf_contents = []

    def download_elf(self) -> list[tuple[int, str]]:
        print('Downloading from FactorDB...')
        if self.expected_length is None:
            self._slice_end = None
            return self._actually_download_elf()
        self._slice_end = -1
        while len(self.elf_contents) < self.expected_length + 1:
            print(f'Download attempt {-self._slice_end}.')
            self._actually_download_elf()
            self._slice_end -= 1
        return self.elf_contents

    def _actually_download_elf(self) -> list[tuple[int, str]]:
        self.elf_contents = []
        if self.sequence_power > 1:
            base = f'{self.sequence_base}^{self.sequence_power}'
        else:
            base = self.sequence_base
        incomplete = True
        first_run = True
        already_exceeded = False
        cycle = False
        while incomplete:
            params = {'seq': base}
            temp_elf_contents = []
            try:
                with requests.get('https://factordb.com/elf.php', params=params, stream=True, cookies=self.cookies) as r:
                    line_count = 0
                    first_line = True
                    bad_file = False
                    for line in r.iter_lines(decode_unicode=True):
                        if 'html' in line:
                            bad_file = True
                            break
                        if first_line and not first_run:
                            first_line = False
                            continue
                        line_count += 1
                        parsed_line = ElfClient.parse_elf_line(line)
                        if not parsed_line[1]:
                            break
                        if parsed_line in self.elf_contents or parsed_line in temp_elf_contents:
                            cycle = True
                            temp_elf_contents.append(parsed_line)
                            break
                        temp_elf_contents.append(parsed_line)
                    incomplete = (bad_file or line_count > 0) and not cycle
            except requests.exceptions.ChunkedEncodingError:
                pass
            if temp_elf_contents:
                temp_max = max(map(lambda x: x[0], temp_elf_contents))
                if temp_max < 1e199 or already_exceeded:
                    self.elf_contents.extend(temp_elf_contents)
                elif self._slice_end is None:
                    raise RuntimeError('Expected length required for sequences exceeding 200 digits')
                else:
                    self.elf_contents.extend(tuple(itertools.takewhile(lambda x: x[0] < 1e199, temp_elf_contents))[0:self._slice_end])
                    already_exceeded = True
                base = self.elf_contents[-1][0]
            if bad_file:
                print('Download error, sleeping 5 seconds...')
                time.sleep(5)
            else:
                first_run = False
                size = max(0, len(self.elf_contents) - 1)
                print(f'Now at {size} lines.')
        return self.elf_contents


class MersenneCAElfDownloader(ElfDownloader):
    """A mersenne.ca ELF file downloader."""

    def download_elf(self) -> list[tuple[int, str]]:
        print('Downloading from mersenne.ca...')
        if self.sequence_power > 1:
            base = f'{self.sequence_base}p{self.sequence_power}'
        else:
            base = self.sequence_base
        with requests.get(f'https://www.mersenne.ca/factordb/elf/alq_{base}.elf') as r:
            if not r.ok:
                raise RuntimeError('ELF file not found on mersenne.ca')
            lines = r.text.splitlines()
            self.elf_contents = list(map(ElfClient.parse_elf_line, lines))
            line_count = max(0, len(self.elf_contents) - 1)
            if len(lines) != len(self.elf_contents):
                raise RuntimeError('ELF file from mersenne.ca has invalid lines')
            print(f'Downloaded {line_count} lines from mersenne.ca.')
            return self.elf_contents
