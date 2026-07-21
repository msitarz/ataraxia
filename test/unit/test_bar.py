# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
import pytest

from ataraxia.bar import Bar


@pytest.fixture
def data():
    return {
        "timestamp": "1234",
        "open": "10.25",
        "high": "30.50",
        "low": "10.00",
        "close": "25.75",
        "volume": "4321",
    }


def test_bar_normalize():
    assert Bar._normalize("1234") == 1234
    assert Bar._normalize("10.25") == int(10.25 * 4)


def test_bar_from_map(data):
    bar = Bar.from_map(data)

    assert bar.timestamp == 1234
    assert bar.open == int(10.25 * 4)
    assert bar.high == int(30.50 * 4)
    assert bar.low == int(10.0 * 4)
    assert bar.close == int(25.75 * 4)
    assert bar.volume == 4321


def test_bar_within():
    """Should return True if value within bar's range."""
    bar = Bar(timestamp=1, open=10, high=20, low=5, close=15, volume=1)

    assert bar.within(14)
