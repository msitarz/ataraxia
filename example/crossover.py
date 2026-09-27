# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Example simple moving average strategy."""

from collections.abc import Sequence
from dataclasses import dataclass

from ataraxia.bar import Bar
from ataraxia.broker import Broker, Signal
from ataraxia.compute import Source
from ataraxia.feature import RollingWindow, Sma


class CrossoverRunner:
    """Simple Moving Average crossover strategy."""

    def __call__(
        self,
        bar: Bar,
        fast_sma: Sequence[float | None],
        slow_sma: Sequence[float | None],
    ) -> Signal | None:
        """Return Signal on SMA crossover."""
        if len(fast_sma) < 2 or len(slow_sma) < 2:
            return None

        fast_current, fast_previous = fast_sma[:2]
        slow_current, slow_previous = slow_sma[:2]
        if (
            fast_current is None
            or fast_previous is None
            or slow_current is None
            or slow_previous is None
        ):
            return None

        if fast_previous < slow_previous and fast_current >= slow_current:
            return Signal(
                side="buy", stop_loss=bar.close - 20, take_profit=bar.close + 30
            )
        elif fast_previous > slow_previous and fast_current <= slow_current:
            return Signal(
                side="sell", stop_loss=bar.close + 20, take_profit=bar.close - 30
            )

        return None


@dataclass(frozen=True)
class CrossoverStrategy:
    """Simple crossover strategy computable node."""

    source: Source[Bar, ..., Bar]

    def deps(self):
        """Return dependencies for the runner."""
        return {
            "bar": self.source,
            "fast_sma": RollingWindow(from_node=Sma(self.source, period=12), maxlen=2),
            "slow_sma": RollingWindow(from_node=Sma(self.source, period=26), maxlen=2),
        }

    def factory(self):
        """Return runner."""
        return CrossoverRunner()

    def sources(self):
        """Return strategy sources."""
        return (self.source,)

    def consumer(self):
        """Return broker as the consumer of the sink."""
        return Broker(self.source, self)


__sink__ = CrossoverStrategy
