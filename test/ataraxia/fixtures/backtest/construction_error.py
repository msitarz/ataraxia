# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Strategy arrangement whose sink constructor raises the retained error."""

from strategy_base import Strategy

from ataraxia.bar import Bar
from ataraxia.broker import Broker
from ataraxia.compute import Source


class ConstructionErrorStrategy(Strategy):
    """Raise the retained strategy error when backtest constructs the sink."""

    def __init__(self, source: Source[Bar, ..., Bar]) -> None:
        raise AttributeError("strategy bug")

    def consumer(self) -> Broker:
        return Broker(self.source, self)


__sink__: type[ConstructionErrorStrategy] = ConstructionErrorStrategy
