# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

from ataraxia.feature import RollingWindowRunner


def test_rolling_window_runner():
    runner = RollingWindowRunner(maxlen=2)

    assert runner(3) == (3,)
    assert runner(4) == (4, 3)
    assert runner(5) == (5, 4)
