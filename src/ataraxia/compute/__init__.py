# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Computation engine.

An elastic computation model with dependency injection.
"""

from .protocols import Computable, Dependency, DependencyMapping, Runner

__all__ = [Computable, Runner, Dependency, DependencyMapping]
