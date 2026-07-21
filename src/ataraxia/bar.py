# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Bar dataclass."""

from collections.abc import Mapping
from dataclasses import dataclass
import re

DOT_PATTERN = re.compile(r"\.")


@dataclass(frozen=True)
class Bar:
    """OHLCV data container for futures data."""

    timestamp: int
    open: int
    high: int
    low: int
    close: int
    volume: int

    @classmethod
    def from_map(cls, bar_map: Mapping[str, str]):
        """Return normalized Bar instantiated from map str values."""
        return cls(**{k: cls._normalize(v) for k, v in bar_map.items()})

    @classmethod
    def _normalize(cls, value: str):
        """Return value as int normalized to ticks."""
        if DOT_PATTERN.search(value):
            return int(float(value) * 4)
        else:
            return int(value)

    def within(self, value: int) -> bool:
        """Return True if value within bar's range, False otherwise."""
        return value >= self.low and value <= self.high
