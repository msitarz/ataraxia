# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

from unittest.mock import MagicMock, patch

import pytest

from ataraxia.bar import Bar
from ataraxia.errors import FeatureError
from ataraxia.feature import SmaRunner, sma


def test_sma():
    """Should return simple moving average."""
    assert sma((4, 6), 2) == 5


def test_sma_error_on_wrong_value():
    """Should raise FeatureError on too many values."""
    with pytest.raises(FeatureError):
        sma((3, 6, 9), 2)


def test_sma_none_on_incomplete_data():
    """Should return None when not enough values."""
    assert sma((2, 3), 3) is None


@pytest.mark.parametrize(
    "values", [(None, 2, 3), (2, None, 3), (2, 3, None), (None, None, None)]
)
def test_sma_none_on_values_with_none(values):
    """Should return None when values contain None."""
    assert sma(values, 3) is None


def test_sma_none_on_excess_values_with_none():
    """Missing values take precedence over the excess-value error."""
    assert sma((2, 3, None), 2) is None


def test_sma_runner():
    """Should call sma with bars close values and period."""
    mock = MagicMock()
    with patch("ataraxia.feature.sma", mock):
        period = 3
        bars = (Bar(timestamp=1, open=10, high=20, low=5, close=15, volume=10),)

        runner = SmaRunner(period)

        runner(bars)

        mock.assert_called_once_with((15,), period)


def test_sma_with_zero():
    """Should calculate sma if there is 0 value."""
    assert sma((0, 2), 2) == 1
