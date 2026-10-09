# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
from collections.abc import Mapping
from dataclasses import dataclass

from hypothesis import example, given
from hypothesis import strategies as st
import pytest

from ataraxia.compute import Computable, Runner
from ataraxia.feature import RollingWindow, RollingWindowRunner


@dataclass(frozen=True)
class _IntRunner:
    value: int

    def __call__(self) -> int:
        return self.value


@dataclass(frozen=True)
class _IntNode:
    value: int

    def deps(self) -> Mapping[str, Computable[..., int]]:
        return {}

    def factory(self) -> Runner[[], int]:
        return _IntRunner(self.value)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/rolling/README.md", ac="AC-1"
)
def test_rolling_window_runner() -> None:
    """Keep the newest two inputs in newest-first order."""
    # Given
    runner = RollingWindowRunner[int](maxlen=2)

    # When
    results = (runner(3), runner(4), runner(5))

    # Then
    assert results == ((3,), (4, 3), (5, 4))


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/rolling/README.md", ac="AC-1"
)
def test_rolling_window() -> None:
    """Preserve dependency identity and create independent initialized runners."""
    # Given
    source = _IntNode(value=0)
    node = RollingWindow[int](maxlen=2, from_node=source)

    # When
    first_runner = node.factory()
    first_results = (first_runner(0), first_runner(3))
    fresh_runner = node.factory()
    fresh_result = fresh_runner(5)

    # Then
    assert node.deps()["item"] is source
    assert first_results == ((0,), (3, 0))
    assert fresh_result == (5,)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/hypothesis/window/README.md", ac="AC-1"
)
@given(
    capacity=st.integers(min_value=0, max_value=8),
    values=st.lists(st.integers(min_value=-100, max_value=100), max_size=24),
)
@example(capacity=0, values=[1, 1])
@example(capacity=3, values=[])
@example(capacity=1, values=[-2, 7])
@example(capacity=3, values=[4, 4])
@example(capacity=2, values=[0, 1, 2])
def test_rolling_window_matches_every_generated_prefix(
    capacity: int, values: list[int]
) -> None:
    """Compare every runner prefix with an independent newest-first slice."""
    # Given
    runner = RollingWindowRunner[int](maxlen=capacity)
    seen: list[int] = []
    actual_prefixes: list[tuple[int, ...]] = []
    expected_prefixes: list[tuple[int, ...]] = []

    # When
    for value in values:
        seen.append(value)
        actual_prefixes.append(runner(value))
        newest = seen[-capacity:] if capacity else []
        expected_prefixes.append(tuple(reversed(newest)))

    # Then
    assert actual_prefixes == expected_prefixes
