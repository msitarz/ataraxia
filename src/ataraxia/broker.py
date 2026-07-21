# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Broker computable."""

from collections.abc import MutableSequence, Sequence
from dataclasses import asdict, dataclass, field
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


class PositionOnBarReturn(TypedDict):
    """Return value of Position.on_bar method."""

    closed: bool
    pnl: int


@dataclass(frozen=True, kw_only=True)
class Position(Signal):
    """Track position data."""

    entry_bar: Bar
    entry_level: int = field(init=False)

    closing_bar: Bar | None = field(init=False, default_factory=lambda: None)
    closing_level: int | None = field(init=False, default_factory=lambda: None)
    closing_pnl: int | None = field(init=False, default_factory=lambda: None)

    def __post_init__(self):
        object.__setattr__(self, "entry_level", self.entry_bar.close)

    def on_bar(self, bar: Bar) -> PositionOnBarReturn:
        """Return realized position value.

        This implementation is a happy path where exit is always at the order.

        Position orders are stop_loss and take_profit only.
        """
        if not self.closing_bar:
            if bar.within(self.stop_loss):
                self.close(bar, self.stop_loss, -abs(self.entry_level - self.stop_loss))
            elif bar.within(self.take_profit):
                self.close(
                    bar, self.take_profit, abs(self.take_profit - self.entry_level)
                )

        return {
            "closed": bool(self.closing_bar),
            "pnl": self.closing_pnl or self.pnl(bar),
        }

    def pnl(self, bar: Bar) -> int:
        """Return unrealized pnl.

        Uses close attribute of the bar.
        """
        if self.side == "buy":
            return bar.close - self.entry_level
        else:
            return self.entry_level - bar.close

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
    open_positions: Sequence[Position]
    closed_positions: Sequence[Position]


@dataclass(frozen=True)
class BrokerRunner:
    """Simple broker implementation.

    Track each signal as separate position, combine pnl in the account.

    Note:
        This implementation assumes that the position was entered at the bar close, so
        position tracking starts from the next bar.  This is due to how the computation
        graph works.  Strategy would send a signal after the bar already closed.

        This is a naive implementation.  It is advised to use lower timeframe data for
        more resolution or a different implementation of the broker runner that covers
        all required edge cases.
    """

    account: Account = field(default_factory=Account)
    open_positions: MutableSequence[Position] = field(default_factory=list)
    closed_positions: MutableSequence[Position] = field(default_factory=list)

    def __call__(self, bar: Bar, signal: Signal) -> BrokerReturn:
        """Return current account and position objects."""
        if signal is not None:
            self.open_positions.append(Position(entry_bar=bar, **asdict(signal)))
        else:
            self.account.unrealized_pnl = 0
            for position in self.open_positions[:]:
                pos = position.on_bar(bar)
                if pos["closed"]:
                    self.account.pnl += pos["pnl"]
                    self.closed_positions.append(position)
                    self.open_positions.remove(position)
                else:
                    self.account.unrealized_pnl += pos["pnl"]

        return {
            "account": self.account,
            "open_positions": self.open_positions,
            "closed_positions": self.closed_positions,
        }


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
