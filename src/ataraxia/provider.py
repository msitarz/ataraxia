# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Providers module.

Providers deliver data to computable graph sources.
"""

from collections.abc import Hashable, Iterator
import csv
from dataclasses import dataclass
from io import TextIOBase
from pathlib import Path
from types import TracebackType
from typing import Protocol, Self, override, runtime_checkable

from .bar import Bar
from .errors import ProviderError

CSV_DELIMITER = ","
CSV_HEADER = ["timestamp", "open", "high", "low", "close", "volume"]


@runtime_checkable
class Provider[T](Hashable, Iterator[T], Protocol):
    """Define Provider that can be used to iterate over in the compute loop.

    It must implement a context manager protocol as there will most likely be operations
    such as file opening or network stream reading which require context management.

    Its use case is to return Provider instance from source node __iter__ method.

    It must be hashable due to most likely being a source node attribute.  As every
    computable node must be hashable, so must its attributes.
    """

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...


@dataclass
class BarProvider(Provider[Bar]):
    """Provide Bar data from a CSV file.

    The CSV file must be delimited with a comma.
    The CSV file must have a following header:
    timestamp,open,high,low,close,volume
    """

    filepath: str | Path
    fd: TextIOBase | None = None
    reader: csv.DictReader[str] | None = None

    @override
    def __enter__(self):
        self.fd = open(self.filepath)
        return self

    @override
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        if self.fd:
            self.fd.close()

    @override
    def __iter__(self):
        return self

    @override
    def __next__(self):
        reader = self._reader()
        return Bar.from_map(next(reader))

    def _reader(self):
        if self.reader is not None:
            return self.reader

        if self.fd is None:
            raise ProviderError("Use provider as context manager")

        header = self.fd.readline().strip().split(CSV_DELIMITER)

        if header != CSV_HEADER:
            raise ProviderError("CSV file must contain a header")

        self.reader = csv.DictReader(self.fd, fieldnames=header)

        return self.reader

    def __hash__(self):
        return hash(self.filepath)
