# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

from _pytest.capture import CaptureFixture
import pytest

from ataraxia.bar import Bar
from ataraxia.broker import Account, BrokerReturn, Position
from ataraxia.cli import display_results


@pytest.fixture
def broker_returns():
    b1o = Bar(
        timestamp=1784516400,
        open=64956,
        high=64977,
        low=64932,
        close=64956,
        volume=12525,
    )
    b1c = Bar(
        timestamp=1784518200,
        open=64940,
        high=64959,
        low=64899,
        close=64927,
        volume=8773,
    )

    p1 = Position(
        side="sell",
        stop_loss=64976,
        take_profit=64926,
        entry_bar=b1o,
    )
    p1.on_bar(b1c)

    b2o = Bar(
        timestamp=1784543400,
        open=64598,
        high=64655,
        low=64568,
        close=64628,
        volume=10333,
    )
    b2c = Bar(
        timestamp=1784544300,
        open=64643,
        high=64661,
        low=64607,
        close=64634,
        volume=9002,
    )

    p2 = Position(
        side="buy",
        stop_loss=64608,
        take_profit=64658,
        entry_bar=b2o,
    )
    p2.on_bar(b2c)

    b3o = Bar(
        timestamp=1784541600,
        open=64430,
        high=64470,
        low=64422,
        close=64450,
        volume=6010,
    )
    b3c = Bar(
        timestamp=1784542500,
        open=64454,
        high=64490,
        low=64445,
        close=64471,
        volume=5062,
    )

    p3 = Position(
        side="buy",
        stop_loss=64430,
        take_profit=64480,
        entry_bar=b3o,
    )
    p3.on_bar(b3c)

    return (
        {
            "account": Account(pnl=10, unrealized_pnl=0),
            "closed_positions": [
                p1,
                p2,
            ],
            "open_positions": [],
        },
        {
            "account": Account(pnl=30, unrealized_pnl=0),
            "closed_positions": [p3],
            "open_positions": [],
        },
    )


def test_display_results(broker_returns: tuple[BrokerReturn], capsys: CaptureFixture):
    display_results(broker_returns)

    captured = capsys.readouterr()

    assert captured.err == ""
    # TODO:
    # assert captured.out == """whatever it should be"""
