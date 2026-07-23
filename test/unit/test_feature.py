# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

from ataraxia.feature import RollingWindow, RollingWindowRunner


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
