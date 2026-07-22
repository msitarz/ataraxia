# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Protocols for the computation engine."""

from collections.abc import Hashable, Iterable, Mapping
from types import TracebackType
from typing import Any, Protocol, Self, runtime_checkable


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
class Provider[T](Hashable, Iterable[T], Protocol):
    """Define Provider that can be used to iterate over in the compute loop.

    It must implement a context manager protocol as there will most likely be operations
    such as file opening or network stream reading which require context management.
    """

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...


@runtime_checkable
class Source[T, **P, R](Computable[P, R], Protocol):
    """Defines source node in the multi-source single-sink DAG of computables.

    Those nodes are used as input from the processed shard data in the compute loop.
    All computable nodes depend on source nodes.
    """

    def send(self, item: T) -> None:
        """Send item as the next runner's return value."""
        ...

    def provider(self) -> Provider[T]:
        """Return Provider for this source node.

        Provider will be iterated over in the compute loop and its yielded values will
        be injected via send method to the Source node.
        """
        ...


@runtime_checkable
class Sink[**P, R](Computable[P, R], Protocol):
    """Defines sink node in the multi-source single-sink DAG of computables.

    The sink node will be a strategy computable node in the backtest.
    """

    def sources(self) -> tuple[Source[Any, ..., Any], ...]:
        """Return all sources used in the computable."""
        ...

    def consumer(self) -> Computable[..., Any] | None:
        """Return consumer of the sink or None.

        Consumer could be aggregating sink's return values or provide final computation.
        For example, it can be a broker computable.
        """
        ...
