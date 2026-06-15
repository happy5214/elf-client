"""FactorDB/mersenne.ca aliquot sequence client."""

import configparser
import http.cookiejar
import math
import re
import subprocess
import time
from typing import Optional

import requests


class ElfClient:
    """Base class for an ELF file client."""

    def __init__(self, sequence_base: int, sequence_power: int, attempts: int):
        self.sequence_base = sequence_base
        self.sequence_power = sequence_power
        if math.log10(sequence_base) * sequence_power > 240:
            raise ValueError('Start value is excessively large')
        self.actual_start_value = sequence_base ** sequence_power
        self.attempts = attempts
        self.config = self._get_config()

    def validate_elf(self) -> None:
        if self.config.has_option('Programs', 'aliqueit'):
            print('aliqueit is configured, validating ELF file...')
            process = subprocess.run([self.config['Programs']['aliqueit'], '-t', str(self.actual_start_value)])
            if process.returncode == 0:
                print('ELF file validation succeeded.')
            else:
                raise RuntimeError('ELF file validation failed')
        else:
            print('aliqueit is not configured, skipping validation...')

    @staticmethod
    def parse_elf_line(elf_line: str) -> tuple[int, Optional[str]]:
        elf_line_format = r'^\d+ \.\s+(\d+) = (\d+(?:\^\d+)?(?: \* \d+(?:\^\d+)?)*)?$'
        match = re.match(elf_line_format, elf_line)
        if match:
            return (int(match[1]), match[2])
        else:
            return (0, None)

    def _get_config(self) -> Optional[configparser.ConfigParser]:
        config = configparser.ConfigParser()
        config.read('factordb_user.ini')
        if config.sections():
            return config
        else:
            return None


class FactorDBElfClient(ElfClient):
    """Base class for a FactorDB ELF file client."""

    def __init__(self, sequence_base: int, sequence_power: int, attempts: int):
        super().__init__(sequence_base, sequence_power, attempts)
        self.cookies = self._get_cookies()

    def _get_cookies(self) -> http.cookiejar.CookieJar:
        if not self.config:
            print('Running anonymously.')
            return requests.cookies.cookiejar_from_dict(dict())
        login_info = self.config['Account']

        user = login_info['User']
        if self.config.has_option('Account', 'Cookie'):
            print(f'Logged in as {user} using existing cookie.')
            return requests.cookies.cookiejar_from_dict({'fdbuser': login_info['Cookie']})

        params = {
            'user': user,
            'pass': login_info['Password'],
            'dlogin': 'Login',
        }

        r = requests.post('https://factordb.com/login.php', params)

        while not r.cookies.get('fdbuser'):
            print('Login error, sleeping 5 seconds...')
            time.sleep(5)
            r = requests.post('https://factordb.com/login.php', params)
            while r.status_code != 200:
                print('Login error, sleeping 5 seconds...')
                time.sleep(5)
                r = requests.post('https://factordb.com/login.php', params)

        print(f'Logged in as {user}.')

        login_info['Cookie'] = r.cookies.get('fdbuser')

        with open('factordb_user.ini', 'wt') as config_file:
            self.config.write(config_file)

        return r.cookies
