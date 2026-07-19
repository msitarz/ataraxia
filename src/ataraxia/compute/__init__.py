# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Computation engine.

An elastic computation model with dependency injection.
"""

from .protocols import Computable, DependencyMapping, Runner, Sink, Source

__all__ = (
    "Computable",
    "DependencyMapping",
    "Runner",
    "Sink",
    "Source",
)
