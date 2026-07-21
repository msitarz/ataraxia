# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Computation engine.

An elastic computation model with dependency injection.
"""

from .loop import compute
from .protocol import Computable, Provider, Runner, Sink, Source

__all__ = ("Computable", "Provider", "Runner", "Sink", "Source", "compute")
