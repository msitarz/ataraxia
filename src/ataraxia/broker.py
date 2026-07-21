# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Broker computable."""

from dataclasses import dataclass, field
from typing import Literal, TypedDict

from .bar import Bar
from .compute import Sink, Source
from .errors import PositionError


@dataclass(frozen=True, kw_only=True)
class Signal:
    """Signal sent from the strategy to the broker.

    This class assumes that only the market order is used.
    """

    side: Literal["buy", "sell"]
    stop_loss: int
    take_profit: int


@dataclass(frozen=True, kw_only=True)
class Position(Signal):
    """Currently held position."""

    entry_bar: Bar
    entry_level: int = field(init=False)

    closing_bar: Bar | None = field(init=False, default_factory=lambda: None)
    closing_level: int | None = field(init=False, default_factory=lambda: None)
    closing_pnl: int | None = field(init=False, default_factory=lambda: None)

    def __post_init__(self):
        object.__setattr__(self, "entry_level", self.entry_bar.close)

    def on_bar(self, bar: Bar):
        """Return realized position value.

        This implementation is a happy path where exit is always at the order.

        Position orders are stop_loss and take_profit only.

        Raises:
            PositionError: When position is already closed,
        """
        if self.closing_bar:
            raise PositionError("Position closed")

        if bar.within(self.stop_loss):
            self.close(bar, self.stop_loss, -abs(self.entry_level - self.stop_loss))
        elif bar.within(self.take_profit):
            self.close(bar, self.take_profit, abs(self.take_profit - self.entry_level))

        if self.closing_bar:
            return self.closing_pnl

        return None

    def close(self, bar: Bar, level: int, pnl: int):
        """Close position."""
        object.__setattr__(self, "closing_bar", bar)
        object.__setattr__(self, "closing_level", level)
        object.__setattr__(self, "closing_pnl", pnl)


@dataclass
class Account:
    """Current account status."""

    pnl: int = 0
    unrealized_pnl: int = 0


class BrokerReturn(TypedDict):
    """Return type from BrokerRunner."""

    account: Account
    position: Position | None


@dataclass(frozen=True)
class BrokerRunner:
    """Simple broker implementation."""

    position: Position | None = None
    account: Account = field(default_factory=Account)

    def __call__(self, bar: Bar, signal: Signal) -> BrokerReturn:
        """Return current account and position objects."""
        return {"account": self.account, "position": self.position}


@dataclass(frozen=True)
class Broker:
    """Simple broker computable."""

    source: Source[Bar, ..., Bar]
    strategy: Sink[..., Signal]

    def deps(self):
        """Return broker dependencies."""
        return {
            "bar": self.source,
            "signal": self.strategy,
        }

    def factory(self):
        """Return Broker runner."""
        return BrokerRunner()
