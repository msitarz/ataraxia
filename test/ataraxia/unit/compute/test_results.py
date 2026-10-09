# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Tests for compute catalogs, dependency selection, and complete results."""

import pytest

from ataraxia.compute.loop import (
    ComputableMapping,
    compute,
    compute_step,
    computed_node_deps,
    prime_catalog,
)
from ataraxia.compute.protocol import Computable
from test.ataraxia.compute_dependency_inputs import (
    ARunner,
    BRunner,
    single_dependency,
)
from test.ataraxia.compute_source_inputs import integer_source_sink


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/compute/results/README.md",
    ac="AC-1",
)
def test_prime_catalog() -> None:
    """Create one matching runner for each node in dependency order."""
    # Given
    a, b = single_dependency()
    nodes = (b, a)

    # When
    actual = prime_catalog(nodes)

    # Then
    assert actual == {b: BRunner(), a: ARunner()}


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/compute/results/README.md",
    ac="AC-1",
)
def test_computed_node_deps() -> None:
    """Select B's value and exclude A's sentinel result."""
    # Given
    a, b = single_dependency()
    computed: dict[Computable[..., object], object] = {
        b: 1,
        a: ValueError("Shouldn't be here"),
    }

    # When
    actual = computed_node_deps(a, computed)

    # Then
    assert actual == {"b": 1}


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/compute/results/README.md",
    ac="AC-1",
)
def test_compute_step() -> None:
    """Compute the complete B and A values for one prepared step."""
    # Given
    a, b = single_dependency()
    nodes = (b, a)
    catalog: ComputableMapping = {b: BRunner(), a: ARunner()}

    # When
    actual = compute_step(nodes, catalog)

    # Then
    assert actual == {b: 1, a: 4}


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/compute/results/README.md",
    ac="AC-1",
)
def test_compute() -> None:
    """Exhaust the real integer source and compare both complete steps."""
    # Given
    sink, source = integer_source_sink()

    # When
    actual = list(compute(sink))

    # Then
    assert actual == [
        {source: 1, sink: 8},
        {source: 3, sink: 10},
    ]
