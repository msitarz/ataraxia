# SPDX-License-Identifier: Apache-2.0
"""Verify registry consumers use the supported public value types."""

import pytest

from script.registry_selection import Package, Selection
from test.script.selection_inputs import PreparedSelection
from test.script.support import select_prepared, tree_state


@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/selection-observations/manifest-adaptation/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/imports/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/selection-observations/README.md",
    ac="AC-1",
)
def test_selector_values_share_the_public_registry_types(
    prepared_selection: PreparedSelection, selection_expected: Selection
) -> None:
    """Verify canonical selector identity, complete values and unchanged inputs.

    CLI exit/diagnostics and complete manifest reading are covered separately.
    """
    # Given
    before = tree_state(prepared_selection.cache)
    inputs_before = tree_state(prepared_selection.directory)

    # When
    result = select_prepared(prepared_selection)

    # Then
    assert isinstance(result, Selection)
    assert all(isinstance(package, Package) for package in result.packages)
    assert result == selection_expected
    assert tree_state(prepared_selection.cache) == before
    assert tree_state(prepared_selection.directory) == inputs_before
