# SPDX-License-Identifier: Apache-2.0
"""Exercise reviewed sandbox disposition and retention validation."""

from dataclasses import replace
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from script import sandbox, sandbox_disposition, sandbox_execution
from test.script.integration.sandbox_lifecycle_support import (
    OTHER_SESSION,
    SESSION,
    WORK_PATH,
    ProvenSupervisor,
    UnprovenSupervisor,
    execution_environment,
)


def _prepare_review_fixture(frozen: Path) -> None:
    subprocess.run(
        ["git", "init", "--quiet", "--initial-branch=main", str(frozen)],
        check=True,
        timeout=10,
    )
    subprocess.run(
        ["git", "-C", str(frozen), "config", "user.name", "Fixture"],
        check=True,
        timeout=10,
    )
    subprocess.run(
        ["git", "-C", str(frozen), "config", "user.email", "fixture@example.test"],
        check=True,
        timeout=10,
    )
    (frozen / "tracked.txt").write_text("reviewed workspace\n")
    subprocess.run(
        ["git", "-C", str(frozen), "add", "tracked.txt"], check=True, timeout=10
    )
    subprocess.run(
        ["git", "-C", str(frozen), "commit", "--quiet", "-m", "fixture"],
        check=True,
        timeout=10,
    )


def _reviewed_material(
    workspace_destination: Path, outputs_destination: Path
) -> sandbox_disposition.ReviewedDisposition:
    return sandbox_disposition.ReviewedDisposition(
        reviewer_id="maintainer-fixture",
        review_reference="review-fixture-1",
        workspace=sandbox_disposition.MaterialDecision(
            "retain", "workspace-import-fixture", workspace_destination
        ),
        outputs=sandbox_disposition.MaterialDecision(
            "retain", "output-import-fixture", outputs_destination
        ),
    )


def _recorded_disposition(
    tmp_path: Path,
) -> tuple[Path, Path, str, Path, Path, Path, sandbox_disposition.DispositionRecord]:
    source, root, generation, frozen = execution_environment(tmp_path)
    _prepare_review_fixture(frozen)
    workspace_copy = tmp_path / "retained-workspace"
    outputs_copy = tmp_path / "retained-outputs"
    with sandbox.locked_sandbox(root, "execute", generation) as scope:
        sandbox.update_marker(scope, {"state": "ready"})
        sandbox_execution.run_attempt(
            scope,
            source_repository=source,
            work=WORK_PATH,
            owner_id="orchestrator-fixture",
            mode="initial",
            session_id=None,
            invocation=sandbox_execution.Invocation(
                ("fixture-evaluation", "retain"), frozen, 10
            ),
            supervisor=ProvenSupervisor(),
        )
        shutil.copytree(frozen, workspace_copy, symlinks=True)
        shutil.copytree(root / ".execute.runs", outputs_copy, symlinks=True)
        record = sandbox_disposition.record_disposition(
            scope,
            owner_id="orchestrator-fixture",
            source_repository=source,
            work=WORK_PATH,
            reviewed=_reviewed_material(workspace_copy, outputs_copy),
        )
        assert (
            sandbox_disposition.validate_disposition(
                scope, owner_id="orchestrator-fixture"
            )
            == record
        )
    return source, root, generation, frozen, workspace_copy, outputs_copy, record


@pytest.mark.covers(
    work="doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md",
    ac="AC-1",
)
def test_disposition_binds_review_workspace_tip_and_retained_outputs(
    tmp_path: Path,
) -> None:
    """Bind reviewed host evidence to the exact tip and retained material."""
    _, _, _, _, workspace_copy, outputs_copy, record = _recorded_disposition(tmp_path)
    assert record["material"]["workspace_head"] is not None
    assert record["workspace"]["destination"] == str(workspace_copy)
    assert record["outputs"]["destination"] == str(outputs_copy)


@pytest.mark.covers(
    work="doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md",
    ac="AC-1",
)
def test_bound_disposition_does_not_require_historical_work_readme(
    tmp_path: Path,
) -> None:
    """Use persisted Work provenance after its source README is removed."""
    source, root, generation, _, _, _, _ = _recorded_disposition(tmp_path)
    with sandbox.locked_sandbox(root, "execute", generation) as scope:
        (source / WORK_PATH).unlink()
        record = sandbox_disposition.record_disposition(
            scope,
            owner_id="orchestrator-fixture",
            source_repository=None,
            work=None,
            reviewed=sandbox_disposition.ReviewedDisposition(
                "maintainer-fixture",
                "review-existing-binding",
                sandbox_disposition.MaterialDecision("discard", "reviewed-workspace"),
                sandbox_disposition.MaterialDecision("discard", "reviewed-outputs"),
            ),
        )
        assert (
            sandbox_disposition.validate_disposition(
                scope, owner_id="orchestrator-fixture"
            )
            == record
        )


@pytest.mark.covers(
    work="doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md",
    ac="AC-1",
)
def test_changed_workspace_invalidates_disposition(tmp_path: Path) -> None:
    """Invalidate approval when workspace bytes differ from the reviewed copy."""
    _, root, generation, frozen, _, _, _ = _recorded_disposition(tmp_path)
    with sandbox.locked_sandbox(root, "execute", generation) as scope:
        (frozen / "tracked.txt").write_text("changed after review\n")
        with pytest.raises(ValueError, match="no longer matches"):
            sandbox_disposition.validate_disposition(
                scope, owner_id="orchestrator-fixture"
            )


@pytest.mark.covers(
    work="doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md",
    ac="AC-1",
)
def test_changed_private_output_invalidates_disposition(tmp_path: Path) -> None:
    """Invalidate approval when an attempt artifact changes after review."""
    _, root, generation, _, _, _, _ = _recorded_disposition(tmp_path)
    with sandbox.locked_sandbox(root, "execute", generation) as scope:
        artifact = next((root / ".execute.runs").glob("*/output.txt"))
        artifact.write_text("changed output\n")
        with pytest.raises(ValueError, match="no longer matches"):
            sandbox_disposition.validate_disposition(
                scope, owner_id="orchestrator-fixture"
            )


@pytest.mark.covers(
    work="doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md",
    ac="AC-1",
)
def test_changed_retention_destination_invalidates_disposition(tmp_path: Path) -> None:
    """Refuse a retained destination whose bytes changed after approval."""
    _, root, generation, _, workspace_copy, _, _ = _recorded_disposition(tmp_path)
    (workspace_copy / "tracked.txt").write_text("retained bytes changed\n")
    with (
        sandbox.locked_sandbox(root, "execute", generation) as scope,
        pytest.raises(ValueError, match="retained material changed"),
    ):
        sandbox_disposition.validate_disposition(scope, owner_id="orchestrator-fixture")


@pytest.mark.covers(
    work="doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md",
    ac="AC-1",
)
def test_rejected_resume_invalidates_prior_disposition(tmp_path: Path) -> None:
    """A rejected attempt clears prior approval before returning to the host."""
    source, root, generation, frozen, _, _, _ = _recorded_disposition(tmp_path)
    with sandbox.locked_sandbox(root, "execute", generation) as scope:
        result = sandbox_execution.run_attempt(
            scope,
            source_repository=source,
            work=WORK_PATH,
            owner_id="orchestrator-fixture",
            mode="resume",
            session_id=OTHER_SESSION,
            invocation=sandbox_execution.Invocation(
                ("fixture-evaluation", "resume-rejected"), frozen, 10
            ),
            supervisor=UnprovenSupervisor(),
        )
        assert result.status == "rejected"
        with pytest.raises(ValueError, match="missing or malformed"):
            sandbox_disposition.validate_disposition(
                scope, owner_id="orchestrator-fixture"
            )


@pytest.mark.covers(
    work="doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md",
    ac="AC-1",
)
@pytest.mark.parametrize(
    "work",
    ["doc/feat/missing/README.md", "../README.md", "doc/feat/example/spec.md"],
)
def test_first_disposition_requires_valid_source_work(
    tmp_path: Path, work: str
) -> None:
    """Require the source Work README before binding an unowned sandbox."""
    source, root, generation, frozen = execution_environment(tmp_path)
    _prepare_review_fixture(frozen)
    (source / "doc/feat/example/spec.md").write_text("# Spec, not a Work README\n")
    with sandbox.locked_sandbox(root, "execute", generation) as scope:
        sandbox.update_marker(scope, {"state": "ready"})
        with pytest.raises(ValueError):
            sandbox_disposition.record_disposition(
                scope,
                owner_id="orchestrator-fixture",
                source_repository=source,
                work=work,
                reviewed=sandbox_disposition.ReviewedDisposition(
                    "maintainer-fixture",
                    "review-invalid-work",
                    sandbox_disposition.MaterialDecision(
                        "discard", "reviewed-workspace"
                    ),
                    sandbox_disposition.MaterialDecision(
                        "discard", "reviewed-no-outputs"
                    ),
                ),
            )


@pytest.mark.covers(
    work="doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md",
    ac="AC-1",
)
def test_failed_preparation_requires_reviewed_diagnostics(tmp_path: Path) -> None:
    """Require an explicit diagnostics reference for partial failed preparation."""
    source, root, generation, _frozen = execution_environment(tmp_path)
    with sandbox.locked_sandbox(root, "execute", generation) as scope:
        sandbox.update_marker(
            scope,
            {
                "state": "failed",
                "failure_stage": "fixture-prepare",
                "failure_status": "1",
                "failure_stdout": "partial output",
                "failure_stderr": "expected failure",
            },
        )
        reviewed = sandbox_disposition.ReviewedDisposition(
            "maintainer-fixture",
            "review-failed-preparation",
            sandbox_disposition.MaterialDecision("discard", "review-partial-workspace"),
            sandbox_disposition.MaterialDecision("discard", "review-no-private-output"),
        )
        with pytest.raises(ValueError, match="diagnostics require"):
            sandbox_disposition.record_disposition(
                scope,
                owner_id="orchestrator-fixture",
                source_repository=source,
                work=WORK_PATH,
                reviewed=reviewed,
            )
        record = sandbox_disposition.record_disposition(
            scope,
            owner_id="orchestrator-fixture",
            source_repository=source,
            work=WORK_PATH,
            reviewed=replace(reviewed, diagnostics_reference="reviewed-diagnostics"),
        )
        assert record["diagnostics_reference"] == "reviewed-diagnostics"
        assert (
            sandbox_disposition.validate_disposition(
                scope, owner_id="orchestrator-fixture"
            )
            == record
        )


@pytest.mark.covers(
    work="doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md",
    ac="AC-1",
)
def test_missing_failed_workspace_requires_explicit_disposition(tmp_path: Path) -> None:
    """Record failure diagnostics even when partial preparation is absent."""
    source, root, generation, frozen = execution_environment(tmp_path)
    with sandbox.locked_sandbox(root, "execute", generation) as scope:
        sandbox.update_marker(
            scope,
            {
                "state": "failed",
                "failure_stage": "fixture-prepare",
                "failure_status": "1",
                "failure_stdout": "",
                "failure_stderr": "workspace missing",
            },
        )
    frozen.rmdir()
    with sandbox.locked_sandbox(root, "execute", generation) as scope:
        record = sandbox_disposition.record_disposition(
            scope,
            owner_id="orchestrator-fixture",
            source_repository=source,
            work=WORK_PATH,
            reviewed=sandbox_disposition.ReviewedDisposition(
                "maintainer-fixture",
                "review-missing-workspace",
                sandbox_disposition.MaterialDecision("discard", "review-no-workspace"),
                sandbox_disposition.MaterialDecision("discard", "review-no-outputs"),
                diagnostics_reference="reviewed-failure-diagnostics",
            ),
        )
        assert record["material"]["workspace_head"] is None
        assert (
            sandbox_disposition.validate_disposition(
                scope, owner_id="orchestrator-fixture"
            )
            == record
        )


@pytest.mark.covers(
    work="doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md",
    ac="AC-1",
)
def test_disposition_refuses_mismatched_owner(tmp_path: Path) -> None:
    """Do not authorize cleanup for a different orchestrator owner."""
    _, root, generation, _, _, _, _ = _recorded_disposition(tmp_path)
    with (
        sandbox.locked_sandbox(root, "execute", generation) as scope,
        pytest.raises(ValueError, match="Work or owner"),
    ):
        sandbox_disposition.record_disposition(
            scope,
            owner_id="other-orchestrator",
            source_repository=None,
            work=None,
            reviewed=sandbox_disposition.ReviewedDisposition(
                "maintainer-fixture",
                "review-wrong-owner",
                sandbox_disposition.MaterialDecision("discard", "reviewed-workspace"),
                sandbox_disposition.MaterialDecision("discard", "reviewed-outputs"),
            ),
        )


@pytest.mark.covers(
    work="doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md",
    ac="AC-1",
)
def test_disposition_rejects_symlink_retention_destination(tmp_path: Path) -> None:
    """Do not follow retention links into unrelated data."""
    source, root, generation, frozen = execution_environment(tmp_path)
    _prepare_review_fixture(frozen)
    target = tmp_path / "unrelated"
    target.mkdir()
    destination = tmp_path / "retained-link"
    destination.symlink_to(target, target_is_directory=True)
    with sandbox.locked_sandbox(root, "execute", generation) as scope:
        sandbox.update_marker(scope, {"state": "ready"})
        with pytest.raises(ValueError, match="symlink"):
            sandbox_disposition.record_disposition(
                scope,
                owner_id="orchestrator-fixture",
                source_repository=source,
                work=WORK_PATH,
                reviewed=sandbox_disposition.ReviewedDisposition(
                    "maintainer-fixture",
                    "review-symlink",
                    sandbox_disposition.MaterialDecision(
                        "retain", "workspace-import", destination
                    ),
                    sandbox_disposition.MaterialDecision(
                        "discard", "reviewed-no-outputs"
                    ),
                ),
            )


@pytest.mark.covers(
    work="doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md",
    ac="AC-1",
)
def test_unknown_execution_cannot_receive_disposition(tmp_path: Path) -> None:
    """Keep an uncertain attempt outside reviewed cleanup authority."""
    source, root, generation, frozen = execution_environment(tmp_path)
    with sandbox.locked_sandbox(root, "execute", generation) as scope:
        sandbox.update_marker(scope, {"state": "ready"})
        sandbox_execution.run_attempt(
            scope,
            source_repository=source,
            work=WORK_PATH,
            owner_id="orchestrator-fixture",
            mode="initial",
            session_id=None,
            invocation=sandbox_execution.Invocation(
                ("fixture-evaluation", "uncertain"), frozen, 10
            ),
            supervisor=UnprovenSupervisor(),
        )
        with pytest.raises(ValueError, match="unknown or running"):
            sandbox_disposition.record_disposition(
                scope,
                owner_id="orchestrator-fixture",
                source_repository=source,
                work=WORK_PATH,
                reviewed=sandbox_disposition.ReviewedDisposition(
                    "maintainer-fixture",
                    "review-unknown",
                    sandbox_disposition.MaterialDecision(
                        "discard", "reviewed-workspace"
                    ),
                    sandbox_disposition.MaterialDecision("discard", "reviewed-output"),
                ),
            )
    marker = json.loads((root / ".execute.ataraxia-sandbox.json").read_text())
    assert marker["cleanup_disposition"] is None


@pytest.mark.covers(
    work="doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md",
    ac="AC-1",
)
def test_replacement_with_fifo_during_public_snapshot_is_bounded(
    tmp_path: Path,
) -> None:
    """Refuse a FIFO replacement at open without blocking or approving."""
    source, root, generation, frozen = execution_environment(tmp_path)
    _prepare_review_fixture(frozen)
    with sandbox.locked_sandbox(root, "execute", generation) as scope:
        sandbox.update_marker(scope, {"state": "ready"})
    fixture = (
        Path(__file__).resolve().parents[1]
        / "fixtures"
        / "sandbox_disposition_fifo_swap.py"
    )
    result = subprocess.run(
        [sys.executable, str(fixture), str(source), str(root), generation],
        cwd=Path(__file__).resolve().parents[3],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "refused replaced non-regular workspace entry"
    marker = json.loads((root / ".execute.ataraxia-sandbox.json").read_text())
    assert marker["cleanup_disposition"] is None


@pytest.mark.covers(
    work="doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md",
    ac="AC-1",
)
@pytest.mark.parametrize("destination_kind", ["ancestor", "descendant"])
def test_retention_destination_cannot_overlap_managed_root(
    tmp_path: Path, destination_kind: str
) -> None:
    """Reject both parent and child paths before inspecting unrelated data."""
    source, root, generation, frozen = execution_environment(tmp_path)
    _prepare_review_fixture(frozen)
    destination = root.parent if destination_kind == "ancestor" else root / "execute"
    with sandbox.locked_sandbox(root, "execute", generation) as scope:
        sandbox.update_marker(scope, {"state": "ready"})
        with pytest.raises(ValueError, match="overlap"):
            sandbox_disposition.record_disposition(
                scope,
                owner_id="orchestrator-fixture",
                source_repository=source,
                work=WORK_PATH,
                reviewed=sandbox_disposition.ReviewedDisposition(
                    "maintainer-fixture",
                    "review-overlap",
                    sandbox_disposition.MaterialDecision(
                        "retain", "workspace-import", destination
                    ),
                    sandbox_disposition.MaterialDecision(
                        "discard", "reviewed-no-outputs"
                    ),
                ),
            )
    marker = json.loads((root / ".execute.ataraxia-sandbox.json").read_text())
    assert marker["cleanup_disposition"] is None


@pytest.mark.covers(
    work="doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md",
    ac="AC-1",
)
def test_invalid_review_record_refuses_without_changing_preserved_bytes(
    tmp_path: Path,
) -> None:
    """Reject invalid host review text and preserve workspace and output bytes."""
    source, root, generation, frozen = execution_environment(tmp_path)
    _prepare_review_fixture(frozen)
    with sandbox.locked_sandbox(root, "execute", generation) as scope:
        sandbox.update_marker(scope, {"state": "ready"})
        sandbox_execution.run_attempt(
            scope,
            source_repository=source,
            work=WORK_PATH,
            owner_id="orchestrator-fixture",
            mode="initial",
            session_id=None,
            invocation=sandbox_execution.Invocation(
                ("fixture-evaluation", "retain"), frozen, 10
            ),
            supervisor=ProvenSupervisor(),
        )
        workspace_before = (frozen / "tracked.txt").read_bytes()
        artifact = next((root / ".execute.runs").glob("*/output.txt"))
        output_before = artifact.read_bytes()
        reviewed = sandbox_disposition.ReviewedDisposition(
            "maintainer-fixture",
            "invalid\nreview",
            sandbox_disposition.MaterialDecision("discard", "review-workspace"),
            sandbox_disposition.MaterialDecision("discard", "review-output"),
        )
        with pytest.raises(ValueError, match="bounded plain text"):
            sandbox_disposition.record_disposition(
                scope,
                owner_id="orchestrator-fixture",
                source_repository=source,
                work=WORK_PATH,
                reviewed=reviewed,
            )
    marker = json.loads((root / ".execute.ataraxia-sandbox.json").read_text())
    assert marker["cleanup_disposition"] is None
    assert (frozen / "tracked.txt").read_bytes() == workspace_before
    assert artifact.read_bytes() == output_before


@pytest.mark.covers(
    work="doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md",
    ac="AC-1",
)
def test_missing_required_diagnostics_field_fails_closed(tmp_path: Path) -> None:
    """Reject a persisted disposition missing its required typed field."""
    _, root, generation, _, _, _, _ = _recorded_disposition(tmp_path)
    marker_path = root / ".execute.ataraxia-sandbox.json"
    marker = json.loads(marker_path.read_text())
    marker["cleanup_disposition"].pop("diagnostics_reference")
    marker_path.write_text(json.dumps(marker))
    artifact = next((root / ".execute.runs").glob("*/output.txt"))
    output_before = artifact.read_bytes()
    with (
        sandbox.locked_sandbox(root, "execute", generation) as scope,
        pytest.raises(ValueError, match="missing or malformed"),
    ):
        sandbox_disposition.validate_disposition(scope, owner_id="orchestrator-fixture")
    assert artifact.read_bytes() == output_before


@pytest.mark.covers(
    work="doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md",
    ac="AC-1",
)
def test_disposition_only_binding_allows_first_initial_attempt(tmp_path: Path) -> None:
    """Allow first execution after an empty binding created for disposition."""
    source, root, generation, frozen = execution_environment(tmp_path)
    _prepare_review_fixture(frozen)
    with sandbox.locked_sandbox(root, "execute", generation) as scope:
        sandbox.update_marker(scope, {"state": "ready"})
        sandbox_disposition.record_disposition(
            scope,
            owner_id="orchestrator-fixture",
            source_repository=source,
            work=WORK_PATH,
            reviewed=sandbox_disposition.ReviewedDisposition(
                "maintainer-fixture",
                "review-before-first-attempt",
                sandbox_disposition.MaterialDecision("discard", "review-workspace"),
                sandbox_disposition.MaterialDecision("discard", "review-no-outputs"),
            ),
        )
        result = sandbox_execution.run_attempt(
            scope,
            source_repository=source,
            work=WORK_PATH,
            owner_id="orchestrator-fixture",
            mode="initial",
            session_id=None,
            invocation=sandbox_execution.Invocation(
                ("fixture-evaluation", "first-attempt"), frozen, 10
            ),
            supervisor=ProvenSupervisor(),
        )
        state = sandbox_execution.read_execution_state(scope)
        assert result.status == "completed"
        assert state is not None
        assert state["binding"]["owner_id"] == "orchestrator-fixture"
        assert len(state["attempts"]) == 1
        with pytest.raises(ValueError, match="missing or malformed"):
            sandbox_disposition.validate_disposition(
                scope, owner_id="orchestrator-fixture"
            )


@pytest.mark.covers(
    work="doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md",
    ac="AC-1",
)
def test_recovered_unknown_run_can_receive_explicit_disposition(tmp_path: Path) -> None:
    """Accept fixture-supplied bound recovery proof, without claiming containment."""
    source, root, generation, frozen = execution_environment(tmp_path)
    _prepare_review_fixture(frozen)
    workspace_copy = tmp_path / "retained-workspace"
    outputs_copy = tmp_path / "retained-outputs"
    with sandbox.locked_sandbox(root, "execute", generation) as scope:
        sandbox.update_marker(scope, {"state": "ready"})
        result = sandbox_execution.run_attempt(
            scope,
            source_repository=source,
            work=WORK_PATH,
            owner_id="orchestrator-fixture",
            mode="initial",
            session_id=None,
            invocation=sandbox_execution.Invocation(
                ("fixture-evaluation", "recover"), frozen, 10
            ),
            supervisor=UnprovenSupervisor(session_id=SESSION),
        )
        assert result.status == "unknown"
        state = sandbox_execution.read_execution_state(scope)
        assert state is not None
        attempt = state["attempts"][0]
        workspace = sandbox.DestinationIdentity(
            attempt["workspace_device"], attempt["workspace_inode"]
        )
        evidence = sandbox_execution.RecoveryEvidence(
            sandbox_execution.StoppageEvidence(
                result.run_id,
                generation,
                workspace,
                "fixture-supervisor",
                "contained-tree-empty",
            ),
            Path(attempt["artifact_dir"]),
        )
        sandbox_execution.recover_attempt(scope, result.run_id, evidence)
        shutil.copytree(frozen, workspace_copy, symlinks=True)
        shutil.copytree(root / ".execute.runs", outputs_copy, symlinks=True)
        record = sandbox_disposition.record_disposition(
            scope,
            owner_id="orchestrator-fixture",
            source_repository=source,
            work=WORK_PATH,
            reviewed=_reviewed_material(workspace_copy, outputs_copy),
        )
        assert (
            sandbox_disposition.validate_disposition(
                scope, owner_id="orchestrator-fixture"
            )
            == record
        )
        recovered = sandbox_execution.read_execution_state(scope)
        assert recovered is not None
        assert recovered["attempts"][0]["status"] == "incomplete"
