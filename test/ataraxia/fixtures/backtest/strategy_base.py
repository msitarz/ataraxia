# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Typed source-driven strategy arrangements for backtest tests."""

from dataclasses import dataclass

from ataraxia.bar import Bar
from ataraxia.broker import Signal
from ataraxia.compute import Source
from ataraxia.compute.protocol import DependencyMapping


@dataclass(frozen=True)
class StrategyBase:
    """Pass one source Bar to a strategy runner."""

    source: Source[Bar, ..., Bar]

    def deps(self) -> DependencyMapping:
        return {"item": self.source}

    def sources(self) -> tuple[Source[Bar, ..., Bar], ...]:
        return (self.source,)


class SignalRunner:
    """Return the retained buy signal for each source Bar."""

    def __call__(self, item: Bar) -> Signal:
        return Signal(side="buy", stop_loss=100, take_profit=200)


@dataclass(frozen=True)
class Strategy(StrategyBase):
    """Provide the retained source-driven Signal runner."""

    def factory(self) -> SignalRunner:
        return SignalRunner()
