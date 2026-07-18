# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Compute loop module."""

from collections.abc import Mapping
from typing import Any

from ataraxia.compute import Computable, Runner


def prime_catalog(
    computables: tuple[Computable[..., Any], ...],
) -> Mapping[Computable[..., Any], Runner[..., Any]]:
    """Return catalog of instantiated runners of computables."""
    return {c: c.factory() for c in computables}
