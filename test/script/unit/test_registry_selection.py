# SPDX-License-Identifier: Apache-2.0
"""Verify reviewed inputs and refusal behavior of the public selector."""

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch

import pytest

from script.registry_selection import Selection
from test.script.selection_inputs import (
    ROOT,
    PreparedSelection,
)
from test.script.support import (
    ChangingRecordRead,
    select_prepared,
    tree_state,
)


@pytest.fixture
def changing_record(
    prepared_selection: PreparedSelection,
) -> Iterator[ChangingRecordRead]:
    """Expose a repeated record read while delegating every read to disk.

    The selector has no filesystem injection point. Scope this boundary double
    to the fixture lifetime, delegate real reads, and restore Path.read_bytes.
    """
    edge = ChangingRecordRead(
        prepared_selection.record,
        ROOT / "test/script/fixtures/registry_selection/unapproved.json",
        Path.read_bytes,
    )
    with patch.object(Path, "read_bytes", autospec=True, side_effect=edge.read):
        yield edge


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/selectors/README.md",
    ac="AC-1",
)
def test_selector_returns_only_reviewed_inputs_without_changing_cache(
    prepared_selection: PreparedSelection,
    selection_expected: Selection,
) -> None:
    """Return the whole accepted selection while preserving cache state."""
    # Given
    case = prepared_selection
    before = tree_state(case.cache)

    # When
    result = select_prepared(case)

    # Then
    after = tree_state(case.cache)
    assert result == selection_expected
    assert after == before


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/selectors/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-2",
)
@pytest.mark.parametrize(
    ("changed_selection", "message"),
    [
        pytest.param(
            "file",
            "missing or external file: uv/archive-v0/dependency/payload.txt",
            id="missing-payload",
        ),
        pytest.param(
            "link",
            "external or changed link: uv/wheels-v6/pypi/dependency/1.0-py3-none-any",
            id="external-link",
        ),
        pytest.param(
            "declaration",
            "stale dependency declaration: uv.lock",
            id="changed-declaration",
        ),
        pytest.param(
            "evidence",
            "changed preparation evidence: successful-setup.log",
            id="changed-evidence",
        ),
        pytest.param(
            "record",
            "preparation digest differs from external acceptance",
            id="unapproved-record",
        ),
    ],
    indirect=["changed_selection"],
)
def test_selector_rejects_changed_inputs_without_modifying_cache(
    changed_selection: PreparedSelection, message: str
) -> None:
    """Refuse each changed input with its exact error and unchanged cache."""
    # Given
    case = changed_selection
    before = tree_state(case.cache)

    # When
    with pytest.raises(ValueError) as error:
        select_prepared(case)

    # Then
    after = tree_state(case.cache)
    assert error.type is ValueError
    assert error.value.args == (message,)
    assert error.value.__cause__ is None
    assert after == before


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-2",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/selectors/README.md",
    ac="AC-1",
)
@pytest.mark.parametrize(
    ("unsupported_selection", "message"),
    [
        pytest.param(
            "uv", "unsupported tool/index/platform/cache condition", id="unsupported-uv"
        ),
        pytest.param(
            "index",
            "unsupported tool/index/platform/cache condition",
            id="unsupported-index",
        ),
        pytest.param(
            "platform",
            "unsupported tool/index/platform/cache condition",
            id="unsupported-platform",
        ),
        pytest.param(
            "layout",
            "unsupported tool/index/platform/cache condition",
            id="unsupported-layout",
        ),
        pytest.param(
            "metadata",
            "missing payload or complete resolver metadata",
            id="missing-metadata",
        ),
        pytest.param(
            "undeclared",
            "inventory contains undeclared entries",
            id="undeclared-artifact",
        ),
        pytest.param(
            "version",
            "wheel does not match declared package",
            id="declared-version-mismatch",
        ),
    ],
    indirect=["unsupported_selection"],
)
def test_selector_rejects_unsupported_records_without_modifying_cache(
    unsupported_selection: PreparedSelection, message: str
) -> None:
    """Refuse unsupported records with their exact errors and cache state."""
    # Given
    case = unsupported_selection
    before = tree_state(case.cache)

    # When
    with pytest.raises(ValueError) as error:
        select_prepared(case)

    # Then
    after = tree_state(case.cache)
    assert error.type is ValueError
    assert error.value.args == (message,)
    assert error.value.__cause__ is None
    assert after == before


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/selectors/README.md",
    ac="AC-1",
)
def test_selector_uses_only_the_single_accepted_record_read(
    prepared_selection: PreparedSelection,
    selection_expected: Selection,
    changing_record: ChangingRecordRead,
) -> None:
    """Use the accepted record snapshot once even if a later read changes."""
    # Given
    case = prepared_selection

    # When
    result = select_prepared(case)

    # Then
    assert result == selection_expected
    assert changing_record.record_reads == 1
