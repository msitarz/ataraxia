# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Features module.

Provide basic features for the computation model.
"""

from collections import deque
from collections.abc import Collection
from dataclasses import dataclass
from typing import ClassVar, NamedTuple, override

from ataraxia.bar import Bar
from ataraxia.compute import Computable, Runner

# ================
# Bar Compute Node
# ================


class BarNode(Runner[[], Bar]):
    """Current bar processed in the computation loop."""

    def __call__(self, bar: Bar):
        """Bar entry point in the computation tree.

        Returns:
            bar: the received input.
        """
        return bar


@dataclass(frozen=True)
class BarSpec(Computable[[], Bar]):
    """Compute specification for the current bar in the loop."""

    compute_node: ClassVar[type[BarNode]] = BarNode

    @override
    def dependencies(self):
        """Dependencies for bar are simply.

        Returns:
            Tuple with type Bar dependency for DI.
        """
        return (Bar,)

    @override
    def factory(self):
        return BarNode()


# ===========================
# Rolling Window Compute Node
# ===========================


class RollingWindowParams(NamedTuple):
    """Parameters for RollingWindow specification."""

    maxlen: int


class RollingWindowNode[T](Runner[[T], tuple[T, ...]]):
    """Container node implementing rolling window."""

    queue: deque[T]

    def __init__(self, maxlen: int):
        self.queue = deque(maxlen=maxlen)

    def __call__(self, item: T):
        """Accumulate item.

        Returns:
            Accumulated items in a tuple.
        """
        self.queue.appendleft(item)
        return tuple(self.queue)


@dataclass(frozen=True)
class RollingWindowSpec[T]:
    """Specification for rolling window container.

    It means to be further specialized rather than used directly to provide valid
    dependency specification.
    """

    init_params: RollingWindowParams
    compute_node: ClassVar = RollingWindowNode

    def dependencies(self):
        """Subclass must provide implementation."""
        raise NotImplementedError("Subclass must provide implementation")

    def factory(self):
        """Return RollingWindowNode instance."""
        return self.compute_node[T](*self.init_params)


# ===========================
# Rolling Bar Window
# ===========================


@dataclass(frozen=True)
class RollingBarSpec(RollingWindowSpec[Bar]):
    """Rolling Bar Window specification."""

    @override
    def dependencies(self):
        return (Bar,)


# ===========================
# SMA Compute Node
# ===========================

type SmaReturnType = float


def sma(items: Collection[SmaReturnType], period: int):
    """Simple Moving Average.

    Args:
        items: Collection of numbers to calculate sma on.
        period: Period parameter for sma.

    Returns:
        Number of calculated sma or None if items not long enough.

    Raises:
        ValueError: When `items` longer than `period`.
    """
    if len(items) < period:
        return None
    elif len(items) > period:
        raise ValueError("Items cannot be longer than period")

    return sum(items) / len(items)


class SmaParams(NamedTuple):
    """Parameter class for SMA node."""

    period: int


@dataclass(frozen=True)
class SmaNode:
    """Compute node for sma."""

    period: int

    def __call__(self, bars: Collection[Bar]):
        """Return SMA for `bars`."""
        return sma(tuple(b.close for b in bars), self.period)


@dataclass(frozen=True)
class SmaSpec:
    """SMA specification."""

    init_params: SmaParams
    compute_node: ClassVar = SmaNode

    def dependencies(self):
        """Return compute node dependencies."""
        return (RollingBarSpec(RollingWindowParams(self.init_params.period)),)

    def factory(self):
        """Return compute node instance."""
        return self.compute_node(*self.init_params)
