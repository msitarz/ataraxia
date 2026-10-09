# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Strategy arrangement that returns an integer instead of a broker result."""

from dataclasses import dataclass

from strategy_base import StrategyBase

from ataraxia.bar import Bar


class NumberResultRunner:
    """Return the retained invalid integer result for each source Bar."""

    def __call__(self, item: Bar) -> int:
        return 42


@dataclass(frozen=True)
class NumberResultStrategy(StrategyBase):
    """Expose the integer result through a real source-driven sink."""

    def factory(self) -> NumberResultRunner:
        return NumberResultRunner()

    def consumer(self) -> None:
        return None


__sink__: type[NumberResultStrategy] = NumberResultStrategy
