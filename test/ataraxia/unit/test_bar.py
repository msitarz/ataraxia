# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
from collections.abc import Mapping

import pytest

from ataraxia.bar import Bar


@pytest.fixture
def data() -> dict[str, str]:
    return {
        "timestamp": "1234",
        "open": "10.25",
        "high": "30.50",
        "low": "10.00",
        "close": "25.75",
        "volume": "4321",
    }


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/bar/README.md", ac="AC-1"
)
def test_bar_from_map(data: Mapping[str, str]) -> None:
    """Normalize integer and quarter-price fields through the public mapping."""
    # Given
    # The data fixture supplies the complete string-valued bar.

    # When
    bar = Bar.from_map(data)

    # Then
    assert bar == Bar(timestamp=1234, open=41, high=122, low=40, close=103, volume=4321)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/bar/README.md", ac="AC-1"
)
def test_bar_from_map_rounds_fractional_tick_value(data: Mapping[str, str]) -> None:
    """Preserve the established rounding result for a fractional tick value."""
    # Given
    rounding_data = dict(data)
    rounding_data["open"] = "3.2"

    # When
    bar = Bar.from_map(rounding_data)

    # Then
    assert bar == Bar(timestamp=1234, open=13, high=122, low=40, close=103, volume=4321)


@pytest.mark.parametrize(
    ("value", "expected"),
    [(4, False), (5, True), (14, True), (20, True), (21, False)],
    ids=["below-low", "at-low", "inside-range", "at-high", "above-high"],
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/bar/README.md", ac="AC-1"
)
def test_bar_within_includes_both_range_boundaries(value: int, expected: bool) -> None:
    """Treat both ends of the Bar price range as inclusive."""
    # Given
    bar = Bar(timestamp=1, open=10, high=20, low=5, close=15, volume=1)

    # When
    result = bar.within(value)

    # Then
    assert result is expected
