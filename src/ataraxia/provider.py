# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Providers module.

Providers deliver data to computable graph sources.
"""

import csv
from dataclasses import dataclass
from io import TextIOBase

from .bar import Bar
from .errors import ProviderError

CSV_DELIMITER = ","
CSV_HEADER = ["timestamp", "open", "high", "low", "close", "volume"]


@dataclass
class BarProvider:
    """Provide Bar data from a CSV file.

    The CSV file must be delimited with a comma.
    The CSV file must have a following header:
    timestamp,open,high,low,close,volume
    """

    filepath: str
    fd: TextIOBase | None = None
    reader: csv.DictReader[str] | None = None

    def __enter__(self):
        self.fd = open(self.filepath)
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback):
        if self.fd:
            self.fd.close()

    def __iter__(self):
        return self

    def __next__(self):
        reader = self._reader()
        return Bar.from_map(next(reader))

    def _reader(self):
        if self.reader is not None:
            return self.reader

        if self.fd is None:
            raise ProviderError("Use provider as context manager")

        # strip newline via [:-1] as readline appends it
        header = self.fd.readline()[:-1].split(CSV_DELIMITER)

        if header != CSV_HEADER:
            raise ProviderError("CSV file must contain a header")

        self.reader = csv.DictReader(self.fd, fieldnames=header)

        return self.reader
