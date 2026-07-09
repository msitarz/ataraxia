# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
import pytest

from ataraxia.bar import Bar
from ataraxia.compute import ComputableNode, ComputableSpec
from ataraxia.features import (
    RollingBarSpec,
    RollingWindowNode,
    RollingWindowParams,
    RollingWindowSpec,
    SmaNode,
    SmaSpec,
    sma,
)


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


def test_rolling_bar_spec():
    rolling_spec = RollingBarSpec(RollingWindowParams(1))

    assert rolling_spec.dependencies() == (Bar,)
    assert isinstance(rolling_spec, ComputableSpec)


def test_sma():
    assert sma([1, 2, 3], period=3) == 2
    assert sma([1, 2, 3], period=5) is None

    with pytest.raises(ValueError):
        sma([1, 2, 3], period=2)


def test_sma_node():
    node = SmaNode(2)

    assert isinstance(node, ComputableNode)


def test_sma_spec():
    spec = SmaSpec(RollingWindowParams(2))

    assert isinstance(spec, ComputableSpec)
