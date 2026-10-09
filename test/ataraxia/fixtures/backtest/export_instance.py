# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Invalid strategy module exporting a Strategy(None) instance."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Strategy:
    """Fixture-local record for the deliberately invalid sink instance."""

    source: None


__sink__: Strategy = Strategy(None)
