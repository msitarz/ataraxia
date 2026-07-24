# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Example simple moving average strategy."""

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
        fast_sma: tuple[float | None, float | None],
        slow_sma: tuple[float | None, float | None],
    ):
        """Return Signal on SMA crossover."""
        if not all(fast_sma) or not all(slow_sma):
            return None

        if fast_sma[1] < slow_sma[1] and fast_sma[0] >= slow_sma[0]:
            return Signal(
                side="buy", stop_loss=bar.close - 20, take_profit=bar.close + 30
            )
        elif fast_sma[1] > slow_sma[1] and fast_sma[0] <= slow_sma[0]:
            return Signal(
                side="sell", stop_loss=bar.close + 20, take_profit=bar.close - 30
            )

        return None


@dataclass(frozen=True)
class CrossoverStrategy:
    """Simple crossover strategy computable node."""

    source: Source

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
