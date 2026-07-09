# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

from ataraxia.compute import ComputableSpec
from ataraxia.features import RollingWindowNode, RollingWindowParams, RollingWindowSpec


def test_rolling_window_node():
    rolling = RollingWindowNode[int](2)

    rolling(5)
    rolling(6)

    assert tuple(rolling.queue) == (6, 5)

    rolling(3)

    assert tuple(rolling.queue) == (3, 6)


def test_rolling_window_spec():
    rolling_spec = RollingWindowSpec[int](RollingWindowParams(1))

    rolling = rolling_spec.factory()

    rolling(3)
    rolling(4)

    assert tuple(rolling.queue) == (4,)
    assert isinstance(rolling_spec, ComputableSpec)
