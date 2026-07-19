# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Protocols for the computation engine."""

from collections.abc import Hashable, Iterable, Mapping
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Runner[**P, R](Protocol):
    """Defines execution unit within the computable graph."""

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """Return computed value."""
        ...


type DependencyMapping = Mapping[str, Computable[..., Any]]


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


@runtime_checkable
class Source[T, **P, R](Iterable[T], Computable[P, R], Protocol):
    """Defines source node in the multi-source single-sink DAG of computables.

    Those nodes are used as input from the processed shard data in the compute loop.
    All computable nodes depend on source nodes.
    """

    def send(self, item: T) -> None:
        """Send item as the next computable runner return value."""
        ...


@runtime_checkable
class Sink[**P, R](Computable[P, R], Protocol):
    """Defines sink node in the multi-source single-sink DAG of computables.

    The sink node will be a strategy computable node in the backtest.
    """

    def sources(self) -> tuple[Source[Any, ..., Any], ...]:
        """Return all sources used in the computable."""
        ...
