# SPDX-License-Identifier: Apache-2.0
"""Exercise bound sandbox attempts and fail-closed recovery."""

from dataclasses import replace
import json
from pathlib import Path
from typing import Literal, cast

import pytest

from script import sandbox, sandbox_execution
from test.script.integration.sandbox_lifecycle_support import (
    OTHER_SESSION,
    SESSION,
    WORK_PATH,
    ProvenSupervisor,
    SupervisorCall,
    UnknownSupervisor,
    UnprovenSupervisor,
    execution_environment,
    mismatched_evidence,
)


@pytest.mark.covers(
    work="doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md",
    ac="AC-1",
)
def test_initial_attempt_binds_source_work_and_retains_artifact(tmp_path: Path) -> None:
    """Bind a source Work absent from the frozen workspace before launch."""
    # Given
    source, root, generation, frozen = execution_environment(tmp_path)
    assert not (frozen / WORK_PATH).exists()

    # When
    invocation = sandbox_execution.Invocation(
        ("fixture-evaluation", "prepared"), frozen, 10
    )
    supervisor = UnprovenSupervisor(session_id=SESSION)
    with sandbox.locked_sandbox(root, "execute", generation) as scope:
        result = sandbox_execution.run_attempt(
            scope,
            source_repository=source,
            work=WORK_PATH,
            owner_id="orchestrator-fixture",
            mode="initial",
            session_id=None,
            invocation=invocation,
            supervisor=supervisor,
        )

    # Then
    marker = json.loads((root / ".execute.ataraxia-sandbox.json").read_text())
    attempt = marker["execution"]["attempts"][0]
    assert result.status == "unknown"
    assert marker["execution"]["binding"] == {
        "common_dir": str((source / ".git").resolve()),
        "work": WORK_PATH,
        "owner_id": "orchestrator-fixture",
    }
    assert attempt["status"] == "unknown"
    assert attempt["session_id"] == SESSION
    assert (
        Path(attempt["artifact_dir"], "output.txt").read_text() == "retained output\n"
    )
    assert Path(attempt["artifact_dir"]).stat().st_mode & 0o777 == 0o700
    assert supervisor.calls == [
        SupervisorCall(
            invocation,
            attempt["run_id"],
            generation,
            sandbox.DestinationIdentity(
                attempt["workspace_device"], attempt["workspace_inode"]
            ),
            Path(attempt["artifact_dir"]),
        )
    ]


@pytest.mark.covers(
    work="doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md",
    ac="AC-1",
)
def test_initial_attempt_rejects_supplied_session_identity(tmp_path: Path) -> None:
    """Only the supervisor may report a UUID for an initial attempt."""
    source, root, generation, frozen = execution_environment(tmp_path)
    launched = False

    class MustNotLaunch:
        def run(
            self,
            invocation: sandbox_execution.Invocation,
            *,
            run_id: str,
            generation: str,
            workspace: sandbox.DestinationIdentity,
            artifact_dir: Path,
        ) -> sandbox_execution.ProcessResult:
            nonlocal launched
            launched = True
            raise AssertionError("invalid initial session must not launch")

    with sandbox.locked_sandbox(root, "execute", generation) as scope:
        sandbox.update_marker(scope, {"cleanup_disposition": {"approved": True}})
        with pytest.raises(ValueError, match="cannot supply a session"):
            sandbox_execution.run_attempt(
                scope,
                source_repository=source,
                work=WORK_PATH,
                owner_id="orchestrator-fixture",
                mode="initial",
                session_id=SESSION,
                invocation=sandbox_execution.Invocation(
                    ("must-not-launch",), frozen, 10
                ),
                supervisor=MustNotLaunch(),
            )

    marker = json.loads((root / ".execute.ataraxia-sandbox.json").read_text())
    assert not launched
    assert marker["cleanup_disposition"] is None
    assert "execution" not in marker


@pytest.mark.covers(
    work="doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md",
    ac="AC-1",
)
def test_resume_identity_mismatch_is_retained_and_invalidates_disposition(
    tmp_path: Path,
) -> None:
    """Reject a mismatched resume without launching the command."""
    # Given
    source, root, generation, frozen = execution_environment(tmp_path)
    with sandbox.locked_sandbox(root, "execute", generation) as scope:
        initial = sandbox_execution.run_attempt(
            scope,
            source_repository=source,
            work=WORK_PATH,
            owner_id="orchestrator-fixture",
            mode="initial",
            session_id=None,
            invocation=sandbox_execution.Invocation(
                ("fixture-evaluation", "initial"), frozen, 10
            ),
            supervisor=ProvenSupervisor(),
        )
        assert initial.status == "completed"
        sandbox.update_marker(scope, {"cleanup_disposition": {"approved": True}})
        result = sandbox_execution.run_attempt(
            scope,
            source_repository=source,
            work=WORK_PATH,
            owner_id="orchestrator-fixture",
            mode="resume",
            session_id=OTHER_SESSION,
            invocation=sandbox_execution.Invocation(
                ("fixture-evaluation", "resume-invalid"), frozen, 10
            ),
            supervisor=UnprovenSupervisor(),
        )
        resumed = sandbox_execution.run_attempt(
            scope,
            source_repository=source,
            work=WORK_PATH,
            owner_id="orchestrator-fixture",
            mode="resume",
            session_id=SESSION,
            invocation=sandbox_execution.Invocation(
                ("fixture-evaluation", "resume-fails"), frozen, 10
            ),
            supervisor=ProvenSupervisor(exit_code=17),
        )

    # Then
    marker = json.loads((root / ".execute.ataraxia-sandbox.json").read_text())
    assert result.status == "rejected"
    assert resumed.status == "failed"
    assert [attempt["status"] for attempt in marker["execution"]["attempts"]] == [
        "completed",
        "rejected",
        "failed",
    ]
    assert marker["cleanup_disposition"] is None
    attempts = marker["execution"]["attempts"]
    assert len({attempt["run_id"] for attempt in attempts}) == 3
    assert attempts[1]["artifact_dir"] == ""
    assert attempts[0]["artifact_dir"] != attempts[2]["artifact_dir"]
    assert [attempt["session_id"] for attempt in attempts] == [SESSION, None, SESSION]


def corrupt_execution_marker(marker_path: Path, corruption: str) -> None:
    marker = json.loads(marker_path.read_text())
    execution = marker["execution"]
    attempt = execution["attempts"][0]
    if corruption == "binding":
        execution["binding"]["common_dir"] = str(marker_path.parent / "other.git")
    elif corruption == "generation":
        attempt["generation"] = "0" * 32
    elif corruption == "workspace":
        attempt["workspace_inode"] += 1
    elif corruption == "session":
        attempt["session_id"] = "not-a-uuid"
    elif corruption == "rejected-session":
        attempt["status"] = "rejected"
        attempt["artifact_dir"] = ""
    else:
        attempt["exit_code"] = 17
    marker_path.write_text(json.dumps(marker))


@pytest.mark.covers(
    work="doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md",
    ac="AC-1",
)
@pytest.mark.parametrize(
    "corruption",
    [
        "binding",
        "generation",
        "workspace",
        "session",
        "outcome",
        "rejected-session",
    ],
)
def test_execution_state_rejects_corrupt_identity_and_outcomes(
    tmp_path: Path, corruption: str
) -> None:
    """Do not grant resume authority from malformed persisted execution state."""
    source, root, generation, frozen = execution_environment(tmp_path)
    with sandbox.locked_sandbox(root, "execute", generation) as scope:
        sandbox_execution.run_attempt(
            scope,
            source_repository=source,
            work=WORK_PATH,
            owner_id="orchestrator-fixture",
            mode="initial",
            session_id=None,
            invocation=sandbox_execution.Invocation(
                ("fixture-evaluation", "finish"), frozen, 10
            ),
            supervisor=ProvenSupervisor(),
        )
        state = sandbox_execution.read_execution_state(scope)
        assert state is not None
        assert state["binding"]["owner_id"] == "orchestrator-fixture"
        assert state["attempts"][0]["session_id"] == SESSION

        corrupt_execution_marker(root / ".execute.ataraxia-sandbox.json", corruption)
        with pytest.raises(ValueError, match=r"execution|malformed"):
            sandbox_execution.read_execution_state(scope)


@pytest.mark.covers(
    work="doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md",
    ac="AC-1",
)
@pytest.mark.parametrize(
    "work",
    [
        "doc/feat/missing/README.md",
        "../README.md",
        "doc/feat/example/spec.md",
    ],
    ids=["missing-work", "escaped-work", "spec-is-not-readme"],
)
def test_invalid_source_work_revokes_disposition_without_an_attempt(
    tmp_path: Path, work: str
) -> None:
    """Reject a missing, escaped, or non-README Work before launch."""
    # Given
    source, root, generation, frozen = execution_environment(tmp_path)
    (source / "doc/feat/example/spec.md").write_text("# Not a Work README\n")
    invocation = sandbox_execution.Invocation(("must-not-launch",), frozen, 10)

    # When
    with sandbox.locked_sandbox(root, "execute", generation) as scope:
        sandbox.update_marker(scope, {"cleanup_disposition": {"approved": True}})
        with pytest.raises(ValueError):
            sandbox_execution.run_attempt(
                scope,
                source_repository=source,
                work=work,
                owner_id="orchestrator-fixture",
                mode="initial",
                session_id=None,
                invocation=invocation,
                supervisor=UnprovenSupervisor(),
            )

    # Then
    marker = json.loads((root / ".execute.ataraxia-sandbox.json").read_text())
    assert marker["cleanup_disposition"] is None
    assert "execution" not in marker
    runs = root / ".execute.runs"
    assert not runs.exists()


@pytest.mark.covers(
    work="doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md",
    ac="AC-1",
)
@pytest.mark.parametrize(
    ("mode", "owner_id", "session_id", "cwd_parts", "command", "timeout", "error"),
    [
        (
            "resume",
            "different-owner",
            SESSION,
            ("execute",),
            ("fixture-evaluation",),
            10.0,
            "does not match the binding",
        ),
        (
            "resume",
            "orchestrator-fixture",
            "not-a-uuid",
            ("execute",),
            ("fixture-evaluation",),
            10.0,
            "must be a UUID",
        ),
        (
            "resume",
            "orchestrator-fixture",
            SESSION,
            ("..", "source"),
            ("fixture-evaluation",),
            10.0,
            "inside the sandbox",
        ),
        (
            "resume",
            "orchestrator-fixture",
            SESSION,
            ("execute",),
            (),
            10.0,
            "command is empty",
        ),
        (
            "resume",
            "orchestrator-fixture",
            SESSION,
            ("execute",),
            ("fixture-evaluation",),
            10.0,
            "mode must be initial or resume",
        ),
        (
            "resume",
            "orchestrator-fixture",
            SESSION,
            ("execute",),
            ("fixture-evaluation",),
            float("nan"),
            "finite positive timeout",
        ),
    ],
    ids=[
        "owner-mismatch",
        "malformed-session",
        "outside-cwd",
        "empty-command",
        "invalid-mode",
        "invalid-timeout",
    ],
)
def test_invalid_resume_preserves_prior_identity_and_artifact(
    tmp_path: Path,
    mode: str,
    owner_id: str,
    session_id: str,
    cwd_parts: tuple[str, ...],
    command: tuple[str, ...],
    timeout: float,
    error: str,
) -> None:
    """Reject invalid resume identity while preserving the earlier attempt."""
    # Given
    source, root, generation, frozen = execution_environment(tmp_path)
    with sandbox.locked_sandbox(root, "execute", generation) as scope:
        initial = sandbox_execution.run_attempt(
            scope,
            source_repository=source,
            work=WORK_PATH,
            owner_id="orchestrator-fixture",
            mode="initial",
            session_id=None,
            invocation=sandbox_execution.Invocation(
                ("fixture-evaluation", "initial"), frozen, 10
            ),
            supervisor=ProvenSupervisor(),
        )
        sandbox.update_marker(scope, {"cleanup_disposition": {"approved": True}})
        before = json.loads((root / ".execute.ataraxia-sandbox.json").read_text())

        # When
        with pytest.raises(ValueError, match=error):
            sandbox_execution.run_attempt(
                scope,
                source_repository=source,
                work=WORK_PATH,
                owner_id=owner_id,
                mode=cast(
                    Literal["initial", "resume"],
                    "invalid" if error.startswith("mode") else mode,
                ),
                session_id=session_id,
                invocation=sandbox_execution.Invocation(
                    command, root.joinpath(*cwd_parts), timeout
                ),
                supervisor=UnprovenSupervisor(),
            )

    # Then
    after = json.loads((root / ".execute.ataraxia-sandbox.json").read_text())
    assert initial.status == "completed"
    assert after["execution"]["binding"] == before["execution"]["binding"]
    assert [item["status"] for item in after["execution"]["attempts"]] == [
        "completed",
        "rejected",
    ]
    assert Path(
        after["execution"]["attempts"][0]["artifact_dir"], "output.txt"
    ).is_file()
    assert after["cleanup_disposition"] is None


@pytest.mark.covers(
    work="doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md",
    ac="AC-1",
)
def test_interrupted_attempt_marker_write_prevents_launch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Do not start a process if its durable running record cannot be written."""
    # Given
    source, root, generation, frozen = execution_environment(tmp_path)
    launched = False

    class MustNotLaunch:
        def run(
            self,
            invocation: sandbox_execution.Invocation,
            *,
            run_id: str,
            generation: str,
            workspace: sandbox.DestinationIdentity,
            artifact_dir: Path,
        ) -> sandbox_execution.ProcessResult:
            nonlocal launched
            launched = True
            raise AssertionError("supervisor must not run")

    real_write = sandbox._atomic_record

    def interrupted_write(
        write_root: Path,
        name: str,
        record: dict[str, sandbox.JsonValue],
        *,
        create: bool,
    ) -> None:
        if "execution" in record:
            raise OSError("simulated interrupted marker write")
        real_write(write_root, name, record, create=create)

    invocation = sandbox_execution.Invocation(("must-not-launch",), frozen, 10)

    # When
    with sandbox.locked_sandbox(root, "execute", generation) as scope:
        sandbox.update_marker(scope, {"cleanup_disposition": {"approved": True}})
        monkeypatch.setattr(sandbox, "_atomic_record", interrupted_write)
        with pytest.raises(OSError, match="simulated interrupted"):
            sandbox_execution.run_attempt(
                scope,
                source_repository=source,
                work=WORK_PATH,
                owner_id="orchestrator-fixture",
                mode="initial",
                session_id=None,
                invocation=invocation,
                supervisor=MustNotLaunch(),
            )

    # Then
    marker = json.loads((root / ".execute.ataraxia-sandbox.json").read_text())
    assert not launched
    assert marker["cleanup_disposition"] is None
    assert "execution" not in marker
    runs = root / ".execute.runs"
    assert not runs.exists()


@pytest.mark.covers(
    work="doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md",
    ac="AC-1",
)
def test_supervisor_exception_is_recorded_as_unknown(
    tmp_path: Path,
) -> None:
    """Preserve uncertainty when the host supervisor raises during an attempt."""
    # Given
    source, root, generation, frozen = execution_environment(tmp_path)
    supervisor = UnprovenSupervisor(failure="supervisor interrupted")
    invocation = sandbox_execution.Invocation(("fixture-evaluation",), frozen, 10)

    # When
    with sandbox.locked_sandbox(root, "execute", generation) as scope:
        result = sandbox_execution.run_attempt(
            scope,
            source_repository=source,
            work=WORK_PATH,
            owner_id="orchestrator-fixture",
            mode="initial",
            session_id=None,
            invocation=invocation,
            supervisor=supervisor,
        )

    # Then
    marker = json.loads((root / ".execute.ataraxia-sandbox.json").read_text())
    attempt = marker["execution"]["attempts"][0]
    assert result.status == "unknown"
    assert attempt["status"] == "unknown"
    assert attempt["message"] == "supervisor outcome uncertain: supervisor interrupted"
    assert len(supervisor.calls) == 1


@pytest.mark.covers(
    work="doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md",
    ac="AC-1",
)
@pytest.mark.parametrize(
    "case",
    ["run", "generation", "workspace", "artifact"],
    ids=["wrong-run", "wrong-generation", "wrong-workspace", "wrong-artifacts"],
)
def test_recovery_requires_matching_stoppage_and_retained_directory(
    tmp_path: Path,
    case: str,
) -> None:
    """Refuse unmatched evidence, then recover only the bound retained run."""
    # Given
    source, root, generation, frozen = execution_environment(tmp_path)
    with sandbox.locked_sandbox(root, "execute", generation) as scope:
        result = sandbox_execution.run_attempt(
            scope,
            source_repository=source,
            work=WORK_PATH,
            owner_id="orchestrator-fixture",
            mode="initial",
            session_id=None,
            invocation=sandbox_execution.Invocation(
                ("fixture-evaluation", "finish"), frozen, 10
            ),
            supervisor=UnprovenSupervisor(session_id=SESSION),
        )
        marker = json.loads((root / ".execute.ataraxia-sandbox.json").read_text())
        attempt = marker["execution"]["attempts"][0]
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

        # When
        wrong = mismatched_evidence(evidence, case)
        with pytest.raises(ValueError, match="does not match"):
            sandbox_execution.recover_attempt(scope, result.run_id, wrong)
        sandbox_execution.recover_attempt(scope, result.run_id, evidence)

    # Then
    marker = json.loads((root / ".execute.ataraxia-sandbox.json").read_text())
    assert result.session_id == SESSION
    assert marker["execution"]["attempts"][0]["status"] == "incomplete"
    assert marker["execution"]["attempts"][0]["artifact_dir"] == str(
        evidence.artifact_dir
    )


@pytest.mark.covers(
    work="doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md",
    ac="AC-1",
)
def test_uncertain_attempt_keeps_lock_and_requires_bound_recovery(
    tmp_path: Path,
) -> None:
    """Keep an uncertain attempt blocked until matching host evidence arrives."""
    # Given
    source, root, generation, frozen = execution_environment(tmp_path)
    lock_during_run: list[str] = []
    supervisor = UnknownSupervisor(
        on_run=lambda: lock_during_run.append(
            sandbox.probe_sandbox(root, "execute", generation).activity
        )
    )
    invocation = sandbox_execution.Invocation(("not-launched",), frozen, 10)

    # When
    with sandbox.locked_sandbox(root, "execute", generation) as scope:
        result = sandbox_execution.run_attempt(
            scope,
            source_repository=source,
            work=WORK_PATH,
            owner_id="orchestrator-fixture",
            mode="initial",
            session_id=None,
            invocation=invocation,
            supervisor=supervisor,
        )
        assert lock_during_run == ["active"]
        state = sandbox_execution.read_execution_state(scope)
        assert state is not None
        attempt = state["attempts"][0]
        assert attempt["status"] == "unknown"
        with pytest.raises(ValueError, match="host-side recovery"):
            sandbox_execution.run_attempt(
                scope,
                source_repository=source,
                work=WORK_PATH,
                owner_id="orchestrator-fixture",
                mode="initial",
                session_id=None,
                invocation=invocation,
                supervisor=supervisor,
            )
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
        bad_evidence = replace(
            evidence,
            stoppage=replace(evidence.stoppage, run_id="0" * 32),
        )
        with pytest.raises(ValueError, match="does not match"):
            sandbox_execution.recover_attempt(scope, result.run_id, bad_evidence)
        sandbox_execution.recover_attempt(scope, result.run_id, evidence)

    # Then
    marker = json.loads((root / ".execute.ataraxia-sandbox.json").read_text())
    assert result.status == "unknown"
    assert marker["execution"]["attempts"][0]["status"] == "incomplete"
    assert marker["execution"]["attempts"][0].get("exit_code") is None
    assert marker["execution"]["attempts"][1]["status"] == "rejected"
