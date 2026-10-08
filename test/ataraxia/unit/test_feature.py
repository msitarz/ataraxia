# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
import pytest

from ataraxia.bar import Bar
from ataraxia.errors import FeatureError
from ataraxia.feature import SmaRunner, sma


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/sma/README.md", ac="AC-1"
)
def test_sma() -> None:
    """Calculate the complete two-value arithmetic mean."""
    # Given
    values = (4, 6)

    # When
    result = sma(values, 2)

    # Then
    assert result == 5


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/sma/README.md", ac="AC-1"
)
def test_sma_error_on_wrong_value() -> None:
    """Reject more observations than the requested period with its reason."""
    # Given
    values = (3, 6, 9)

    # When
    with pytest.raises(FeatureError) as error:
        sma(values, 2)

    # Then
    assert str(error.value) == "Cannot have more values than period"


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/sma/README.md", ac="AC-1"
)
def test_sma_none_on_incomplete_data() -> None:
    """Return None until the requested number of observations is available."""
    # Given
    values = (2, 3)

    # When
    result = sma(values, 3)

    # Then
    assert result is None


@pytest.mark.parametrize(
    "values",
    [(None, 2, 3), (2, None, 3), (2, 3, None), (None, None, None)],
    ids=["missing-first", "missing-middle", "missing-last", "all-missing"],
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/sma/README.md", ac="AC-1"
)
def test_sma_none_on_values_with_none(
    values: tuple[float | None, ...],
) -> None:
    """Return None for each placement of missing input values."""
    # Given
    period = 3

    # When
    result = sma(values, period)

    # Then
    assert result is None


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/sma/README.md", ac="AC-1"
)
def test_sma_none_on_excess_values_with_none() -> None:
    """Let missing values take precedence over the excess-value error."""
    # Given
    values = (2, 3, None)

    # When
    result = sma(values, 2)

    # Then
    assert result is None


@pytest.mark.parametrize(
    ("bars", "period", "expected"),
    [
        (
            (Bar(timestamp=1, open=10, high=20, low=5, close=15, volume=10),),
            3,
            None,
        ),
        (
            (
                Bar(timestamp=1, open=2, high=4, low=0, close=0, volume=10),
                Bar(timestamp=2, open=3, high=5, low=1, close=2, volume=11),
            ),
            2,
            1,
        ),
        (
            (
                Bar(timestamp=1, open=8, high=11, low=1, close=4, volume=10),
                Bar(timestamp=2, open=10, high=13, low=2, close=6, volume=11),
            ),
            2,
            5,
        ),
    ],
    ids=["one-bar-warmup", "zero-close", "complete-close-mean"],
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/sma/README.md", ac="AC-1"
)
def test_sma_runner(bars: tuple[Bar, ...], period: int, expected: float | None) -> None:
    """Calculate warm-up and complete means through real close-value Bars."""
    # Given
    runner = SmaRunner(period)

    # When
    result = runner(bars)

    # Then
    assert result == expected


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/sma/README.md", ac="AC-1"
)
def test_sma_with_zero() -> None:
    """Include zero as a valid scalar observation in the mean."""
    # Given
    values = (0, 2)

    # When
    result = sma(values, 2)

    # Then
    assert result == 1
