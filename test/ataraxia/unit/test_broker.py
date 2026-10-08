# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
from collections.abc import Sequence
from dataclasses import asdict
from typing import TypedDict

import pytest

from ataraxia.bar import Bar
from ataraxia.broker import Account, BrokerRunner, Position, Signal


class PositionFixture(TypedDict):
    position: Position
    signal: Signal
    bar: Bar


@pytest.fixture
def long_position() -> PositionFixture:
    signal = Signal(side="buy", stop_loss=10, take_profit=30)
    bar = Bar(timestamp=1, open=20, high=30, low=15, close=25, volume=1)

    position = Position(entry_bar=bar, **asdict(signal))

    return {
        "bar": bar,
        "signal": signal,
        "position": position,
    }


@pytest.fixture
def short_position() -> PositionFixture:
    signal = Signal(side="sell", stop_loss=29, take_profit=11)
    bar = Bar(timestamp=1, open=20, high=30, low=15, close=25, volume=1)

    position = Position(entry_bar=bar, **asdict(signal))

    return {
        "bar": bar,
        "signal": signal,
        "position": position,
    }


@pytest.fixture
def accounts():
    return (Account(pnl=2000, unrealized_pnl=150), Account(pnl=999, unrealized_pnl=444))


def test_sum_accounts(accounts: Sequence[Account]):
    summed: Account = sum(accounts)

    assert summed.pnl == 2999
    assert summed.unrealized_pnl == 594


def test_broker_runner_no_signal():
    """Test single signal broker that exits."""
    broker = BrokerRunner()

    bar = Bar(timestamp=1, open=2, high=3, low=1, close=2, volume=0)

    assert broker(bar=bar, signal=None) == {
        "account": Account(),
        "open_positions": [],
        "closed_positions": [],
    }


def test_broker_runner_signal_add_position(long_position):
    """Test position entry."""
    broker = BrokerRunner()

    ret = broker(bar=long_position["bar"], signal=long_position["signal"])

    assert len(ret["open_positions"]) == 1
    assert len(ret["closed_positions"]) == 0

    assert ret["account"].pnl == 0
    assert ret["account"].unrealized_pnl == 0


def test_broker_runner_signal_close_position(long_position):
    """Test position add and close."""
    broker = BrokerRunner()

    broker(bar=long_position["bar"], signal=long_position["signal"])

    bar = Bar(timestamp=2, open=25, high=35, low=15, close=25, volume=1)

    ret = broker(bar=bar, signal=None)

    assert len(ret["open_positions"]) == 0
    assert len(ret["closed_positions"]) == 1

    assert ret["account"].pnl == 5
    assert ret["account"].unrealized_pnl == 0


def test_broker_runner_unrealized_pnl(long_position):
    """Test unrealized pnl."""
    broker = BrokerRunner()

    broker(bar=long_position["bar"], signal=long_position["signal"])

    bar = Bar(timestamp=2, open=25, high=29, low=15, close=29, volume=1)

    ret = broker(bar=bar, signal=None)

    assert len(ret["open_positions"]) == 1
    assert len(ret["closed_positions"]) == 0

    assert ret["account"].pnl == 0
    assert ret["account"].unrealized_pnl == 4


def test_broker_runner_position_update_on_signal(long_position, short_position):
    """Should update already opened positions when receiving a signal."""
    broker = BrokerRunner()

    broker(bar=long_position["bar"], signal=long_position["signal"])

    bar = Bar(timestamp=1, open=20, high=29, low=15, close=28, volume=1)

    ret = broker(bar=bar, signal=short_position["signal"])

    assert ret["account"].pnl == 0
    assert ret["account"].unrealized_pnl == 3

    assert len(ret["open_positions"]) == 2
    assert len(ret["closed_positions"]) == 0
