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


@dataclass
class BarProvider:
    """Provide Bar data from a CSV file.

    The CSV file must have a following header:
    timestamp,open,high,low,close,volume
    """

    filepath: str
    fd: TextIOBase | None = None
    reader: csv.DictReader[str] | None = None

    def __enter__(self):
        self.fd = open(self.filepath)
        self.reader = csv.DictReader(self.fd)
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback):
        if self.fd:
            self.fd.close()

    def __iter__(self):
        return self

    def __next__(self):
        if self.reader is None:
            raise ProviderError("Use provider as context manager")

        row = next(self.reader)
        return Bar.from_map(row)
