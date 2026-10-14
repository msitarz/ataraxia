# SPDX-License-Identifier: Apache-2.0
"""Small source and supervisor fixtures for sandbox lifecycle tests."""

from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
import subprocess
from typing import override

from script import sandbox, sandbox_execution

WORK_PATH = "doc/feat/example/README.md"
SESSION = "12345678-1234-5678-1234-567812345678"
OTHER_SESSION = "87654321-4321-8765-4321-876543218765"


@dataclass(frozen=True)
class SupervisorCall:
    """Arguments passed across the host-owned supervisor boundary."""

    invocation: sandbox_execution.Invocation
    run_id: str
    generation: str
    workspace: sandbox.DestinationIdentity
    artifact_dir: Path


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


def execution_scope(root: Path, source: Path) -> str:
    common = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "--git-common-dir"],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    ).stdout.strip()
    common_dir = (source / common).resolve()
    with sandbox.locked_sandbox(root, "execute", None, create=True) as scope:
        sandbox.reserve_destination(
            scope,
            {
                "common_dir": str(common_dir),
                "project": "fixture",
                "base": "a" * 40,
            },
        )
    assert scope.generation is not None
    return scope.generation


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
    generation = execution_scope(root, source)
    return source, root, generation, root / "execute"


class UnprovenSupervisor:
    """Return deterministic results without emulating an external process."""

    def __init__(
        self,
        exit_code: int | None = 0,
        session_id: str | None = None,
        on_run: Callable[[], None] | None = None,
        failure: str | None = None,
    ) -> None:
        self.exit_code = exit_code
        self.session_id = session_id
        self.on_run = on_run
        self.failure = failure
        self.calls: list[SupervisorCall] = []

    def run(
        self,
        invocation: sandbox_execution.Invocation,
        *,
        run_id: str,
        generation: str,
        workspace: sandbox.DestinationIdentity,
        artifact_dir: Path,
    ) -> sandbox_execution.ProcessResult:
        self.calls.append(
            SupervisorCall(invocation, run_id, generation, workspace, artifact_dir)
        )
        (artifact_dir / "output.txt").write_text("retained output\n")
        if self.on_run is not None:
            self.on_run()
        if self.failure is not None:
            raise RuntimeError(self.failure)
        return sandbox_execution.ProcessResult(self.exit_code, self.session_id, None)


class ProvenSupervisor(UnprovenSupervisor):
    """Return a fixture attestation tied to the received run identity."""

    def __init__(self, exit_code: int = 0, session_id: str = SESSION) -> None:
        super().__init__(exit_code, session_id)

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
        super().run(
            invocation,
            run_id=run_id,
            generation=generation,
            workspace=workspace,
            artifact_dir=artifact_dir,
        )
        return sandbox_execution.ProcessResult(
            self.exit_code,
            self.session_id,
            sandbox_execution.StoppageEvidence(
                run_id,
                generation,
                workspace,
                "fixture-supervisor",
                "contained-tree-empty",
            ),
        )


class UnknownSupervisor(UnprovenSupervisor):
    """Represent a supervisor that cannot establish process-tree stoppage."""

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
        super().run(
            invocation,
            run_id=run_id,
            generation=generation,
            workspace=workspace,
            artifact_dir=artifact_dir,
        )
        return sandbox_execution.ProcessResult(None, None, None)
