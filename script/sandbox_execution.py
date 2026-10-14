# SPDX-License-Identifier: Apache-2.0
"""Persist bound execution attempts and require evidence before recovery."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import math
import os
from pathlib import Path
import re
import secrets
import stat
from typing import Literal, NotRequired, Protocol, TypedDict, cast
from uuid import UUID

from script import sandbox
from script.work_paths import resolve_work_file


class WorkBinding(TypedDict):
    """Source Work and host-controlled owner bound to this sandbox."""

    common_dir: str
    work: str
    owner_id: str


class AttemptRecord(TypedDict):
    """One durable initial or resumed process attempt."""

    run_id: str
    generation: str
    workspace_device: int
    workspace_inode: int
    session_id: str | None
    status: Literal[
        "running", "completed", "failed", "unknown", "rejected", "incomplete"
    ]
    artifact_dir: str
    message: NotRequired[str]
    exit_code: NotRequired[int]
    observed_session_id: NotRequired[str]


class ExecutionState(TypedDict):
    """Typed execution extension stored separately from owned marker fields."""

    binding: WorkBinding
    attempts: list[AttemptRecord]


@dataclass(frozen=True)
class StoppageEvidence:
    """Supervisor attestation tied to one attempt and workspace identity."""

    run_id: str
    generation: str
    workspace: sandbox.DestinationIdentity
    supervisor_id: str
    proof: Literal["contained-tree-empty"]


@dataclass(frozen=True)
class ProcessResult:
    """Known exit status, available session identity, and stoppage proof."""

    exit_code: int | None
    session_id: str | None
    stoppage: StoppageEvidence | None


@dataclass(frozen=True)
class Invocation:
    """One host-approved command and its bounded working-directory request."""

    command: tuple[str, ...]
    cwd: Path
    timeout_seconds: float


class ProcessSupervisor(Protocol):
    """Run one process and attest complete tree stoppage when it is known."""

    def run(
        self,
        invocation: Invocation,
        *,
        run_id: str,
        generation: str,
        workspace: sandbox.DestinationIdentity,
        artifact_dir: Path,
    ) -> ProcessResult:
        """Run the command and attest stoppage only when the whole tree is known."""
        ...


@dataclass(frozen=True)
class RecoveryEvidence:
    """Trusted host report bound to one stopped run and its retained directory."""

    stoppage: StoppageEvidence
    artifact_dir: Path


@dataclass(frozen=True)
class AttemptResult:
    """Outcome and stable run/session identities returned to the host caller."""

    run_id: str
    status: Literal["completed", "failed", "unknown", "rejected"]
    session_id: str | None
    exit_code: int | None


def _common_directory(repository: Path) -> str:
    common = Path(
        sandbox.run([
            "git",
            "-C",
            str(repository),
            "rev-parse",
            "--git-common-dir",
        ])
    )
    if not common.is_absolute():
        common = repository / common
    return str(common.resolve(strict=True))


def _binding(
    scope: sandbox.SandboxScope,
    repository: Path,
    work: str,
    owner_id: str,
) -> WorkBinding:
    if scope.generation is None or scope.record is None:
        raise ValueError("execution requires a reserved sandbox")
    repository = repository.resolve(strict=True)
    if not repository.is_dir():
        raise ValueError("source repository is not a directory")
    common = _common_directory(repository)
    if common != scope.record.owned["common_dir"]:
        raise ValueError("source repository does not own this sandbox")
    if not owner_id or len(owner_id) > 256 or any(ord(char) < 32 for char in owner_id):
        raise ValueError("invalid host owner identity")
    work_file = resolve_work_file(repository, work)
    if work_file.name != "README.md":
        raise ValueError("execution binding must name a source Work README.md")
    return {"common_dir": common, "work": work, "owner_id": owner_id}


def _read_state(marker: sandbox.Marker) -> ExecutionState | None:
    raw = marker.extensions.get("execution")
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("malformed execution state")
    binding = raw.get("binding")
    attempts = raw.get("attempts")
    if (
        not isinstance(binding, dict)
        or not isinstance(binding.get("common_dir"), str)
        or not isinstance(binding.get("work"), str)
        or not isinstance(binding.get("owner_id"), str)
        or not isinstance(attempts, list)
    ):
        raise ValueError("malformed execution state")
    checked: list[AttemptRecord] = []
    run_ids: set[str] = set()
    for attempt in attempts:
        parsed = _parse_attempt(attempt)
        if parsed is None or parsed["run_id"] in run_ids:
            raise ValueError("malformed execution attempt")
        run_ids.add(parsed["run_id"])
        checked.append(parsed)
    typed_binding: WorkBinding = {
        "common_dir": binding["common_dir"],
        "work": binding["work"],
        "owner_id": binding["owner_id"],
    }
    if (
        not typed_binding["work"]
        or not typed_binding["owner_id"]
        or len(typed_binding["owner_id"]) > 256
        or any(ord(char) < 32 for char in typed_binding["owner_id"])
    ):
        raise ValueError("malformed execution binding")
    owned = marker.owned
    destination = sandbox.DestinationIdentity(
        owned["destination_device"], owned["destination_inode"]
    )
    if typed_binding["common_dir"] != owned["common_dir"] or any(
        item["generation"] != owned["generation"]
        or sandbox.DestinationIdentity(
            item["workspace_device"], item["workspace_inode"]
        )
        != destination
        for item in checked
    ):
        raise ValueError("execution state does not match sandbox identity")
    return {"binding": typed_binding, "attempts": checked}


def read_execution_state(scope: sandbox.SandboxScope) -> ExecutionState | None:
    """Read validated execution state under the caller's current lock lease.

    Returns:
        The current validated execution extension, if one has been recorded.

    Raises:
        ValueError: If the lease is stale or the durable execution state is malformed.
    """
    current = sandbox.refresh_scope(scope)
    if current.record is None:
        raise ValueError("execution state requires a reserved sandbox")
    return _read_state(current.record)


def work_binding(
    scope: sandbox.SandboxScope,
    *,
    owner_id: str,
    source_repository: Path | None = None,
    work: str | None = None,
) -> WorkBinding:
    """Return the existing host binding or establish one for failed preparation.

    Existing bindings remain valid after their source Work file is removed. An
    unbound sandbox requires both the source repository and its Work README.

    Raises:
        ValueError: If the lease, owner, Work path, or reserved sandbox is invalid.
    """
    current = sandbox.refresh_scope(scope)
    if current.record is None:
        raise ValueError("Work binding requires a reserved sandbox")
    state = read_execution_state(current)
    if state is not None:
        binding = state["binding"]
        if binding["owner_id"] != owner_id or (
            work is not None and binding["work"] != work
        ):
            raise ValueError("Work or owner does not match the existing binding")
        return binding
    if source_repository is None or work is None:
        raise ValueError("unbound sandbox requires source repository and Work README")
    return _binding(current, source_repository, work, owner_id)


def _parse_attempt(raw: object) -> AttemptRecord | None:
    if not isinstance(raw, dict):
        return None
    value: Mapping[str, object] = raw
    run_id, generation = value.get("run_id"), value.get("generation")
    device, inode = value.get("workspace_device"), value.get("workspace_inode")
    session_id, status = value.get("session_id"), value.get("status")
    artifact_dir, message = value.get("artifact_dir"), value.get("message")
    exit_code = value.get("exit_code")
    observed_session_id = value.get("observed_session_id")
    try:
        if any(
            isinstance(session, str) and _canonical_session(session) != session
            for session in (session_id, observed_session_id)
        ):
            return None
    except ValueError:
        return None
    if (
        not isinstance(run_id, str)
        or re.fullmatch(r"[0-9a-f]{32}", run_id) is None
        or not isinstance(generation, str)
        or re.fullmatch(r"[0-9a-f]{32}", generation) is None
        or not isinstance(device, int)
        or isinstance(device, bool)
        or device < 0
        or not isinstance(inode, int)
        or isinstance(inode, bool)
        or inode < 0
        or (session_id is not None and not isinstance(session_id, str))
        or status
        not in ("running", "completed", "failed", "unknown", "rejected", "incomplete")
        or not isinstance(artifact_dir, str)
        or (status == "rejected" and artifact_dir != "")
        or (status != "rejected" and not artifact_dir)
        or (message is not None and not isinstance(message, str))
        or (
            exit_code is not None
            and (not isinstance(exit_code, int) or isinstance(exit_code, bool))
        )
        or (
            observed_session_id is not None and not isinstance(observed_session_id, str)
        )
        or (status == "running" and (message is not None or exit_code is not None))
        or (
            status == "rejected"
            and (
                session_id is not None
                or exit_code is not None
                or observed_session_id is not None
            )
        )
        or (status == "completed" and exit_code != 0)
        or (status == "failed" and (exit_code is None or exit_code == 0))
        or (status in ("unknown", "rejected", "incomplete") and not message)
        or (status in ("completed", "failed") and message is not None)
        or (observed_session_id is not None and status not in ("unknown", "incomplete"))
        or (observed_session_id is not None and observed_session_id == session_id)
    ):
        return None
    parsed: AttemptRecord = {
        "run_id": run_id,
        "generation": generation,
        "workspace_device": device,
        "workspace_inode": inode,
        "session_id": session_id,
        "status": status,
        "artifact_dir": artifact_dir,
    }
    if isinstance(message, str):
        parsed["message"] = message
    if isinstance(exit_code, int) and not isinstance(exit_code, bool):
        parsed["exit_code"] = exit_code
    if isinstance(observed_session_id, str):
        parsed["observed_session_id"] = observed_session_id
    return parsed


def _workspace(
    scope: sandbox.SandboxScope,
) -> tuple[Path, sandbox.DestinationIdentity]:
    if scope.destination_identity is None:
        raise ValueError("execution requires an existing sandbox directory")
    destination = scope.root / scope.name
    info = destination.lstat()
    if not stat.S_ISDIR(info.st_mode) or (
        info.st_dev,
        info.st_ino,
    ) != (scope.destination_identity.device, scope.destination_identity.inode):
        raise ValueError("sandbox workspace identity changed")
    return destination.resolve(strict=True), sandbox.DestinationIdentity(
        info.st_dev, info.st_ino
    )


def _canonical_session(session_id: str | None) -> str | None:
    if session_id is None:
        return None
    try:
        canonical = str(UUID(session_id))
    except ValueError as error:
        raise ValueError("session identity must be a UUID") from error
    if canonical != session_id.lower():
        raise ValueError("session identity must be a canonical UUID")
    return canonical


def _artifact_directory(scope: sandbox.SandboxScope, run_id: str) -> Path:
    root = scope.root / f".{scope.name}.runs"
    root.mkdir(mode=0o700, exist_ok=True)
    info = root.lstat()
    if (
        not stat.S_ISDIR(info.st_mode)
        or info.st_uid != os.getuid()
        or stat.S_IMODE(info.st_mode) != 0o700
    ):
        raise ValueError("unsafe private execution artifact root")
    directory = root / run_id
    directory.mkdir(mode=0o700)
    info = directory.lstat()
    if (
        not stat.S_ISDIR(info.st_mode)
        or info.st_uid != os.getuid()
        or stat.S_IMODE(info.st_mode) != 0o700
    ):
        raise ValueError("unsafe private execution artifact directory")
    return directory


def _artifact_path(scope: sandbox.SandboxScope, run_id: str) -> Path:
    return scope.root / f".{scope.name}.runs" / run_id


def _evidence_matches(
    evidence: StoppageEvidence,
    *,
    attempt: AttemptRecord,
    workspace: sandbox.DestinationIdentity,
) -> bool:
    return (
        evidence.run_id == attempt["run_id"]
        and evidence.generation == attempt["generation"]
        and evidence.workspace == workspace
        and bool(evidence.supervisor_id)
        and evidence.proof == "contained-tree-empty"
    )


def _pending_attempts(state: ExecutionState) -> Sequence[AttemptRecord]:
    return tuple(
        item for item in state["attempts"] if item["status"] in ("running", "unknown")
    )


def _save(
    scope: sandbox.SandboxScope,
    state: ExecutionState,
) -> sandbox.SandboxScope:
    changes: sandbox.SandboxExtensions = {
        "execution": cast(sandbox.JsonValue, state),
        "cleanup_disposition": None,
    }
    return sandbox.update_marker(scope, changes)


def _reject_existing(
    scope: sandbox.SandboxScope,
    state: ExecutionState | None,
    message: str,
) -> sandbox.SandboxScope:
    if state is None or scope.record is None:
        return scope
    identity = scope.record.owned
    workspace = sandbox.DestinationIdentity(
        identity["destination_device"], identity["destination_inode"]
    )
    return _save(scope, _rejected_attempt(scope, state, workspace, message))


def _unknown_attempt(
    scope: sandbox.SandboxScope,
    state: ExecutionState,
    attempt: AttemptRecord,
    reason: str,
    exit_code: int | None,
) -> AttemptResult:
    attempt["status"] = "unknown"
    attempt["message"] = reason
    if exit_code is not None:
        attempt["exit_code"] = exit_code
    _save(scope, state)
    session_id = attempt.get("observed_session_id", attempt["session_id"])
    return AttemptResult(attempt["run_id"], "unknown", session_id, exit_code)


def _record_supervisor_result(
    scope: sandbox.SandboxScope,
    state: ExecutionState,
    attempt: AttemptRecord,
    result: ProcessResult,
    requested_session: str | None,
    workspace: sandbox.DestinationIdentity,
) -> AttemptResult:
    if result.session_id is not None:
        try:
            observed_session = _canonical_session(result.session_id)
        except ValueError as error:
            return _unknown_attempt(
                scope,
                state,
                attempt,
                str(error),
                result.exit_code,
            )
        if requested_session is not None and observed_session != requested_session:
            attempt["observed_session_id"] = observed_session or ""
            return _unknown_attempt(
                scope,
                state,
                attempt,
                "supervisor returned a different session identity",
                result.exit_code,
            )
        attempt["session_id"] = observed_session
    if result.exit_code is not None:
        attempt["exit_code"] = result.exit_code
    if (
        result.exit_code is None
        or result.stoppage is None
        or not _evidence_matches(result.stoppage, attempt=attempt, workspace=workspace)
    ):
        return _unknown_attempt(
            scope,
            state,
            attempt,
            "complete process-tree stoppage was not established",
            result.exit_code,
        )
    elif result.exit_code == 0:
        attempt["status"] = "completed"
        status = "completed"
    else:
        attempt["status"] = "failed"
        status = "failed"
    _save(scope, state)
    return AttemptResult(
        attempt["run_id"], status, attempt["session_id"], result.exit_code
    )


def _check_existing_attempts(
    scope: sandbox.SandboxScope,
    state: ExecutionState | None,
    binding: WorkBinding,
    mode: Literal["initial", "resume"],
    session_id: str | None,
    workspace: sandbox.DestinationIdentity,
) -> AttemptResult | None:
    if mode not in ("initial", "resume"):
        _reject_existing(scope, state, "invalid execution mode")
        raise ValueError("execution mode must be initial or resume")
    if state is None:
        if mode == "resume":
            raise ValueError("cannot resume before initial Work and owner binding")
        return None
    if state["binding"] != binding:
        _reject_existing(scope, state, "Work or owner mismatch")
        raise ValueError("Evaluation Work or owner does not match the binding")
    if _pending_attempts(state):
        _reject_existing(scope, state, "recovery required")
        raise ValueError("an execution attempt requires host-side recovery")
    if mode == "initial" and not state["attempts"]:
        return None
    prior_sessions = {
        item["session_id"]
        for item in state["attempts"]
        if item["session_id"] is not None
    }
    if mode == "resume" and session_id is not None and prior_sessions == {session_id}:
        return None
    rejected = _rejected_attempt(scope, state, workspace, "resume identity mismatch")
    _save(scope, rejected)
    return AttemptResult(rejected["attempts"][-1]["run_id"], "rejected", None, None)


def _validated_request(
    scope: sandbox.SandboxScope,
    source_repository: Path,
    work: str,
    owner_id: str,
    session_id: str | None,
    invocation: Invocation,
) -> tuple[WorkBinding, str | None, sandbox.DestinationIdentity]:
    binding = _binding(scope, source_repository, work, owner_id)
    requested_session = _canonical_session(session_id)
    destination, workspace = _workspace(scope)
    cwd = invocation.cwd.resolve(strict=True)
    if not cwd.is_dir() or (cwd != destination and not cwd.is_relative_to(destination)):
        raise ValueError("execution directory must be inside the sandbox")
    if not invocation.command or any(
        not isinstance(part, str) or not part for part in invocation.command
    ):
        raise ValueError("execution command is empty or malformed")
    if not math.isfinite(invocation.timeout_seconds) or invocation.timeout_seconds <= 0:
        raise ValueError("execution requires a finite positive timeout")
    return binding, requested_session, workspace


def _begin_attempt(
    scope: sandbox.SandboxScope,
    state: ExecutionState | None,
    binding: WorkBinding,
    generation: str,
    workspace: sandbox.DestinationIdentity,
    session_id: str | None,
) -> tuple[sandbox.SandboxScope, ExecutionState, AttemptRecord, Path]:
    run_id = secrets.token_hex(16)
    artifact_dir = _artifact_path(scope, run_id)
    attempt: AttemptRecord = {
        "run_id": run_id,
        "generation": generation,
        "workspace_device": workspace.device,
        "workspace_inode": workspace.inode,
        "session_id": session_id,
        "status": "running",
        "artifact_dir": str(artifact_dir),
    }
    state = state or {"binding": binding, "attempts": []}
    state = {"binding": state["binding"], "attempts": [*state["attempts"], attempt]}
    scope = _save(scope, state)
    try:
        artifact_dir = _artifact_directory(scope, run_id)
    except (OSError, ValueError) as error:
        attempt["status"] = "rejected"
        attempt["artifact_dir"] = ""
        attempt["message"] = f"artifact setup failed: {error}"
        _save(scope, state)
        raise
    return scope, state, attempt, artifact_dir


def run_attempt(
    scope: sandbox.SandboxScope,
    *,
    source_repository: Path,
    work: str,
    owner_id: str,
    mode: Literal["initial", "resume"],
    session_id: str | None,
    invocation: Invocation,
    supervisor: ProcessSupervisor,
) -> AttemptResult:
    """Persist a bound attempt before launch and fail closed on uncertain exit.

    Returns:
        The retained attempt status. Unknown means no bound stoppage proof exists.

    Raises:
        ValueError: If the source Work or host ownership is unsafe or mismatched.
        OSError: If durable marker or artifact setup fails.
    """
    scope = sandbox.refresh_scope(scope)
    if scope.generation is None or scope.record is None:
        raise ValueError("execution requires a reserved sandbox")
    _workspace(scope)
    generation = scope.generation
    scope = sandbox.update_marker(scope, {"cleanup_disposition": None})
    state = read_execution_state(scope)
    try:
        binding, requested_session, workspace = _validated_request(
            scope, source_repository, work, owner_id, session_id, invocation
        )
        if mode == "initial" and requested_session is not None:
            raise ValueError("initial execution cannot supply a session UUID")
    except (OSError, ValueError) as error:
        _reject_existing(scope, state, f"invalid execution request: {error}")
        raise
    rejected = _check_existing_attempts(
        scope, state, binding, mode, requested_session, workspace
    )
    if rejected is not None:
        return rejected
    scope, state, attempt, artifact_dir = _begin_attempt(
        scope, state, binding, generation, workspace, requested_session
    )

    try:
        result = supervisor.run(
            invocation,
            run_id=attempt["run_id"],
            generation=generation,
            workspace=workspace,
            artifact_dir=artifact_dir,
        )
    except Exception as error:
        return _unknown_attempt(
            scope,
            state,
            attempt,
            f"supervisor outcome uncertain: {error}",
            None,
        )
    return _record_supervisor_result(
        scope, state, attempt, result, requested_session, workspace
    )


def _rejected_attempt(
    scope: sandbox.SandboxScope,
    state: ExecutionState,
    workspace: sandbox.DestinationIdentity,
    message: str,
) -> ExecutionState:
    if scope.generation is None:
        raise ValueError("rejected attempt requires a reserved sandbox")
    rejected: AttemptRecord = {
        "run_id": secrets.token_hex(16),
        "generation": scope.generation,
        "workspace_device": workspace.device,
        "workspace_inode": workspace.inode,
        "session_id": None,
        "status": "rejected",
        "artifact_dir": "",
        "message": message,
    }
    return {"binding": state["binding"], "attempts": [*state["attempts"], rejected]}


def _validate_artifact_directory(
    scope: sandbox.SandboxScope,
    attempt_path: Path,
    evidence_path: Path,
) -> None:
    root = scope.root.resolve(strict=True)
    expected = Path(os.path.abspath(attempt_path))
    supplied = Path(os.path.abspath(evidence_path))
    if (
        supplied != expected
        or expected.parent != scope.root / f".{scope.name}.runs"
        or not expected.is_relative_to(root)
    ):
        raise ValueError("preserved artifact directory does not match the attempt")
    run_root_info = expected.parent.lstat()
    artifact_info = expected.lstat()
    if any(
        not stat.S_ISDIR(info.st_mode)
        or info.st_uid != os.getuid()
        or stat.S_IMODE(info.st_mode) != 0o700
        for info in (run_root_info, artifact_info)
    ):
        raise ValueError("preserved artifact directory is unsafe")


def recover_attempt(
    scope: sandbox.SandboxScope,
    run_id: str,
    evidence: RecoveryEvidence,
) -> None:
    """Resolve an interrupted attempt from identity-bound host evidence.

    Evidence must come from a trusted host recovery authority after process-tree
    stoppage and artifact preservation; a PID or boolean alone is insufficient.

    Raises:
        ValueError: If identity, stoppage, or retained artifact evidence differs.
    """
    scope = sandbox.refresh_scope(scope)
    if scope.record is None or scope.generation is None:
        raise ValueError("recovery requires a reserved sandbox")
    _workspace(scope)
    generation = scope.generation
    scope = sandbox.update_marker(scope, {"cleanup_disposition": None})
    state = read_execution_state(scope)
    if state is None:
        raise ValueError("sandbox has no execution record to recover")
    attempt = next(
        (item for item in state["attempts"] if item["run_id"] == run_id), None
    )
    if attempt is None or attempt["status"] not in ("running", "unknown"):
        raise ValueError("execution attempt is not recoverable")
    workspace = sandbox.DestinationIdentity(
        attempt["workspace_device"], attempt["workspace_inode"]
    )
    current_workspace = _workspace(scope)[1]
    if (
        attempt["generation"] != generation
        or workspace != current_workspace
        or not _evidence_matches(
            evidence.stoppage, attempt=attempt, workspace=workspace
        )
    ):
        raise ValueError("recovery evidence does not match the attempt")
    _validate_artifact_directory(
        scope, Path(attempt["artifact_dir"]), evidence.artifact_dir
    )
    attempt["status"] = "incomplete"
    attempt["message"] = "host recovery established stoppage and preservation"
    _save(scope, state)
