# SPDX-License-Identifier: Apache-2.0
"""Verify registry consumers use the supported public value types."""

import pytest

from script.registry_selection import Package, Selection
from test.script.support import PreparedSelection, select_prepared, tree_state


@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/imports/README.md",
    ac="AC-1",
)
def test_selector_values_share_the_public_registry_types(
    prepared_selection: PreparedSelection, selection_expected: Selection
) -> None:
    """Given actual registry imports, existing helper consumers receive
    the real public types/functions with stable selector and validator outcomes.

    Covers the selector's complete result and public value identity; existing
    validator and Make cases cover the remaining consumer obligations.
    """
    # Given
    before = tree_state(prepared_selection.cache)

    # When
    result = select_prepared(prepared_selection)

    # Then
    assert isinstance(result, Selection)
    assert all(isinstance(package, Package) for package in result.packages)
    assert result == selection_expected
    assert tree_state(prepared_selection.cache) == before
