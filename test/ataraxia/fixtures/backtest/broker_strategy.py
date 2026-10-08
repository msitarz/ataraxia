# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Strategy arrangement consumed by the real broker."""

from dataclasses import dataclass

from strategy_base import Strategy

from ataraxia.broker import Broker


@dataclass(frozen=True)
class BrokerStrategy(Strategy):
    """Send the source-driven signal into the broker."""

    def consumer(self) -> Broker:
        return Broker(self.source, self)


__sink__: type[BrokerStrategy] = BrokerStrategy
