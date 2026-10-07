# SPDX-License-Identifier: Apache-2.0
"""Verify real CLI artifacts, unchanged inputs and disposable process isolation."""

from pathlib import Path
import sys

import pytest

from test.script.selection_inputs import ROOT, PreparedSelection, arrange_changed_input
from test.script.selection_manifest import ManifestObservation
from test.script.selection_process import run_selection_cli, tree_state


@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/selection-observations/process-state/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/selection-observations/README.md",
    ac="AC-1",
)
def test_cli_success_retains_complete_artifacts_and_isolated_environment(
    tmp_path: Path,
    prepared_selection: PreparedSelection,
    manifest_expected: ManifestObservation,
) -> None:
    """Given fresh accepted or refused inputs, actual CLI observations
    retain precise exit/diagnostics, whole manifests or failure artifacts and
    complete source/destination state; process scratch stays contained outside
    observed inputs and expected answers remain independent of production output.

    Given prepared inputs, actual selector/CLI observations retain
    complete manifest fields, file bytes/link targets, exit and diagnostics
    through precisely typed results.

    Parent coverage verifies successful CLI exit/diagnostics, complete manifest
    artifacts and source/destination bytes/link state.

    Covers real CLI success, all artifact bytes, whole input state and environment
    containment; the companion case covers exact refusal diagnostics/artifacts.
    """
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
    assert (result.exit_code, result.stdout, result.stderr) == (0, "", "")
    assert result.manifest == manifest_expected
    assert result.failure is None
    assert result.destination_exists
    assert result.destination_after == {"selection.json": expected_bytes}
    assert result.source_after == cache_before
    assert result.inputs_after == {**before, "result/selection.json": expected_bytes}
    home, scratch = Path(result.environment["HOME"]), Path(result.environment["TMPDIR"])
    assert home.is_dir() and scratch.is_dir()
    assert home.parent == scratch.parent
    assert home.is_relative_to(tmp_path) and scratch.is_relative_to(tmp_path)
    assert not home.is_relative_to(case.directory)
    assert not scratch.is_relative_to(case.directory)
    assert result.environment == {
        "PATH": f"{Path(sys.executable).parent}:/usr/bin:/bin",
        "HOME": str(home),
        "TMPDIR": str(scratch),
    }


@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/selection-observations/process-state/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/selection-observations/README.md",
    ac="AC-1",
)
def test_cli_refusal_retains_literal_failure_and_complete_input_state(
    prepared_selection: PreparedSelection,
) -> None:
    """Given fresh accepted or refused inputs, actual CLI observations
    retain precise exit/diagnostics, whole manifests or failure artifacts and
    complete source/destination state; process scratch stays contained outside
    observed inputs and expected answers remain independent of production output.

    Given prepared inputs, actual selector/CLI observations retain
    complete manifest fields, file bytes/link targets, exit and diagnostics
    through precisely typed results.

    Parent coverage verifies refused CLI exit/diagnostics, complete failure
    artifacts and source/destination bytes/link state.

    Covers exact real CLI refusal and all artifact/input bytes; environment
    containment and complete successful manifests are covered separately.
    """
    # Given
    case = prepared_selection
    arrange_changed_input(case, "declaration")
    before = tree_state(case.directory)
    cache_before = tree_state(case.cache)
    expected = (
        "registry selection failed: stale dependency declaration: uv.lock; "
        "retain destination and reprepare/review inputs\n"
    )

    # When
    result = run_selection_cli(case)

    # Then
    assert (result.exit_code, result.stdout, result.stderr) == (1, "", expected)
    assert result.manifest is None
    assert result.failure == expected
    assert result.destination_exists
    assert result.destination_after == {"failure.txt": expected.encode()}
    assert result.source_after == cache_before
    assert result.inputs_after == {**before, "result/failure.txt": expected.encode()}
