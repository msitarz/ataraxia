# SPDX-License-Identifier: Apache-2.0
"""Typed evidence persistence port and synchronous composition adapter.

The adapter owns event ordering and identity forwarding. Storage, projection,
and artifact-writing leaves remain explicit injection points until implemented.
"""

from collections.abc import Callable
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
    """Exclusive run setup and append-only evidence boundary."""

    def create(self, output_directory: Path, plan: FrozenPlan, /) -> PreparedEvidence:
        """Create exclusive evidence storage before any process can launch."""

    def record_attempt(
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

    def record_wait_event(self, event: WaitEvent, /) -> None:
        """Append one wait lifecycle observation."""

    def record_quota_probe_event(self, event: QuotaProbeLifecycleInput, /) -> None:
        """Append a scheduled, started, or prelaunch-cancelled probe event."""

    def record_quota_probe_settled(
        self, evidence: QuotaProbeEvidence, /
    ) -> QuotaProbeSettled:
        """Project process evidence and append its settled probe record."""

    def record_quota_telemetry(self, event: QuotaTelemetryEvent, /) -> None:
        """Append passive provider-neutral quota telemetry."""

    def finalize(self, record: RunRecord, /) -> None:
        """Persist final accounting; a failure leaves evidence incomplete."""


type CreateEvidence = Callable[[Path, FrozenPlan], PreparedEvidence]
type ProjectAttempt = Callable[
    [RunId, CallId, int, AttemptNumber, AttemptEvidence, RetryAssessment | None],
    AttemptRecord,
]
type AppendAttempt = Callable[[AttemptRecord], None]
type AppendWaitEvent = Callable[[WaitEvent], None]
type AppendProbeEvent = Callable[[QuotaProbeLifecycleInput], None]
type ProjectSettledProbe = Callable[[QuotaProbeEvidence], QuotaProbeSettled]
type AppendSettledProbe = Callable[[QuotaProbeSettled], None]
type AppendQuotaTelemetry = Callable[[QuotaTelemetryEvent], None]
type FinalizeEvidence = Callable[[RunRecord], None]


class EvidenceStoreAdapter:
    """Compose ordered evidence operations around unfinished typed leaves.

    Projection receives live supervisor evidence, while records contain only
    serializable scalars and artifact references. Every persistence leaf is
    synchronous so dispatch cannot proceed before its outcome is durable.

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
        """Store leaf operations used by this synchronous evidence boundary."""
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

    def create(self, output_directory: Path, plan: FrozenPlan, /) -> PreparedEvidence:
        """Exclusively prepare evidence before dispatch by delegating the leaf.

        Returns:
            The paths to the prepared evidence area and staged instructions.
        """
        return self._create_evidence(output_directory, plan)

    def record_attempt(
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
        record = self._project_attempt(
            run_id,
            call_id,
            position,
            attempt_number,
            evidence,
            retry_assessment,
        )
        self._append_attempt(record)
        return record

    def record_wait_event(self, event: WaitEvent, /) -> None:
        """Append each wait transition synchronously before policy advances."""
        self._append_wait_event(event)

    def record_quota_probe_event(self, event: QuotaProbeLifecycleInput, /) -> None:
        """Append a scalar probe transition without inventing process evidence."""
        self._append_probe_event(event)

    def record_quota_probe_settled(
        self, evidence: QuotaProbeEvidence, /
    ) -> QuotaProbeSettled:
        """Project and append settled probe evidence before quota resumption.

        Returns:
            The shared process projection and quota assessment after append.
        """
        settled = self._project_settled_probe(evidence)
        self._append_settled_probe(settled)
        return settled

    def record_quota_telemetry(self, event: QuotaTelemetryEvent, /) -> None:
        """Append passive telemetry as a separate associated observation."""
        self._append_quota_telemetry(event)

    def finalize(self, record: RunRecord, /) -> None:
        """Persist truthful final accounting through the supplied leaf."""
        self._finalize_evidence(record)


def _create_evidence(output_directory: Path, plan: FrozenPlan, /) -> PreparedEvidence:
    """Exclusive creation and pre-dispatch plan persistence are unfinished."""
    raise NotImplementedError("exclusive evidence creation is not implemented")


def _project_attempt(
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


def _append_attempt(record: AttemptRecord, /) -> None:
    """Append-only attempt record persistence is unfinished."""
    raise NotImplementedError("attempt record persistence is not implemented")


def _append_wait_event(event: WaitEvent, /) -> None:
    """Append-only wait event persistence is unfinished."""
    raise NotImplementedError("wait event persistence is not implemented")


def _append_probe_event(event: QuotaProbeLifecycleInput, /) -> None:
    """Append-only probe lifecycle persistence is unfinished."""
    raise NotImplementedError("probe event persistence is not implemented")


def _project_settled_probe(evidence: QuotaProbeEvidence, /) -> QuotaProbeSettled:
    """Probe artifact writing and process projection are unfinished."""
    raise NotImplementedError("settled probe projection is not implemented")


def _append_settled_probe(event: QuotaProbeSettled, /) -> None:
    """Append-only settled probe persistence is unfinished."""
    raise NotImplementedError("settled probe persistence is not implemented")


def _append_quota_telemetry(event: QuotaTelemetryEvent, /) -> None:
    """Append-only passive telemetry persistence is unfinished."""
    raise NotImplementedError("quota telemetry persistence is not implemented")


def _finalize_evidence(record: RunRecord, /) -> None:
    """Final run accounting persistence is unfinished."""
    raise NotImplementedError("final evidence persistence is not implemented")
