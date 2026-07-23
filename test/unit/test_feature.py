# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

import pytest

from ataraxia.errors import FeatureError
from ataraxia.feature import RollingWindow, RollingWindowRunner, sma


def test_rolling_window_runner():
    runner = RollingWindowRunner[int](maxlen=2)

    assert runner(3) == (3,)
    assert runner(4) == (4, 3)
    assert runner(5) == (5, 4)


def test_rolling_window():
    class TestNode:
        def __init__(self):
            self.iterator = iter(range(3, 5))

        def __call__(self):
            return next(self.iterator)

        def deps(self):
            return {}

        def factory(self):
            return self

    from_node = TestNode()

    node = RollingWindow[int](maxlen=2, from_node=from_node)

    assert node.deps()["item"] is from_node


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


def test_sma_none_on_values_with_none():
    """Should return None when values contain None."""
    assert sma((2, 3, None), 3) is None
