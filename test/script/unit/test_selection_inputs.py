# SPDX-License-Identifier: Apache-2.0
"""Verify complete literal input state and fresh arrangement isolation."""

from pathlib import Path

import pytest

from test.script.selection_inputs import (
    ROOT,
    PreparedSelection,
    arrange_changed_input,
    changed_input_name,
    copy_selection_fixture,
    record_fixture_name,
)
from test.script.support import tree_state


@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/selection-inputs/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/selection-inputs/filesystem-and-fixtures/README.md",
    ac="AC-1",
)
def test_accepted_arrangement_preserves_complete_literal_inputs(tmp_path: Path) -> None:
    """Given fresh accepted or damaged named arrangements, selection
    consumers receive precise paths/data, independent accepted digest provenance
    and complete literal file bytes/link targets; changing one arrangement does
    not affect another or shared source fixtures.

    Given fresh accepted or damaged named inputs, arrangements
    expose precisely typed paths/data and the independent preparation acceptance
    digest without changing shared source fixtures.

    Parent coverage verifies complete typed accepted paths, digest and bytes/link
    targets; damaged records and copy/source isolation are covered separately.

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
    result = copy_selection_fixture(tmp_path, record_fixture_name("accepted"))

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
    work="doc/feat/testing-conformance/scripts/registry/selection-inputs/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/selection-inputs/filesystem-and-fixtures/README.md",
    ac="AC-1",
)
def test_damaging_one_copy_preserves_other_copy_and_source(tmp_path: Path) -> None:
    """Given fresh accepted or damaged named arrangements, selection
    consumers receive precise paths/data, independent accepted digest provenance
    and complete literal file bytes/link targets; changing one arrangement does
    not affect another or shared source fixtures.

    Given fresh accepted or damaged named inputs, arrangements
    expose precisely typed paths/data and the independent preparation acceptance
    digest without changing shared source fixtures.

    Parent coverage verifies damaged-copy independence and unchanged shared source;
    complete accepted state and record/digest preservation are covered separately.

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


@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/selection-inputs/filesystem-and-fixtures/README.md",
    ac="AC-1",
)
@pytest.mark.parametrize(
    ("name", "message"),
    [
        ("uv", "unknown fixture input: uv"),
        ("accepted", "unknown fixture input: accepted"),
        ("unknown", "unknown fixture input: unknown"),
    ],
    ids=["record-variant", "accepted-record", "unknown-name"],
)
def test_changed_input_boundary_rejects_other_domains_without_mutation(
    prepared_selection: PreparedSelection, name: str, message: str
) -> None:
    """Given fresh accepted or damaged named arrangements, selection
    consumers receive precise paths/data, independent accepted digest provenance
    and complete literal file bytes/link targets; changing one arrangement does
    not affect another or shared source fixtures.

    Covers truthful changed-input narrowing and unchanged inputs on refusal;
    supported names and their effects are covered by existing consumer cases.
    """
    # Given
    before = tree_state(prepared_selection.directory)

    # When
    with pytest.raises(ValueError) as error:
        arrange_changed_input(prepared_selection, changed_input_name(name))

    # Then
    assert error.value.args == (message,)
    assert error.value.__cause__ is None
    assert tree_state(prepared_selection.directory) == before


@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/selection-inputs/filesystem-and-fixtures/README.md",
    ac="AC-1",
)
@pytest.mark.parametrize(
    ("name", "message"),
    [
        ("file", "unknown record fixture: file"),
        ("declaration", "unknown record fixture: declaration"),
        ("unknown", "unknown record fixture: unknown"),
    ],
    ids=["changed-file", "changed-declaration", "unknown-name"],
)
def test_record_boundary_rejects_other_domains_before_creating_inputs(
    tmp_path: Path, name: str, message: str
) -> None:
    """Given fresh accepted or damaged named arrangements, selection
    consumers receive precise paths/data, independent accepted digest provenance
    and complete literal file bytes/link targets; changing one arrangement does
    not affect another or shared source fixtures.

    Covers truthful record-name narrowing and absence of output on refusal;
    all eight supported records/digests are covered by the record-variant cases.
    """
    # Given
    destination = tmp_path / "rejected"

    # When
    with pytest.raises(ValueError) as error:
        copy_selection_fixture(destination, record_fixture_name(name))

    # Then
    assert error.value.args == (message,)
    assert error.value.__cause__ is None
    assert not destination.exists()
