# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Strategy arrangement returning a valid broker result directly."""

from dataclasses import dataclass

from strategy_base import StrategyBase

from ataraxia.bar import Bar
from ataraxia.broker import Account, BrokerReturn


class SinkResultRunner:
    """Return an empty, valid broker result for each source Bar."""

    def __call__(self, item: Bar) -> BrokerReturn:
        return {
            "account": Account(),
            "open_positions": [],
            "closed_positions": [],
        }


@dataclass(frozen=True)
class SinkResultStrategy(StrategyBase):
    """Return the runner's valid result without a broker consumer."""

    def factory(self) -> SinkResultRunner:
        return SinkResultRunner()

    def consumer(self) -> None:
        return None


__sink__: type[SinkResultStrategy] = SinkResultStrategy
