# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Tests for dependency graph construction and ordering."""

import graphlib

import pytest

from ataraxia.compute.graph import Graph, dependency_graph, sort_graph
from ataraxia.errors import CycleError
from test.ataraxia.compute_dependency_inputs import single_dependency


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/compute/results/README.md",
    ac="AC-1",
)
def test_dependency_graph_good_path() -> None:
    """Build the exact graph from A to its shared B dependency."""
    # Given
    a, b = single_dependency()

    # When
    actual = dependency_graph(a)

    # Then
    assert actual == {a: (b,), b: ()}


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/compute/results/README.md",
    ac="AC-1",
)
def test_sort_graph() -> None:
    """Order B before A so its dependency is available first."""
    # Given
    a, b = single_dependency()
    graph: Graph = {a: (b,), b: ()}

    # When
    actual = sort_graph(graph)

    # Then
    assert actual == (b, a)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/compute/results/README.md",
    ac="AC-1",
)
def test_sort_graph_cycle_error() -> None:
    """Report the cycle reason and retain graphlib's cause."""
    # Given
    a, b = single_dependency()
    graph: Graph = {a: (b,), b: (a,)}

    # When
    with pytest.raises(CycleError) as error:
        sort_graph(graph)

    # Then
    assert str(error.value) == "Cyclical dependency graph"
    assert type(error.value.__cause__) is graphlib.CycleError
