# SPDX-License-Identifier: Apache-2.0
"""Typed asynchronous evidence persistence port and filesystem adapter.

The adapter owns event ordering and identity forwarding. Filesystem leaves
publish immutable artifacts and append durable lifecycle observations.
"""

import asyncio
from collections.abc import Callable, Coroutine
from functools import partial, wraps
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Protocol

from pydantic import BaseModel

from script.eval.model import (
    AttemptEvidence,
    AttemptNumber,
    AttemptOutcomeKind,
    AttemptRecord,
    CallId,
    ControlFlow,
    FrozenPlan,
    PreparedEvidence,
    QuotaProbeEvidence,
    QuotaProbeLifecycleInput,
    QuotaProbeRecord,
    QuotaProbeSettled,
    QuotaTelemetryEvent,
    RetryAssessment,
    RunId,
    RunRecord,
    WaitEvent,
)
from script.process_supervisor import (
    AttemptCancelled,
    AttemptFailureEvidence,
    AttemptObservation,
    Completed,
    InfrastructureFailure,
    OutputLimitExceeded,
    TimedOut,
)


class EvidenceStore(Protocol):
    """Exclusive run setup and append-only evidence boundary.

    Callers must complete one successful ``create`` before recording. The
    adapter rejects evidence operations before preparation and rejects a
    second successful preparation attempt. Each submitted operation remains
    owned through lock waiting, projection, and append under cooperative caller
    cancellation. The caller receives ``CancelledError`` only after the whole
    operation settles; a concurrent operation failure remains its cause.

    The adapter uses an in-memory lock for this instance on its event loop.
    It provides no coordination with another adapter or process. A coroutine
    that has not started is not submitted. The runner must retain and await all
    submitted evidence operations during shutdown. The public
    ``create_evidence_store`` factory binds unfinished default leaves; the
    adapter constructor requires every leaf explicitly.
    """

    async def create(
        self, output_directory: Path, plan: FrozenPlan, /
    ) -> PreparedEvidence:
        """Create exclusive evidence storage before any process can launch."""

    async def record_attempt(
        self,
        run_id: RunId,
        call_id: CallId,
        position: int,
        attempt_number: AttemptNumber,
        evidence: AttemptEvidence,
        retry_assessment: RetryAssessment | None,
        /,
    ) -> AttemptRecord:
        """Project and append one classified process outcome."""

    async def record_wait_event(self, event: WaitEvent, /) -> None:
        """Append one wait lifecycle observation."""

    async def record_quota_probe_event(
        self, event: QuotaProbeLifecycleInput, /
    ) -> None:
        """Append a scheduled, started, or prelaunch-cancelled probe event."""

    async def record_quota_probe_settled(
        self, evidence: QuotaProbeEvidence, /
    ) -> QuotaProbeSettled:
        """Project process evidence and append its settled probe record."""

    async def record_quota_telemetry(self, event: QuotaTelemetryEvent, /) -> None:
        """Append passive provider-neutral quota telemetry."""

    async def finalize(self, record: RunRecord, /) -> None:
        """Persist final accounting; a failure leaves evidence incomplete."""


type CreateEvidence = Callable[[Path, FrozenPlan], PreparedEvidence]
type ProjectAttempt = Callable[
    [
        PreparedEvidence,
        RunId,
        CallId,
        int,
        AttemptNumber,
        AttemptEvidence,
        RetryAssessment | None,
    ],
    AttemptRecord,
]
type AppendAttempt = Callable[[PreparedEvidence, AttemptRecord], None]
type AppendWaitEvent = Callable[[PreparedEvidence, WaitEvent], None]
type AppendProbeEvent = Callable[[PreparedEvidence, QuotaProbeLifecycleInput], None]
type ProjectSettledProbe = Callable[
    [PreparedEvidence, QuotaProbeEvidence], QuotaProbeSettled
]
type AppendSettledProbe = Callable[[PreparedEvidence, QuotaProbeSettled], None]
type AppendQuotaTelemetry = Callable[[PreparedEvidence, QuotaTelemetryEvent], None]
type FinalizeEvidence = Callable[[PreparedEvidence, RunRecord], None]


def _retain_operation[**P, R](
    operation: Callable[P, Coroutine[None, None, R]],
) -> Callable[P, Coroutine[None, None, R]]:
    """Keep lock waiting and every effect owned after public submission.

    Returns:
        A coroutine preserving the decorated operation's parameters and result.
    """

    @wraps(operation)
    async def run(*args: P.args, **kwargs: P.kwargs) -> R:
        task = asyncio.create_task(operation(*args, **kwargs))
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError as cancellation:
            await _settle_started_task(task)
            failure = _task_exception(task)
            if failure is not None:
                cancellation.add_note(f"Evidence operation also failed: {failure!r}")
                raise cancellation from failure
            raise cancellation

    return run


class EvidenceStoreAdapter:
    """Compose ordered evidence operations around unfinished typed leaves.

    Every submitted operation is serialized and retained through settlement
    under cooperative caller cancellation. Injected synchronous leaves run in
    worker threads. The leaves define the storage and projection boundary, so
    their responsibilities do not depend on a particular storage backend.

    Args:
        create_evidence: Exclusively set up a run's evidence area and persist
            its frozen plan and staged instructions before dispatch.
        project_attempt: Write artifacts for one process attempt and build its
            serializable ``AttemptRecord``; it does not append that record.
        append_attempt: Durably persist a projected attempt record.
        append_wait_event: Persist one scalar wait lifecycle transition.
        append_probe_event: Persist one scalar probe lifecycle transition.
        project_settled_probe: Write settled probe artifacts and build its
            serializable process projection and quota assessment.
        append_settled_probe: Durably persist a projected settled probe.
        append_quota_telemetry: Durably persist one passive telemetry event.
        finalize_evidence: Persist final run accounting.

    Each leaf is responsible for fulfilling its described setup, artifact,
    projection, or persistence obligation. This boundary permits storage
    implementations such as object storage without promising that any such
    backend is implemented here.

    Example:
        ``create_evidence_store(project_attempt=fake_project)`` can be
        exercised without files by supplying typed in-memory leaves.
    """

    def __init__(
        self,
        *,
        create_evidence: CreateEvidence,
        project_attempt: ProjectAttempt,
        append_attempt: AppendAttempt,
        append_wait_event: AppendWaitEvent,
        append_probe_event: AppendProbeEvent,
        project_settled_probe: ProjectSettledProbe,
        append_settled_probe: AppendSettledProbe,
        append_quota_telemetry: AppendQuotaTelemetry,
        finalize_evidence: FinalizeEvidence,
    ) -> None:
        """Store synchronous leaves used by this async boundary."""
        self._create_evidence = create_evidence
        self._project_attempt = project_attempt
        self._append_attempt = append_attempt
        self._append_wait_event = append_wait_event
        self._append_probe_event = append_probe_event
        self._project_settled_probe = project_settled_probe
        self._append_settled_probe = append_settled_probe
        self._append_quota_telemetry = append_quota_telemetry
        self._finalize_evidence = finalize_evidence
        self._prepared: PreparedEvidence | None = None
        self._lock = asyncio.Lock()

    @_retain_operation
    async def create(
        self, output_directory: Path, plan: FrozenPlan, /
    ) -> PreparedEvidence:
        """Exclusively prepare evidence before dispatch by delegating the leaf.

        Returns:
            The paths to the prepared evidence area and staged instructions.

        Raises:
            RuntimeError: Evidence storage has already been bound for this run.
        """
        async with self._lock:
            if self._prepared is not None:
                raise RuntimeError("evidence storage is already prepared for this run")
            prepared = await _invoke_leaf(
                partial(self._create_evidence, output_directory, plan)
            )
            self._bind_prepared(prepared)
            return prepared

    @_retain_operation
    async def record_attempt(
        self,
        run_id: RunId,
        call_id: CallId,
        position: int,
        attempt_number: AttemptNumber,
        evidence: AttemptEvidence,
        retry_assessment: RetryAssessment | None,
        /,
    ) -> AttemptRecord:
        """Project then append one attempt, returning only after persistence.

        The classifier is runner-owned; this adapter preserves its supplied
        assessment and never interprets output content.

        Returns:
            The projected record after its append operation succeeds.
        """
        async with self._lock:
            prepared = self._require_prepared()
            record = await _invoke_leaf(
                partial(
                    self._project_attempt,
                    prepared,
                    run_id,
                    call_id,
                    position,
                    attempt_number,
                    evidence,
                    retry_assessment,
                ),
            )
            await _invoke_leaf(partial(self._append_attempt, prepared, record))
            return record

    @_retain_operation
    async def record_wait_event(self, event: WaitEvent, /) -> None:
        """Append each wait transition before policy advances."""
        async with self._lock:
            await _invoke_leaf(
                partial(self._append_wait_event, self._require_prepared(), event)
            )

    @_retain_operation
    async def record_quota_probe_event(
        self, event: QuotaProbeLifecycleInput, /
    ) -> None:
        """Append a scalar probe transition without inventing process evidence."""
        async with self._lock:
            await _invoke_leaf(
                partial(self._append_probe_event, self._require_prepared(), event)
            )

    @_retain_operation
    async def record_quota_probe_settled(
        self, evidence: QuotaProbeEvidence, /
    ) -> QuotaProbeSettled:
        """Project and append settled probe evidence before quota resumption.

        Returns:
            The shared process projection and quota assessment after append.
        """
        async with self._lock:
            prepared = self._require_prepared()
            settled = await _invoke_leaf(
                partial(self._project_settled_probe, prepared, evidence)
            )
            await _invoke_leaf(partial(self._append_settled_probe, prepared, settled))
            return settled

    @_retain_operation
    async def record_quota_telemetry(self, event: QuotaTelemetryEvent, /) -> None:
        """Append passive telemetry as a separate associated observation."""
        async with self._lock:
            await _invoke_leaf(
                partial(self._append_quota_telemetry, self._require_prepared(), event)
            )

    @_retain_operation
    async def finalize(self, record: RunRecord, /) -> None:
        """Persist truthful final accounting through the supplied leaf."""
        async with self._lock:
            await _invoke_leaf(
                partial(self._finalize_evidence, self._require_prepared(), record)
            )

    def _require_prepared(self) -> PreparedEvidence:
        """Return this run's storage handle or reject pre-setup evidence calls.

        Raises:
            RuntimeError: Successful run preparation has not completed.
        """
        if self._prepared is None:
            raise RuntimeError("evidence storage must be prepared before recording")
        return self._prepared

    def _bind_prepared(self, prepared: PreparedEvidence) -> None:
        """Bind the prepared handle before releasing create-operation ownership."""
        self._prepared = prepared


def create_evidence_store(
    *,
    create_evidence: CreateEvidence | None = None,
    project_attempt: ProjectAttempt | None = None,
    append_attempt: AppendAttempt | None = None,
    append_wait_event: AppendWaitEvent | None = None,
    append_probe_event: AppendProbeEvent | None = None,
    project_settled_probe: ProjectSettledProbe | None = None,
    append_settled_probe: AppendSettledProbe | None = None,
    append_quota_telemetry: AppendQuotaTelemetry | None = None,
    finalize_evidence: FinalizeEvidence | None = None,
) -> EvidenceStoreAdapter:
    """Compose the adapter with unfinished default leaves or supplied test ports.

    Returns:
        An adapter with all nine leaf dependencies explicitly bound.
    """
    return EvidenceStoreAdapter(
        create_evidence=_create_evidence
        if create_evidence is None
        else create_evidence,
        project_attempt=_project_attempt
        if project_attempt is None
        else project_attempt,
        append_attempt=_append_attempt if append_attempt is None else append_attempt,
        append_wait_event=_append_wait_event
        if append_wait_event is None
        else append_wait_event,
        append_probe_event=_append_probe_event
        if append_probe_event is None
        else append_probe_event,
        project_settled_probe=(
            _project_settled_probe
            if project_settled_probe is None
            else project_settled_probe
        ),
        append_settled_probe=(
            _append_settled_probe
            if append_settled_probe is None
            else append_settled_probe
        ),
        append_quota_telemetry=(
            _append_quota_telemetry
            if append_quota_telemetry is None
            else append_quota_telemetry
        ),
        finalize_evidence=(
            _finalize_evidence if finalize_evidence is None else finalize_evidence
        ),
    )


async def _invoke_leaf[Result](
    leaf: Callable[[], Result],
) -> Result:
    """Run one synchronous leaf off-loop within its owned operation.

    Returns:
        The leaf result.
    """
    return await asyncio.to_thread(leaf)


async def _settle_started_task[Result](
    task: asyncio.Task[Result],
) -> None:
    """Wait for task settlement while consuming repeated owner cancellation."""
    while not task.done():
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            continue
        except BaseException:
            break


def _task_exception[Result](task: asyncio.Task[Result]) -> BaseException | None:
    """Return a settled task's exception without raising it."""
    try:
        return task.exception()
    except BaseException as failure:
        return failure


def _create_evidence(output_directory: Path, plan: FrozenPlan, /) -> PreparedEvidence:
    """Create a fresh run area and persist frozen inputs.

    Returns:
        Absolute paths to the run area, plan, and optional instructions.

    Raises:
        FileExistsError: The requested destination already exists.
        OSError: The ignore status or filesystem operation cannot be established.
        ValueError: An in-repository destination is not Git-ignored.
    """
    if os.path.lexists(output_directory):
        raise FileExistsError(f"evidence output already exists: {output_directory}")
    destination = output_directory.expanduser().resolve()
    repository = plan.repository_root.resolve()
    try:
        relative = destination.relative_to(repository)
    except ValueError:
        relative = None
    if relative is not None:
        result = subprocess.run(
            ["git", "check-ignore", "--quiet", "--no-index", "--", relative.as_posix()],
            cwd=repository,
            capture_output=True,
            check=False,
        )
        if result.returncode == 1:
            raise ValueError(
                "evidence output inside the context repository must be Git-ignored"
            )
        if result.returncode != 0:
            raise OSError(
                f"could not verify output ignore status (git exit {result.returncode})"
            )
    destination.mkdir(parents=True, exist_ok=False)
    _fsync_directory(destination.parent)
    plan_path = destination / "plan.json"
    _write_new_file(plan_path, _json_bytes(plan))
    instruction_path = None
    if plan.instructions_file is not None:
        instruction_path = destination / "instructions.bin"
        _write_new_file(instruction_path, plan.instructions_file.content)
    return PreparedEvidence(destination, plan_path, instruction_path)


def _project_attempt(
    prepared: PreparedEvidence,
    run_id: RunId,
    call_id: CallId,
    position: int,
    attempt_number: AttemptNumber,
    evidence: AttemptEvidence,
    retry_assessment: RetryAssessment | None,
    /,
) -> AttemptRecord:
    """Publish raw stream prefixes and project the supervisor facts.

    Returns:
        The immutable metadata projection for this attempt.
    """
    base = (
        prepared.output_directory / "attempts" / call_id / f"attempt-{attempt_number}"
    )
    stdout, stderr = _publish_streams(base, evidence)
    return AttemptRecord.model_validate(
        _process_record(evidence)
        | {
            "run_id": run_id,
            "call_id": call_id,
            "position": position,
            "attempt_number": attempt_number,
            "stdout_artifact": stdout,
            "stderr_artifact": stderr,
            "retry_assessment": retry_assessment,
        }
    )


def _append_attempt(prepared: PreparedEvidence, record: AttemptRecord, /) -> None:
    """Atomically publish one immutable attempt record."""
    _write_new_file(
        prepared.output_directory
        / "attempts"
        / record.call_id
        / f"attempt-{record.attempt_number}.json",
        _json_bytes(record),
    )


def _append_wait_event(prepared: PreparedEvidence, event: WaitEvent, /) -> None:
    """Append a durable wait event."""
    _append_event(prepared, "wait", event)


def _append_probe_event(
    prepared: PreparedEvidence, event: QuotaProbeLifecycleInput, /
) -> None:
    """Append a durable probe lifecycle event."""
    _append_event(prepared, "probe", event)


def _project_settled_probe(
    prepared: PreparedEvidence, evidence: QuotaProbeEvidence, /
) -> QuotaProbeSettled:
    """Project probe process facts through the shared outcome projection.

    Returns:
        The settled quota probe with raw process artifact references.
    """
    probe_id = evidence.request.schedule.probe_id
    stdout, stderr = _publish_streams(
        prepared.output_directory / "probes" / str(probe_id), evidence.process
    )
    record = QuotaProbeRecord.model_validate(
        _process_record(evidence.process)
        | {
            "stdout_artifact": stdout,
            "stderr_artifact": stderr,
            "request": evidence.request,
            "quota_state": evidence.quota_state,
            "observation": evidence.observation,
            "classification_basis": evidence.classification_basis,
        }
    )
    return QuotaProbeSettled(kind="settled", record=record)


def _append_settled_probe(
    prepared: PreparedEvidence, event: QuotaProbeSettled, /
) -> None:
    """Append the settled probe record to the event ledger."""
    _append_event(prepared, "probe", event)


def _append_quota_telemetry(
    prepared: PreparedEvidence, event: QuotaTelemetryEvent, /
) -> None:
    """Append passive quota telemetry to the event ledger."""
    _append_event(prepared, "quota_telemetry", event)


def _finalize_evidence(prepared: PreparedEvidence, record: RunRecord, /) -> None:
    """Write final accounting without replacing the original plan."""
    _write_new_file(prepared.output_directory / "run.json", _json_bytes(record))


def _process_record(evidence: AttemptEvidence, /) -> dict[str, object]:
    """Project all supervisor outcomes without classifying captured content.

    Returns:
        Fields accepted by the shared persisted process record.
    """
    outcome = evidence.outcome
    observation, exit_status, kind, termination = _outcome_projection(
        outcome, evidence.control_flow
    )
    cleanup = (
        None
        if observation is None
        else {
            "process": observation.cleanup.process,
            "signals": tuple(
                {
                    "signal": item.signal,
                    "outcome": item.outcome,
                    "diagnostic": item.diagnostic,
                }
                for item in observation.cleanup.signals
            ),
            "direct_wait": observation.cleanup.direct_wait,
            "wait_diagnostic": observation.cleanup.wait_diagnostic,
        }
    )
    request = evidence.request
    return {
        "control_flow": evidence.control_flow,
        "outcome_kind": kind,
        "started_at_utc": evidence.started_at_utc,
        "ended_at_utc": evidence.ended_at_utc,
        "argv": request.argv,
        "cwd": str(request.cwd),
        "timeout_seconds": request.timeout_seconds,
        "cleanup_timeout_seconds": request.cleanup_timeout_seconds,
        "grace_seconds": request.grace_seconds,
        "output_limit_bytes": request.output_limit_bytes,
        "elapsed_seconds": None if observation is None else observation.elapsed_seconds,
        "elapsed_basis": "unavailable"
        if observation is None
        else "supervisor_observation",
        "exit_status": exit_status,
        "termination_reason": termination,
        "cleanup": cleanup,
        "stdout_artifact": None,
        "stderr_artifact": None,
        "usage_telemetry": evidence.usage_telemetry,
        "error_type": evidence.error_type,
        "diagnostic": evidence.diagnostic,
    }


def _outcome_projection(
    outcome: object, control_flow: ControlFlow
) -> tuple[AttemptObservation | None, int | None, AttemptOutcomeKind, str | None]:
    """Return observation, status, outcome kind, and termination label.

    Raises:
        TypeError: The supervisor returned an unsupported outcome value.
    """
    match outcome:
        case AttemptCancelled() as cancelled:
            return (
                cancelled.observation,
                cancelled.exit_status,
                "cancelled",
                "cancelled",
            )
        case AttemptFailureEvidence() as failure:
            return (
                failure.observation,
                failure.exit_status,
                "unexpected_exception",
                "exception",
            )
        case Completed() as completed:
            return completed.observation, completed.exit_status, "completed", "exited"
        case TimedOut() as timeout:
            return timeout.observation, timeout.exit_status, "timed_out", "timed_out"
        case OutputLimitExceeded() as overflow:
            return (
                overflow.observation,
                overflow.exit_status,
                "output_limit_exceeded",
                "output_limit_exceeded",
            )
        case InfrastructureFailure() as failure:
            return (
                failure.observation,
                failure.exit_status,
                "infrastructure_failure",
                "infrastructure_failure",
            )
        case None:
            kind = (
                "unexpected_exception" if control_flow == "raised" else "no_observation"
            )
            termination = "exception" if control_flow == "raised" else None
            return None, None, kind, termination
        case _:
            raise TypeError(f"unsupported supervisor outcome: {type(outcome).__name__}")


def _publish_streams(
    base: Path, evidence: AttemptEvidence, /
) -> tuple[str | None, str | None]:
    """Publish exact observed streams, including empty byte strings.

    Returns:
        Absolute artifact paths, or ``None`` for unavailable output.
    """
    outcome = evidence.outcome
    observation = (
        outcome.observation
        if isinstance(
            outcome,
            (
                AttemptCancelled,
                AttemptFailureEvidence,
                Completed,
                TimedOut,
                OutputLimitExceeded,
                InfrastructureFailure,
            ),
        )
        else None
    )
    if observation is None or observation.output is None:
        return None, None
    stdout, stderr = base.with_suffix(".stdout"), base.with_suffix(".stderr")
    _write_new_file(stdout, observation.output.stdout)
    _write_new_file(stderr, observation.output.stderr)
    return str(stdout.resolve()), str(stderr.resolve())


def _json_bytes(value: BaseModel) -> bytes:
    """Encode validated metadata as UTF-8 JSON.

    Returns:
        A newline-terminated JSON document.
    """
    return (value.model_dump_json(indent=2) + "\n").encode("utf-8")


def _write_new_file(path: Path, content: bytes, /) -> None:
    """Fsync a temporary file and atomically publish without replacement."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=".evidence-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
        temporary.unlink()
        _fsync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def _append_event(prepared: PreparedEvidence, kind: str, event: BaseModel, /) -> None:
    """Append one fsynced JSON Lines event."""
    path = prepared.output_directory / "events.jsonl"
    encoded = (
        json.dumps(
            {"kind": kind, "event": json.loads(_json_bytes(event))},
            separators=(",", ":"),
        ).encode()
        + b"\n"
    )
    fd = os.open(path, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o600)
    try:
        remaining = memoryview(encoded)
        while remaining:
            written = os.write(fd, remaining)
            remaining = remaining[written:]
        os.fsync(fd)
    finally:
        os.close(fd)
    _fsync_directory(path.parent)


def _fsync_directory(path: Path, /) -> None:
    """Persist directory-entry updates where directory fsync is available."""
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
