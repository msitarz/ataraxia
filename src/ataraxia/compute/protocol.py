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
class Source[T, **P, R](Iterable[T], Computable[P, R], Protocol):
    """Defines source node in the multi-source single-sink DAG of computables.

    Those nodes are used as input from the processed shard data in the compute loop.
    All computable nodes depend on source nodes.
    """

    def send(self, item: T) -> None:
        """Called by the compute loop with item yielded from the provider.

        Generally it should set runner's item which will be returned when compute
        graph calls it.
        """
        ...

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...


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
