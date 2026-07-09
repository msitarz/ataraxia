# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Bar dataclass."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Bar:
    """Provides OHLCV bar data."""

    timestamp: int
    close: int
