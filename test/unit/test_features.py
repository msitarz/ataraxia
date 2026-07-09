# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

from ataraxia.features import RollingWindowNode


def test_rolling_window_node():
    rolling = RollingWindowNode[int](2)

    rolling(5)
    rolling(6)

    assert tuple(rolling.queue) == (6, 5)

    rolling(3)

    assert tuple(rolling.queue) == (3, 6)
