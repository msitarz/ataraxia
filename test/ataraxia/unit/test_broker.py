# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
from dataclasses import dataclass
from typing import Literal

import pytest

from ataraxia.bar import Bar
from ataraxia.broker import Account, BrokerReturn, BrokerRunner, Position, Signal


@dataclass(frozen=True)
class AccountSnapshot:
    pnl: int
    unrealized_pnl: int


@dataclass(frozen=True)
class PositionSnapshot:
    side: Literal["buy", "sell"]
    stop_loss: int
    take_profit: int
    entry_bar: Bar
    entry_level: int
    closing_bar: Bar | None
    closing_level: int | None
    closing_pnl: int | None


@dataclass(frozen=True)
class BrokerSnapshot:
    account: AccountSnapshot
    open_positions: tuple[PositionSnapshot, ...]
    closed_positions: tuple[PositionSnapshot, ...]


def _position_snapshot(position: Position) -> PositionSnapshot:
    return PositionSnapshot(
        side=position.side,
        stop_loss=position.stop_loss,
        take_profit=position.take_profit,
        entry_bar=position.entry_bar,
        entry_level=position.entry_level,
        closing_bar=position.closing_bar,
        closing_level=position.closing_level,
        closing_pnl=position.closing_pnl,
    )


def _broker_snapshot(result: BrokerReturn) -> BrokerSnapshot:
    return BrokerSnapshot(
        account=AccountSnapshot(
            pnl=result["account"].pnl,
            unrealized_pnl=result["account"].unrealized_pnl,
        ),
        open_positions=tuple(
            _position_snapshot(position) for position in result["open_positions"]
        ),
        closed_positions=tuple(
            _position_snapshot(position) for position in result["closed_positions"]
        ),
    )


def _expected_open_position(
    side: Literal["buy", "sell"],
    stop_loss: int,
    take_profit: int,
    entry_bar: Bar,
    entry_level: int,
) -> PositionSnapshot:
    return PositionSnapshot(
        side=side,
        stop_loss=stop_loss,
        take_profit=take_profit,
        entry_bar=entry_bar,
        entry_level=entry_level,
        closing_bar=None,
        closing_level=None,
        closing_pnl=None,
    )


def _expected_closed_position(
    side: Literal["buy", "sell"],
    stop_loss: int,
    take_profit: int,
    entry_bar: Bar,
    entry_level: int,
    closing_bar: Bar,
    closing_level: int,
    closing_pnl: int,
) -> PositionSnapshot:
    return PositionSnapshot(
        side=side,
        stop_loss=stop_loss,
        take_profit=take_profit,
        entry_bar=entry_bar,
        entry_level=entry_level,
        closing_bar=closing_bar,
        closing_level=closing_level,
        closing_pnl=closing_pnl,
    )


@pytest.fixture
def entry_bar() -> Bar:
    return Bar(timestamp=1, open=20, high=30, low=15, close=25, volume=1)


@pytest.fixture
def long_signal() -> Signal:
    return Signal(side="buy", stop_loss=10, take_profit=30)


@pytest.fixture
def short_signal() -> Signal:
    return Signal(side="sell", stop_loss=29, take_profit=11)


@pytest.fixture
def accounts() -> tuple[Account, Account]:
    return (Account(pnl=2000, unrealized_pnl=150), Account(pnl=999, unrealized_pnl=444))


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/broker/README.md", ac="AC-1"
)
def test_sum_accounts(accounts: tuple[Account, Account]) -> None:
    """Sum realized and unrealized account totals independently."""
    # Given
    # Two account values are supplied by the typed fixture.

    # When
    summed = sum(accounts)

    # Then
    assert isinstance(summed, Account)
    snapshot = AccountSnapshot(pnl=summed.pnl, unrealized_pnl=summed.unrealized_pnl)
    assert snapshot == AccountSnapshot(pnl=2999, unrealized_pnl=594)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/broker/README.md", ac="AC-1"
)
def test_broker_runner_no_signal() -> None:
    """Return an empty broker snapshot when no signal is supplied."""
    # Given
    broker = BrokerRunner()
    bar = Bar(timestamp=1, open=2, high=3, low=1, close=2, volume=0)

    # When
    snapshot = _broker_snapshot(broker(bar=bar, signal=None))

    # Then
    assert snapshot == BrokerSnapshot(
        account=AccountSnapshot(pnl=0, unrealized_pnl=0),
        open_positions=(),
        closed_positions=(),
    )


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/broker/README.md", ac="AC-1"
)
def test_broker_runner_signal_add_position(entry_bar: Bar, long_signal: Signal) -> None:
    """Admit a position after its signal bar even when that bar touches target."""
    # Given
    broker = BrokerRunner()

    # When
    snapshot = _broker_snapshot(broker(bar=entry_bar, signal=long_signal))

    # Then
    assert snapshot == BrokerSnapshot(
        account=AccountSnapshot(pnl=0, unrealized_pnl=0),
        open_positions=(
            _expected_open_position(
                side="buy",
                stop_loss=10,
                take_profit=30,
                entry_bar=entry_bar,
                entry_level=25,
            ),
        ),
        closed_positions=(),
    )


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/broker/README.md", ac="AC-1"
)
def test_broker_runner_signal_close_position(
    entry_bar: Bar, long_signal: Signal
) -> None:
    """Snapshot entry before a later bar moves the position to closed."""
    # Given
    broker = BrokerRunner()
    entry_snapshot = _broker_snapshot(broker(bar=entry_bar, signal=long_signal))
    exit_bar = Bar(timestamp=2, open=25, high=35, low=15, close=25, volume=1)

    # When
    exit_snapshot = _broker_snapshot(broker(bar=exit_bar, signal=None))

    # Then
    assert entry_snapshot == BrokerSnapshot(
        account=AccountSnapshot(pnl=0, unrealized_pnl=0),
        open_positions=(
            _expected_open_position(
                side="buy",
                stop_loss=10,
                take_profit=30,
                entry_bar=entry_bar,
                entry_level=25,
            ),
        ),
        closed_positions=(),
    )
    assert exit_snapshot == BrokerSnapshot(
        account=AccountSnapshot(pnl=5, unrealized_pnl=0),
        open_positions=(),
        closed_positions=(
            _expected_closed_position(
                side="buy",
                stop_loss=10,
                take_profit=30,
                entry_bar=entry_bar,
                entry_level=25,
                closing_bar=exit_bar,
                closing_level=30,
                closing_pnl=5,
            ),
        ),
    )


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/broker/README.md", ac="AC-1"
)
def test_broker_runner_unrealized_pnl(entry_bar: Bar, long_signal: Signal) -> None:
    """Keep a position open and snapshot its complete unrealized state."""
    # Given
    broker = BrokerRunner()
    entry_snapshot = _broker_snapshot(broker(bar=entry_bar, signal=long_signal))
    mark_bar = Bar(timestamp=2, open=25, high=29, low=15, close=29, volume=1)

    # When
    snapshot = _broker_snapshot(broker(bar=mark_bar, signal=None))

    # Then
    assert entry_snapshot == BrokerSnapshot(
        account=AccountSnapshot(pnl=0, unrealized_pnl=0),
        open_positions=(
            _expected_open_position(
                side="buy",
                stop_loss=10,
                take_profit=30,
                entry_bar=entry_bar,
                entry_level=25,
            ),
        ),
        closed_positions=(),
    )
    assert snapshot == BrokerSnapshot(
        account=AccountSnapshot(pnl=0, unrealized_pnl=4),
        open_positions=(
            _expected_open_position(
                side="buy",
                stop_loss=10,
                take_profit=30,
                entry_bar=entry_bar,
                entry_level=25,
            ),
        ),
        closed_positions=(),
    )


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/broker/README.md", ac="AC-1"
)
def test_broker_runner_position_update_on_signal(
    entry_bar: Bar, long_signal: Signal, short_signal: Signal
) -> None:
    """Update old positions before admitting a new signaled position."""
    # Given
    broker = BrokerRunner()
    entry_snapshot = _broker_snapshot(broker(bar=entry_bar, signal=long_signal))
    signal_bar = Bar(timestamp=2, open=20, high=29, low=15, close=28, volume=1)

    # When
    update_snapshot = _broker_snapshot(broker(bar=signal_bar, signal=short_signal))

    # Then
    assert entry_snapshot == BrokerSnapshot(
        account=AccountSnapshot(pnl=0, unrealized_pnl=0),
        open_positions=(
            _expected_open_position(
                side="buy",
                stop_loss=10,
                take_profit=30,
                entry_bar=entry_bar,
                entry_level=25,
            ),
        ),
        closed_positions=(),
    )
    assert update_snapshot == BrokerSnapshot(
        account=AccountSnapshot(pnl=0, unrealized_pnl=3),
        open_positions=(
            _expected_open_position(
                side="buy",
                stop_loss=10,
                take_profit=30,
                entry_bar=entry_bar,
                entry_level=25,
            ),
            _expected_open_position(
                side="sell",
                stop_loss=29,
                take_profit=11,
                entry_bar=signal_bar,
                entry_level=28,
            ),
        ),
        closed_positions=(),
    )
