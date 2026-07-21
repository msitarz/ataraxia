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
def basic_position() -> PositionFixture:
    signal = Signal(side="buy", stop_loss=10, take_profit=30)
    bar = Bar(timestamp=1, open=20, high=30, low=15, close=25, volume=1)

    position = Position(bar=bar, **asdict(signal))

    return {
        "bar": bar,
        "signal": signal,
        "position": position,
    }


def test_position_init(basic_position: PositionFixture):
    """Position use bar's close on init."""
    assert basic_position["position"].entry == 25


def test_position_on_bar_no_order_hit(basic_position: PositionFixture):
    """Should return None when no order hit."""
    position = basic_position["position"]

    bar = Bar(timestamp=2, open=25, high=29, low=20, close=28, volume=2)

    assert position.on_bar(bar) is None


def test_broker_runner_no_signal():
    """Test single signal broker that exits."""
    broker = BrokerRunner()

    assert broker(None, Bar(timestamp=1, open=2, high=3, low=1, close=2, volume=0)) == {
        "account": Account(),
        "position": None,
    }
