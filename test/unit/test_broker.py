# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
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


def test_position_init(long_position: PositionFixture):
    """Position use bar's close on init."""
    assert long_position["position"].entry_level == 25


def test_position_on_bar_no_order_hit(long_position: PositionFixture):
    """Should return None when no order hit."""
    position = long_position["position"]

    bar = Bar(timestamp=2, open=25, high=29, low=20, close=28, volume=2)

    assert position.on_bar(bar) == {"closed": False, "pnl": 3}


def test_position_on_bar_stop_loss_hit(long_position: PositionFixture):
    """Should return negative pnl when stop loss hit."""
    position = long_position["position"]

    bar = Bar(timestamp=2, open=25, high=28, low=5, close=28, volume=2)

    assert position.on_bar(bar) == {"pnl": -15, "closed": True}


def test_position_on_bar_take_profit_hit(long_position: PositionFixture):
    """Should return positive pnl when take profit hit."""
    position = long_position["position"]

    bar = Bar(timestamp=2, open=25, high=30, low=11, close=28, volume=2)

    assert position.on_bar(bar) == {"pnl": 5, "closed": True}


def test_position_on_bar_both_orders_hit(long_position: PositionFixture):
    """Should trigger stop loss when both orders hit."""
    position = long_position["position"]

    bar = Bar(timestamp=2, open=25, high=30, low=10, close=28, volume=2)

    assert position.on_bar(bar) == {"pnl": -15, "closed": True}


def test_position_on_bar_when_already_finished(long_position: PositionFixture):
    """Should raise when position not working."""
    position = long_position["position"]

    bar = Bar(timestamp=2, open=25, high=28, low=5, close=28, volume=2)

    position.on_bar(bar)

    bar2 = Bar(timestamp=3, open=25, high=35, low=20, close=28, volume=2)

    assert position.on_bar(bar2) == {"pnl": -15, "closed": True}


def test_position_short_on_bar_take_profit_hit(short_position: PositionFixture):
    """Should return positive pnl when take profit when shorting hit."""
    position = short_position["position"]

    bar = Bar(timestamp=2, open=25, high=28, low=11, close=28, volume=2)

    assert position.on_bar(bar) == {"pnl": 14, "closed": True}


def test_position_short_on_bar_stop_loss_hit(short_position: PositionFixture):
    """Should return positive pnl when take profit when shorting hit."""
    position = short_position["position"]

    bar = Bar(timestamp=2, open=25, high=29, low=11, close=28, volume=2)

    assert position.on_bar(bar) == {"pnl": -4, "closed": True}


def test_position_short_on_bar_closing_pnl(short_position: PositionFixture):
    """Should return positive pnl when take profit when shorting hit."""
    position = short_position["position"]

    bar = Bar(timestamp=2, open=25, high=29, low=11, close=28, volume=2)

    position.on_bar(bar)

    assert position.closing_pnl == -4


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
