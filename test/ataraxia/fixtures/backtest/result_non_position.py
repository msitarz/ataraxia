# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Strategy arrangement whose closed positions contain a non-Position value."""

from dataclasses import dataclass
from typing import TypedDict

from strategy_base import StrategyBase

from ataraxia.bar import Bar
from ataraxia.broker import Account, Position


class NonPositionResult(TypedDict):
    """Precisely type the retained result with an invalid closed-position member."""

    account: Account
    open_positions: list[Position]
    closed_positions: list[object]


class NonPositionResultRunner:
    """Return the retained structurally invalid broker result."""

    def __call__(self, item: Bar) -> NonPositionResult:
        return {
            "account": Account(),
            "open_positions": [],
            "closed_positions": [object()],
        }


@dataclass(frozen=True)
class NonPositionResultStrategy(StrategyBase):
    """Expose the invalid result through a real source-driven sink."""

    def factory(self) -> NonPositionResultRunner:
        return NonPositionResultRunner()

    def consumer(self) -> None:
        return None


__sink__: type[NonPositionResultStrategy] = NonPositionResultStrategy
