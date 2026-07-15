# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Compute loop module."""

from collections.abc import Mapping
from typing import Any

from ataraxia.compute import Computable, Runner


def kickstart_runners(
    sorted_graph: tuple[Computable[..., Any], ...],
) -> Mapping[Computable[..., Any], Runner[..., Any]]:
    """Return instantiated runner catalog."""
    return {c: c.factory() for c in sorted_graph}
