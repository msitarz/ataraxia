# SPDX-License-Identifier: Apache-2.0
"""Typed asynchronous evidence persistence port and composition adapter.

The adapter owns event ordering and identity forwarding. Storage, projection,
and artifact-writing leaves remain explicit injection points until implemented.
"""

import asyncio
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import Protocol

from script.eval.model import (
    AttemptEvidence,
    AttemptNumber,
    AttemptRecord,
    CallId,
    FrozenPlan,
    PreparedEvidence,
    QuotaProbeEvidence,
    QuotaProbeLifecycleInput,
    QuotaProbeSettled,
    QuotaTelemetryEvent,
    RetryAssessment,
    RunId,
    RunRecord,
    WaitEvent,
)


class EvidenceStore(Protocol):
    """Exclusive run setup and append-only evidence boundary.

    Callers must complete one successful ``create`` before recording. The
    adapter rejects evidence operations before preparation and rejects a
    second successful preparation attempt.
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


class EvidenceStoreAdapter:
    """Compose ordered evidence operations around unfinished typed leaves.

    Every operation is serialized. Injected synchronous leaves run in worker
    threads; a started leaf settles before cancellation releases the operation.

    Example:
        ``EvidenceStoreAdapter(project_attempt=fake_project, ...)`` can be
        exercised without files by supplying typed in-memory leaves.
    """

    def __init__(
        self,
        create_evidence: CreateEvidence | None = None,
        project_attempt: ProjectAttempt | None = None,
        append_attempt: AppendAttempt | None = None,
        append_wait_event: AppendWaitEvent | None = None,
        append_probe_event: AppendProbeEvent | None = None,
        project_settled_probe: ProjectSettledProbe | None = None,
        append_settled_probe: AppendSettledProbe | None = None,
        append_quota_telemetry: AppendQuotaTelemetry | None = None,
        finalize_evidence: FinalizeEvidence | None = None,
    ) -> None:
        """Store synchronous leaves used by this async boundary."""
        self._create_evidence = (
            _create_evidence if create_evidence is None else create_evidence
        )
        self._project_attempt = (
            _project_attempt if project_attempt is None else project_attempt
        )
        self._append_attempt = (
            _append_attempt if append_attempt is None else append_attempt
        )
        self._append_wait_event = (
            _append_wait_event if append_wait_event is None else append_wait_event
        )
        self._append_probe_event = (
            _append_probe_event if append_probe_event is None else append_probe_event
        )
        self._project_settled_probe = (
            _project_settled_probe
            if project_settled_probe is None
            else project_settled_probe
        )
        self._append_settled_probe = (
            _append_settled_probe
            if append_settled_probe is None
            else append_settled_probe
        )
        self._append_quota_telemetry = (
            _append_quota_telemetry
            if append_quota_telemetry is None
            else append_quota_telemetry
        )
        self._finalize_evidence = (
            _finalize_evidence if finalize_evidence is None else finalize_evidence
        )
        self._prepared: PreparedEvidence | None = None
        self._lock = asyncio.Lock()

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
            return await _invoke_leaf(
                partial(self._create_evidence, output_directory, plan),
                on_success=self._bind_prepared,
            )

    def _bind_prepared(self, prepared: PreparedEvidence) -> None:
        """Bind the prepared handle before releasing create-operation ownership."""
        self._prepared = prepared

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

    async def record_wait_event(self, event: WaitEvent, /) -> None:
        """Append each wait transition before policy advances."""
        async with self._lock:
            await _invoke_leaf(
                partial(self._append_wait_event, self._require_prepared(), event)
            )

    async def record_quota_probe_event(
        self, event: QuotaProbeLifecycleInput, /
    ) -> None:
        """Append a scalar probe transition without inventing process evidence."""
        async with self._lock:
            await _invoke_leaf(
                partial(self._append_probe_event, self._require_prepared(), event)
            )

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

    async def record_quota_telemetry(self, event: QuotaTelemetryEvent, /) -> None:
        """Append passive telemetry as a separate associated observation."""
        async with self._lock:
            await _invoke_leaf(
                partial(self._append_quota_telemetry, self._require_prepared(), event)
            )

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


async def _invoke_leaf[Result](
    leaf: Callable[[], Result],
    *,
    on_success: Callable[[Result], None] | None = None,
) -> Result:
    """Run a bound leaf off-loop and retain ownership through cancellation.

    Returns:
        The leaf result after successful settlement.

    Raises:
        asyncio.CancelledError: After a started leaf settles.
    """
    task = asyncio.create_task(asyncio.to_thread(leaf))
    try:
        result = await asyncio.shield(task)
    except asyncio.CancelledError as cancellation:
        await _settle_started_task(task)
        failure = _task_exception(task)
        if failure is not None:
            cancellation.add_note(f"Evidence leaf also failed: {failure!r}")
            raise cancellation from failure
        result = _task_result(task)
        if on_success is not None:
            on_success(result)
        raise cancellation
    if on_success is not None:
        on_success(result)
    return result


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


def _task_exception(task: asyncio.Task[object]) -> BaseException | None:
    """Return a settled task's exception without raising it."""
    try:
        return task.exception()
    except BaseException as failure:
        return failure


def _task_result[Result](task: asyncio.Task[Result]) -> Result:
    """Return the result of a task already confirmed to have succeeded."""
    return task.result()


def _create_evidence(output_directory: Path, plan: FrozenPlan, /) -> PreparedEvidence:
    """Exclusive creation and pre-dispatch plan persistence are unfinished."""
    raise NotImplementedError("exclusive evidence creation is not implemented")


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
    """Artifact writing and shared process projection are unfinished."""
    raise NotImplementedError("attempt evidence projection is not implemented")


def _append_attempt(prepared: PreparedEvidence, record: AttemptRecord, /) -> None:
    """Append-only attempt record persistence is unfinished."""
    raise NotImplementedError("attempt record persistence is not implemented")


def _append_wait_event(prepared: PreparedEvidence, event: WaitEvent, /) -> None:
    """Append-only wait event persistence is unfinished."""
    raise NotImplementedError("wait event persistence is not implemented")


def _append_probe_event(
    prepared: PreparedEvidence, event: QuotaProbeLifecycleInput, /
) -> None:
    """Append-only probe lifecycle persistence is unfinished."""
    raise NotImplementedError("probe event persistence is not implemented")


def _project_settled_probe(
    prepared: PreparedEvidence, evidence: QuotaProbeEvidence, /
) -> QuotaProbeSettled:
    """Probe artifact writing and process projection are unfinished."""
    raise NotImplementedError("settled probe projection is not implemented")


def _append_settled_probe(
    prepared: PreparedEvidence, event: QuotaProbeSettled, /
) -> None:
    """Append-only settled probe persistence is unfinished."""
    raise NotImplementedError("settled probe persistence is not implemented")


def _append_quota_telemetry(
    prepared: PreparedEvidence, event: QuotaTelemetryEvent, /
) -> None:
    """Append-only passive telemetry persistence is unfinished."""
    raise NotImplementedError("quota telemetry persistence is not implemented")


def _finalize_evidence(prepared: PreparedEvidence, record: RunRecord, /) -> None:
    """Final run accounting persistence is unfinished."""
    raise NotImplementedError("final evidence persistence is not implemented")
