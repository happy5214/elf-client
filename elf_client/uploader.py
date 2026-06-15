"""FactorDB/mersenne.ca aliquot sequence uploader.

This module uploads an ELF file for an aliquot sequence from FactorDB or mersenne.ca.
"""

import itertools
import subprocess
import time

import requests

from .client import ElfClient, FactorDBElfClient


class ElfUploader(ElfClient):
    """Base class for an ELF file uploader."""

    def read_and_upload_elf(self) -> None:
        self.validate_elf()
        self.upload_elf()

    def upload_elf(self) -> None:
        raise NotImplementedError()


class FactorDBElfUploader(ElfUploader, FactorDBElfClient):
    """A FactorDB ELF file uploader."""

    def __init__(self, sequence_base: int, sequence_power: int, attempts: int):
        super().__init__(sequence_base, sequence_power, attempts)
        self.cookies = self._get_cookies()

    def upload_elf(self) -> None:
        print('Uploading to FactorDB...')
        with open(f'alq_{self.actual_start_value}.elf', 'rt') as elf_file:
            self.elf_contents = list(map(ElfClient.parse_elf_line, elf_file))
        for batch in itertools.batched(self.elf_contents, 50):
            self._upload_batch(batch)

    def _upload_batch(self, batch: tuple[tuple[int, str]]) -> None:
        lines = map(lambda x: f'{x[0]} = {x[1]}', batch)
        params = {'format': '7', 'report': '\n'.join(lines)}
        for i in range(self.attempts):
            try:
                with requests.post('https://factordb.com/report.php', params=params, cookies=self.cookies) as r:
                    if r.ok:
                        return
            except requests.exceptions.ChunkedEncodingError:
                pass
            print('Upload error, sleeping 5 seconds...')
            time.sleep(5)
        raise RuntimeError('Exceeded attempt limit on a batch')


class MersenneCAElfUploader(ElfUploader):
    """A mersenne.ca ELF file uploader."""

    def upload_elf(self) -> None:
        print('Uploading to mersenne.ca...')
        with open(f'alq_{self.actual_start_value}.elf', 'rb') as elf_file:
            files = {'elf_file': elf_file}
            with requests.post(f'https://www.mersenne.ca/factordb/elf/index.php', files=files) as r:
                if r.status_code == requests.codes.created:
                    print('Uploaded to mersenne.ca.')
                elif r.status_code == requests.codes.forbidden:
                    raise RuntimeError('ELF file already on mersenne.ca and locked; overwriting not allowed')
                elif r.status_code == requests.codes.conflict:
                    raise RuntimeError('ELF file already on mersenne.ca; overwriting not yet implemented')
                else:
                    raise RuntimeError(f'mersenne.ca returned an error: {r.status_code}')
