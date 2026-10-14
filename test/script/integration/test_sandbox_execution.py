# SPDX-License-Identifier: Apache-2.0
"""Exercise bound sandbox attempts and fail-closed recovery."""

from contextlib import suppress
from dataclasses import replace
import json
import os
from pathlib import Path
import select
import shutil
import signal
import subprocess
import sys
from typing import IO, Literal, cast, override

import pytest

from script import sandbox, sandbox_disposition, sandbox_execution

WORK_PATH = "doc/feat/example/README.md"
SESSION = "12345678-1234-5678-1234-567812345678"
OTHER_SESSION = "87654321-4321-8765-4321-876543218765"


def mismatched_evidence(
    evidence: sandbox_execution.RecoveryEvidence, case: str
) -> sandbox_execution.RecoveryEvidence:
    stoppage = evidence.stoppage
    if case == "run":
        stoppage = replace(stoppage, run_id="wrong-run")
    elif case == "generation":
        stoppage = replace(stoppage, generation="0" * 32)
    elif case == "workspace":
        workspace = stoppage.workspace
        stoppage = replace(
            stoppage,
            workspace=sandbox.DestinationIdentity(
                workspace.device + 1, workspace.inode
            ),
        )
    artifact_dir = (
        evidence.artifact_dir.parent / "wrong-artifact"
        if case == "artifact"
        else evidence.artifact_dir
    )
    return sandbox_execution.RecoveryEvidence(stoppage, artifact_dir)


def execution_scope(root: Path, source: Path) -> tuple[str, sandbox.SandboxScope]:
    common = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "--git-common-dir"],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    ).stdout.strip()
    common_dir = (source / common).resolve()
    with sandbox.locked_sandbox(root, "execute", None, create=True) as empty:
        reserved = sandbox.reserve_destination(
            empty,
            {
                "common_dir": str(common_dir),
                "project": "fixture",
                "base": "a" * 40,
            },
        )
    assert reserved.generation is not None
    return reserved.generation, reserved


def execution_environment(tmp_path: Path) -> tuple[Path, Path, str, Path]:
    source = tmp_path / "source"
    source.mkdir()
    subprocess.run(
        ["git", "init", "--quiet", "--initial-branch=main", str(source)],
        check=True,
        timeout=10,
    )
    (source / WORK_PATH).parent.mkdir(parents=True)
    (source / WORK_PATH).write_text("# Fixture Evaluation Work\n")
    root = tmp_path / "managed"
    root.mkdir(mode=0o700)
    generation, _ = execution_scope(root, source)
    return source, root, generation, root / "execute"


class UnprovenSupervisor:
    """Run a real process but report no descendant-containment proof."""

    def __init__(self, session_id: str | None = None) -> None:
        self.session_id = session_id

    def run(
        self,
        invocation: sandbox_execution.Invocation,
        *,
        run_id: str,
        generation: str,
        workspace: sandbox.DestinationIdentity,
        artifact_dir: Path,
    ) -> sandbox_execution.ProcessResult:
        (artifact_dir / "output.txt").write_text("retained output\n")
        result = subprocess.run(
            invocation.command,
            cwd=invocation.cwd,
            check=False,
            capture_output=True,
            timeout=invocation.timeout_seconds,
            text=True,
        )
        return sandbox_execution.ProcessResult(result.returncode, self.session_id, None)


class ProvenSupervisor(UnprovenSupervisor):
    """Fixture supervisor that returns identity-bound stoppage evidence."""

    @override
    def run(
        self,
        invocation: sandbox_execution.Invocation,
        *,
        run_id: str,
        generation: str,
        workspace: sandbox.DestinationIdentity,
        artifact_dir: Path,
    ) -> sandbox_execution.ProcessResult:
        result = super().run(
            invocation,
            run_id=run_id,
            generation=generation,
            workspace=workspace,
            artifact_dir=artifact_dir,
        )
        return sandbox_execution.ProcessResult(
            result.exit_code,
            SESSION,
            sandbox_execution.StoppageEvidence(
                run_id,
                generation,
                workspace,
                "fixture-supervisor",
                "contained-tree-empty",
            ),
        )


class WrapperSupervisor:
    """Kill a real wrapper while its new-session descendant remains alive."""

    def __init__(self) -> None:
        self.gate: Path | None = None
        self.pid_path: Path | None = None
        self.done_descriptor: int | None = None
        self.child_pid: int | None = None
        self.released = False
        self.wrapper: subprocess.Popen[str] | None = None

    def run(
        self,
        invocation: sandbox_execution.Invocation,
        *,
        run_id: str,
        generation: str,
        workspace: sandbox.DestinationIdentity,
        artifact_dir: Path,
    ) -> sandbox_execution.ProcessResult:
        self.gate = artifact_dir / "descendant-gate"
        self.pid_path = artifact_dir / "descendant.pid"
        done = artifact_dir / "descendant-done"
        started = artifact_dir / "descendant-started"
        os.mkfifo(self.gate, 0o600)
        os.mkfifo(done, 0o600)
        self.done_descriptor = os.open(done, os.O_RDWR | os.O_NONBLOCK)
        self.wrapper = subprocess.Popen(
            [
                *invocation.command,
                str(self.gate),
                str(self.pid_path),
                str(done),
                str(started),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout = self.wrapper.stdout
        if stdout is None:
            raise RuntimeError("wrapper has no output stream")
        readable: list[IO[str]] = [stdout]
        writable: list[IO[str]] = []
        exceptional: list[IO[str]] = []
        ready, _, _ = select.select(
            readable, writable, exceptional, invocation.timeout_seconds
        )
        if not ready:
            self.wrapper.kill()
            _, stderr = self.wrapper.communicate(timeout=invocation.timeout_seconds)
            raise TimeoutError(f"wrapper did not report descendant startup: {stderr}")
        if stdout.readline() != "descendant-started\n":
            raise RuntimeError("wrapper did not report descendant startup")
        self.child_pid = int(self.pid_path.read_text())
        self.wrapper.kill()
        self.wrapper.communicate(timeout=invocation.timeout_seconds)
        self.wrapper = None
        return sandbox_execution.ProcessResult(None, None, None)

    def release_descendant(self) -> None:
        if self.released or self.gate is None or self.done_descriptor is None:
            return
        if self.child_pid is None:
            self.released = True
            return
        if self.child_pid is not None:
            try:
                os.kill(self.child_pid, 0)
            except ProcessLookupError:
                self.released = True
                return
        gate_descriptor = os.open(self.gate, os.O_RDWR | os.O_NONBLOCK)
        try:
            os.write(gate_descriptor, b"x")
        finally:
            os.close(gate_descriptor)
        readable: list[int] = [self.done_descriptor]
        writable: list[int] = []
        exceptional: list[int] = []
        ready, _, _ = select.select(readable, writable, exceptional, 10)
        if not ready:
            raise TimeoutError("descendant did not report completion")
        os.read(self.done_descriptor, len(b"stopped"))
        self.released = True

    def cleanup(self) -> None:
        if self.wrapper is not None and self.wrapper.poll() is None:
            self.wrapper.kill()
            self.wrapper.communicate(timeout=10)
        try:
            self.release_descendant()
        finally:
            if self.child_pid is not None and not self.released:
                with suppress(ProcessLookupError):
                    os.kill(self.child_pid, signal.SIGTERM)
            if self.done_descriptor is not None:
                os.close(self.done_descriptor)
                self.done_descriptor = None


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
        (sys.executable, "-c", "print('prepared')"), frozen, 10
    )
    with sandbox.locked_sandbox(root, "execute", generation) as scope:
        result = sandbox_execution.run_attempt(
            scope,
            source_repository=source,
            work=WORK_PATH,
            owner_id="orchestrator-fixture",
            mode="initial",
            session_id=None,
            invocation=invocation,
            supervisor=UnprovenSupervisor(),
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
    assert attempt["session_id"] is None
    assert (
        Path(attempt["artifact_dir"], "output.txt").read_text() == "retained output\n"
    )
    assert Path(attempt["artifact_dir"]).stat().st_mode & 0o777 == 0o700


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
                    (sys.executable, "-c", "print('must not run')"), frozen, 10
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
                (sys.executable, "-c", "print('initial')"), frozen, 10
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
                (sys.executable, "-c", "raise SystemExit(91)"), frozen, 10
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
                (sys.executable, "-c", "raise SystemExit(17)"), frozen, 10
            ),
            supervisor=ProvenSupervisor(),
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
                (sys.executable, "-c", "print('finished')"), frozen, 10
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
    invocation = sandbox_execution.Invocation(
        (sys.executable, "-c", "print('must not run')"), frozen, 10
    )

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
            (sys.executable,),
            10.0,
            "does not match the binding",
        ),
        (
            "resume",
            "orchestrator-fixture",
            "not-a-uuid",
            ("execute",),
            (sys.executable,),
            10.0,
            "must be a UUID",
        ),
        (
            "resume",
            "orchestrator-fixture",
            SESSION,
            ("..", "source"),
            (sys.executable,),
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
            (sys.executable,),
            10.0,
            "mode must be initial or resume",
        ),
        (
            "resume",
            "orchestrator-fixture",
            SESSION,
            ("execute",),
            (sys.executable,),
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
                (sys.executable, "-c", "print('initial')"), frozen, 10
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

    invocation = sandbox_execution.Invocation(
        (sys.executable, "-c", "print('must not run')"), frozen, 10
    )

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
                (sys.executable, "-c", "print('finished')"), frozen, 10
            ),
            supervisor=UnprovenSupervisor(SESSION),
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


def _verify_live_attempt_blocks_and_recovers(
    scope: sandbox.SandboxScope,
    root: Path,
    generation: str,
    source: Path,
    invocation: sandbox_execution.Invocation,
    supervisor: WrapperSupervisor,
    result: sandbox_execution.AttemptResult,
) -> None:
    assert supervisor.child_pid is not None
    os.kill(supervisor.child_pid, 0)
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
    recovery_evidence = sandbox_execution.RecoveryEvidence(
        sandbox_execution.StoppageEvidence(
            result.run_id,
            generation,
            workspace,
            "fixture-supervisor",
            "contained-tree-empty",
        ),
        Path(attempt["artifact_dir"]),
    )
    unsupported = replace(
        recovery_evidence,
        stoppage=replace(recovery_evidence.stoppage, run_id="0" * 32),
    )
    with pytest.raises(ValueError, match="does not match"):
        sandbox_execution.recover_attempt(scope, result.run_id, unsupported)
    supervisor.release_descendant()
    sandbox_execution.recover_attempt(scope, result.run_id, recovery_evidence)
    assert sandbox.probe_sandbox(root, "execute", generation).activity == "active"


@pytest.mark.covers(
    work="doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md",
    ac="AC-1",
)
def test_live_process_keeps_attempt_unknown_and_blocks_another_launch(
    tmp_path: Path,
) -> None:
    """Refuse another attempt while an unproven real child is still running."""
    # Given
    source, root, generation, frozen = execution_environment(tmp_path)
    supervisor = WrapperSupervisor()
    invocation = sandbox_execution.Invocation(
        (
            sys.executable,
            str(
                Path(__file__).resolve().parents[1]
                / "fixtures"
                / "sandbox_wrapper_with_descendant.py"
            ),
            "wrapper",
        ),
        frozen,
        10,
    )

    # When
    try:
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
            _verify_live_attempt_blocks_and_recovers(
                scope, root, generation, source, invocation, supervisor, result
            )
    finally:
        supervisor.cleanup()

    # Then
    marker = json.loads((root / ".execute.ataraxia-sandbox.json").read_text())
    assert result.status == "unknown"
    assert marker["execution"]["attempts"][0]["status"] == "incomplete"
    assert marker["execution"]["attempts"][0].get("exit_code") is None
    assert marker["execution"]["attempts"][1]["status"] == "rejected"


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
                (sys.executable, "-c", "print('retained')"), frozen, 10
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
                (sys.executable, "-c", "raise SystemExit(1)"), frozen, 10
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
                (sys.executable, "-c", "print('uncertain')"), frozen, 10
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
                (sys.executable, "-c", "print('retained')"), frozen, 10
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
                (sys.executable, "-c", "print('first attempt')"), frozen, 10
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
                (sys.executable, "-c", "print('recovered output')"), frozen, 10
            ),
            supervisor=UnprovenSupervisor(SESSION),
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
