# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Broker computable."""

from dataclasses import dataclass, field
from typing import Literal, TypedDict

from .bar import Bar
from .compute import Sink, Source


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

    bar: Bar
    entry: int = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "entry", self.bar.close)

    def on_bar(self, bar: Bar):
        """Return realized position value.

        Position orders are stop_loss and take_profit .
        """
        return None


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
