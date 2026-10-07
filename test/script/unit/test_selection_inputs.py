# SPDX-License-Identifier: Apache-2.0
"""Verify complete literal input state and fresh arrangement isolation."""

from pathlib import Path

import pytest

from test.script.selection_inputs import (
    ROOT,
    PreparedSelection,
    arrange_changed_input,
    copy_selection_fixture,
)
from test.script.support import tree_state


@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/selection-inputs/filesystem-and-fixtures/README.md",
    ac="AC-1",
)
def test_accepted_arrangement_preserves_complete_literal_inputs(tmp_path: Path) -> None:
    """Given fresh accepted or damaged named arrangements, selection
    consumers receive precise paths/data, independent accepted digest provenance
    and complete literal file bytes/link targets; changing one arrangement does
    not affect another or shared source fixtures.

    Covers complete accepted paths, digest and filesystem contents; independent
    copy isolation is covered by the companion case.
    """
    # Given
    fixtures = ROOT / "test/script/fixtures/registry_selection"
    expected = {
        "successful-setup.log": b"fixture preparation evidence\n",
        "repository/uv.lock": b"# frozen fixture declaration\n",
        "repository/pyproject.toml": b"# frozen fixture declaration\n",
        "repository/.pre-commit-config.yaml": (
            b"# frozen fixture declaration\nrepos: []\n"
        ),
        "cache/answers": b"project answer\n",
        "cache/uv/interpreter-v4/environment": b"old environment\n",
        "cache/uv/sdists-v9/editable/project.whl": b"project editable payload\n",
        "cache/prek/cache/uv/simple-v25/pypi/dependency.rkyv": (
            b"opaque fixture simple record\n"
        ),
        "cache/uv/archive-v0/dependency/payload.txt": b"pinned fixture payload\n",
        "cache/uv/archive-v0/dependency/dependency-1.0.dist-info/METADATA": (
            b"Name: dependency\nVersion: 1.0\n"
        ),
        "cache/uv/wheels-v6/pypi/dependency/1.0-py3-none-any.http": (
            b"opaque fixture HTTP record\n"
        ),
        "cache/prek/cache/uv/archive-v0/dependency/payload.txt": (
            b"pinned fixture payload\n"
        ),
        "cache/prek/cache/uv/archive-v0/dependency/dependency-1.0.dist-info/METADATA": (
            b"Name: dependency\nVersion: 1.0\n"
        ),
        "cache/prek/cache/uv/wheels-v6/pypi/dependency/1.0-py3-none-any.http": (
            b"opaque fixture HTTP record\n"
        ),
        "cache/uv/wheels-v6/pypi/dependency/1.0-py3-none-any": (
            "../../../archive-v0/dependency"
        ),
        "cache/prek/cache/uv/wheels-v6/pypi/dependency/1.0-py3-none-any": (
            "../../../archive-v0/dependency"
        ),
        "record.json": (fixtures / "records/accepted.json").read_bytes(),
    }

    # When
    result = copy_selection_fixture(tmp_path, "accepted")

    # Then
    assert result == PreparedSelection(
        tmp_path,
        tmp_path / "cache",
        tmp_path / "repository",
        tmp_path / "record.json",
        "86a0bd7e2b6004ca8deaaf776b1f344fa65b1531ccf3585a423635d14f559cff",
        tmp_path / "result",
    )
    assert tree_state(result.directory) == expected


@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/selection-inputs/filesystem-and-fixtures/README.md",
    ac="AC-1",
)
def test_damaging_one_copy_preserves_other_copy_and_source(tmp_path: Path) -> None:
    """Given fresh accepted or damaged named arrangements, selection
    consumers receive precise paths/data, independent accepted digest provenance
    and complete literal file bytes/link targets; changing one arrangement does
    not affect another or shared source fixtures.

    Covers independent copies and source-fixture immutability when a selected
    payload is removed; literal contents and digest are covered separately.
    """
    # Given
    fixtures = ROOT / "test/script/fixtures/registry_selection"
    source_before = tree_state(fixtures)
    first = copy_selection_fixture(tmp_path / "first", "accepted")
    second = copy_selection_fixture(tmp_path / "second", "accepted")
    second_before = tree_state(second.directory)

    # When
    arrange_changed_input(first, "file")

    # Then
    assert not (first.cache / "uv/archive-v0/dependency/payload.txt").exists()
    assert tree_state(second.directory) == second_before
    assert tree_state(fixtures) == source_before
