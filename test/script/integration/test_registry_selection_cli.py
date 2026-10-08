# SPDX-License-Identifier: Apache-2.0
"""Verify registry CLI delivery and refusal state at its process boundary."""

import pytest

from test.script.selection_inputs import ROOT, PreparedSelection
from test.script.selection_manifest import ManifestObservation
from test.script.selection_process import run_selection_cli, tree_state


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/cli/README.md",
    ac="AC-1",
)
def test_cli_delivers_the_reviewed_manifest_without_changing_cache(
    prepared_selection: PreparedSelection,
    manifest_expected: ManifestObservation,
) -> None:
    """Deliver the reviewed manifest and preserve the complete input state."""
    # Given
    case = prepared_selection
    before = tree_state(case.directory)
    cache_before = tree_state(case.cache)
    expected_bytes = (
        ROOT / "test/script/fixtures/registry_selection/expected-selection.json"
    ).read_bytes()

    # When
    result = run_selection_cli(case)

    # Then
    assert result.exit_code == 0, result.output
    assert result.manifest == manifest_expected
    assert result.failure is None
    assert result.destination_after == {"selection.json": expected_bytes}
    assert result.source_after == cache_before
    assert result.inputs_after == {**before, "result/selection.json": expected_bytes}


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-2",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/cli/README.md",
    ac="AC-1",
)
def test_cli_retains_missing_record_failure_without_changing_cache(
    cli_missing_record: PreparedSelection,
) -> None:
    """Retain the literal missing-record refusal and recovery artifact."""
    # Given
    case = cli_missing_record
    before = tree_state(case.directory)
    cache_before = tree_state(case.cache)
    missing_path = str(case.record)
    expected = (
        "registry selection failed: [Errno 2] No such file or directory: "
        f"'{missing_path}'; retain destination and reprepare/review inputs\n"
    )

    # When
    result = run_selection_cli(case)

    # Then
    assert result.exit_code == 1, result.output
    assert result.failure == expected
    assert result.stderr == expected
    assert result.failure == result.stderr
    assert result.destination_after == {"failure.txt": expected.encode()}
    assert result.source_after == cache_before
    assert result.inputs_after == {**before, "result/failure.txt": expected.encode()}


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-2",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/cli/README.md",
    ac="AC-1",
)
def test_cli_preserves_an_existing_destination(
    cli_existing_destination: PreparedSelection,
) -> None:
    """Preserve an existing destination sentinel on CLI refusal."""
    # Given
    case = cli_existing_destination
    before = tree_state(case.directory)

    # When
    result = run_selection_cli(case)

    # Then
    assert result.exit_code == 1, result.output
    assert "selection destination must be new" in result.output
    assert result.destination_after == {"sentinel.txt": b"changed fixture content\n"}
    assert result.manifest is None
    assert result.failure is None
    assert result.inputs_after == before


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-2",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/cli/README.md",
    ac="AC-1",
)
def test_cli_rejects_destinations_inside_the_input_cache(
    cli_cache_destination: PreparedSelection,
) -> None:
    """Reject a cache-contained destination without changing input state."""
    # Given
    case = cli_cache_destination
    before = tree_state(case.directory)

    # When
    result = run_selection_cli(case)

    # Then
    assert result.exit_code == 1, result.output
    assert "selection destination must be outside the input cache" in result.output
    assert result.destination_exists is False
    assert result.destination_after == {}
    assert result.inputs_after == before
