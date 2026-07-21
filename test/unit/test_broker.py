# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
from dataclasses import asdict
from typing import TypedDict

import pytest

from ataraxia.bar import Bar
from ataraxia.broker import Account, BrokerRunner, Position, Signal
from ataraxia.errors import PositionError


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

    assert position.on_bar(bar) is None


def test_position_on_bar_stop_loss_hit(long_position: PositionFixture):
    """Should return negative pnl when stop loss hit."""
    position = long_position["position"]

    bar = Bar(timestamp=2, open=25, high=28, low=5, close=28, volume=2)

    assert position.on_bar(bar) == -15


def test_position_on_bar_take_profit_hit(long_position: PositionFixture):
    """Should return positive pnl when take profit hit."""
    position = long_position["position"]

    bar = Bar(timestamp=2, open=25, high=30, low=11, close=28, volume=2)

    assert position.on_bar(bar) == 5


def test_position_on_bar_both_orders_hit(long_position: PositionFixture):
    """Should trigger stop loss when both orders hit."""
    position = long_position["position"]

    bar = Bar(timestamp=2, open=25, high=30, low=10, close=28, volume=2)

    assert position.on_bar(bar) == -15


def test_position_on_bar_when_already_finished(long_position: PositionFixture):
    """Should raise when position not working."""
    position = long_position["position"]

    bar = Bar(timestamp=2, open=25, high=28, low=5, close=28, volume=2)

    position.on_bar(bar)

    with pytest.raises(PositionError):
        position.on_bar(bar)


def test_position_short_on_bar_take_profit_hit(short_position: PositionFixture):
    """Should return positive pnl when take profit when shorting hit."""
    position = short_position["position"]

    bar = Bar(timestamp=2, open=25, high=28, low=11, close=28, volume=2)

    assert position.on_bar(bar) == 14


def test_position_short_on_bar_stop_loss_hit(short_position: PositionFixture):
    """Should return positive pnl when take profit when shorting hit."""
    position = short_position["position"]

    bar = Bar(timestamp=2, open=25, high=29, low=11, close=28, volume=2)

    assert position.on_bar(bar) == -4


def test_broker_runner_no_signal():
    """Test single signal broker that exits."""
    broker = BrokerRunner()

    assert broker(None, Bar(timestamp=1, open=2, high=3, low=1, close=2, volume=0)) == {
        "account": Account(),
        "position": None,
    }
