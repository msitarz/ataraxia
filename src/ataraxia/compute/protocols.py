# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Protocols for the computation engine."""

from collections.abc import Hashable, Mapping
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Runner[**P, R](Protocol):
    """Defines execution unit within the computable graph."""

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """Return computed value."""
        ...


type Dependency[**P, R] = Computable[P, R]
type DependencyMapping = Mapping[str, Dependency[..., Any]]


@runtime_checkable
class Computable[**P, R](Hashable, Protocol):
    """Computable graph node.

    Defines specification of a computable node in the computable graph.
    """

    def deps(self) -> DependencyMapping:
        """Return dependencies of this computable, inputs to the runner.

        Mapping key will be unpacked into runner call.  Match dependency names with
        runner __call__ method parameter names.
        """
        ...

    def factory(self) -> Runner[P, R]:
        """Return instance of this computable execution unit."""
        ...
