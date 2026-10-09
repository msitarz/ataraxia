# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Tests for shared dependency values and fresh runner state."""

from collections.abc import Mapping
from dataclasses import dataclass, field

import pytest

from ataraxia.compute.loop import compute
from test.ataraxia.compute_source_inputs import IntegerSource

type StepSnapshot = tuple[int, int, int, int, tuple[int, int], int]
type RunSnapshot = tuple[StepSnapshot, ...]


@dataclass
class TotalRunner:
    """Accumulate source items once for each fresh execution."""

    total: int = 0
    calls: int = 0

    def __call__(self, item: int) -> int:
        self.calls += 1
        self.total += item
        return self.total


@dataclass(frozen=True)
class Total:
    """Share one source total across equal dependency specifications."""

    source: IntegerSource
    runners: list[TotalRunner] = field(compare=False, hash=False)

    def deps(self) -> Mapping[str, IntegerSource]:
        return {"item": self.source}

    def factory(self) -> TotalRunner:
        runner = TotalRunner()
        self.runners.append(runner)
        return runner


@dataclass(frozen=True)
class BranchRunner:
    """Add this branch's fixed offset to the shared total."""

    offset: int

    def __call__(self, total: int) -> int:
        return total + self.offset


@dataclass(frozen=True)
class Branch:
    """Expose one offset branch over a shared Total node."""

    total: Total
    offset: int

    def deps(self) -> Mapping[str, Total]:
        return {"total": self.total}

    def factory(self) -> BranchRunner:
        return BranchRunner(self.offset)


@dataclass(frozen=True)
class DiamondRunner:
    """Return both branch values as the complete sink result."""

    def __call__(self, left: int, right: int) -> tuple[int, int]:
        return left, right


@dataclass(frozen=True)
class Diamond:
    """Join the two offset branches over one source."""

    left: Branch
    right: Branch

    def deps(self) -> Mapping[str, Branch]:
        return {"left": self.left, "right": self.right}

    def factory(self) -> DiamondRunner:
        return DiamondRunner()

    def sources(self) -> tuple[IntegerSource, ...]:
        return (self.left.total.source,)

    def consumer(self) -> None:
        return None


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/compute/sharing/README.md",
    ac="AC-1",
)
def test_equivalent_dependencies_share_state_once_per_bar() -> None:
    """Share totals per bar, then create fresh runner state on the next run."""
    # Given
    source = IntegerSource()
    runners: list[TotalRunner] = []
    left = Total(source, runners)
    right = Total(source, runners)
    assert left is not right
    assert left == right
    left_branch = Branch(left, 10)
    right_branch = Branch(right, 20)
    sink = Diamond(left_branch, right_branch)
    graph_nodes = (source, left, right, left_branch, right_branch, sink)
    original_hashes = tuple(map(hash, graph_nodes))
    expected_snapshot: RunSnapshot = (
        (1, 1, 11, 21, (11, 21), 5),
        (3, 4, 14, 24, (14, 24), 5),
    )
    snapshots: list[RunSnapshot] = []

    # When
    for _ in range(2):
        steps = list(compute(sink))
        snapshots.append(
            tuple(
                (
                    step[source],
                    step[left],
                    step[left_branch],
                    step[right_branch],
                    step[sink],
                    len(step),
                )
                for step in steps
            )
        )
        assert source.context.is_closed
        assert tuple(map(hash, graph_nodes)) == original_hashes

    # Then
    assert snapshots == [expected_snapshot, expected_snapshot]
    assert [(runner.calls, runner.total) for runner in runners] == [(2, 4), (2, 4)]
    assert runners[0] is not runners[1]
