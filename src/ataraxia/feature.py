# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Basic features as computable nodes."""

from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass

from ataraxia.bar import Bar
from ataraxia.compute import Computable
from ataraxia.errors import FeatureError


class RollingWindowRunner[T]:
    """Accumulate items.

    It accumulates items in reverse chronological order, meaning the most recent item is
    at the start of returned tuple.
    """

    maxlen: int
    q: deque[T]

    def __init__(self, maxlen: int):
        self.maxlen = maxlen
        self.q = deque(maxlen=maxlen)

    def __call__(self, item: T) -> tuple[T, ...]:
        """Return accumulated items as a tuple."""
        self.q.appendleft(item)
        return tuple(self.q)


@dataclass(frozen=True)
class RollingWindow[T]:
    """Computable node used for accumulation.

    Uses RollingWindowRunner as implementation, so it accumulates items in reverse
    chronological order.
    """

    from_node: Computable[..., T]
    maxlen: int

    def deps(self):
        """Return dependencies for RollingWindow."""
        return {"item": self.from_node}

    def factory(self):
        """Return new RollingWindowRunner instance."""
        return RollingWindowRunner[T](self.maxlen)


def sma(values: Sequence[float], period: int) -> float | None:
    """Return simple moving average of period for values.

    Raises:
        FeatureError: When values have more items than period.
    """
    if len(values) < period or not all(values):
        return None
    elif len(values) > period:
        raise FeatureError("Cannot have more values than period")

    return sum(values) / period


@dataclass(frozen=True)
class SmaRunner:
    """Simple Moving Average."""

    period: int

    def __call__(self, bars: Sequence[Bar]):
        """Return simple moving average."""
        return sma(tuple(b.close for b in bars), self.period)


@dataclass(frozen=True)
class Sma:
    """Simple Moving Average computable from Bar source."""

    source: Computable[..., Bar]
    period: int

    def deps(self):
        """Return dependencies."""
        return {"bars": RollingWindow(from_node=self.source, maxlen=self.period)}

    def factory(self):
        """Return runner."""
        return SmaRunner(self.period)
