# SPDX-License-Identifier: Apache-2.0
"""Pure call settlement decisions over captured and durable facts."""

from asyncio import CancelledError
from dataclasses import dataclass, replace
from typing import Literal

from script.eval.model import (
    AttemptEvidence,
    AttemptNumber,
    AttemptRecord,
    CallId,
    CapacityWaitContext,
    HarnessConfig,
    ProcessRecord,
    QuotaTelemetryEvent,
    RetryAssessment,
    WaitId,
    WaitRecord,
)
from script.eval.runner.policy import (
    capacity_retry_allowed,
    confident_no_result,
    infrastructure_retry_allowed,
    safe_process_cleanup,
)
from script.eval.runner.ports import EffectiveCall

from .state import StopReason, WaitWrite


@dataclass(frozen=True)
class CallHistory:
    """Durable records for one position; the active attempt is not in history."""

    call: EffectiveCall
    attempts: tuple[AttemptRecord, ...]
    waits: tuple[WaitRecord, ...]


@dataclass(frozen=True)
class AttemptWrite:
    """Captured attempt and classification retained until the write succeeds."""

    number: AttemptNumber
    evidence: AttemptEvidence
    assessment: RetryAssessment | None


@dataclass(frozen=True)
class CallEvidenceFailure:
    """A failed obligation and error; history retains any durable attempt."""

    obligation: AttemptWrite | WaitWrite | QuotaTelemetryEvent
    error: BaseException


@dataclass(frozen=True)
class CallWait:
    """A call-local wait from preparation through durable end.

    A prepared wait has a sampled delay but no submitted start write. The owner
    submits and retains that write until it settles. ``start_phase`` determines
    whether cancellation must close the wait; monotonic time and the sampled
    delay support progress without a parallel timer ledger.
    """

    wait_id: WaitId
    context: CapacityWaitContext
    started_at_utc: str
    started_monotonic: float
    start_phase: Literal["prepared", "submitted", "durable"]
    end_record: WaitRecord | None

    def matches_retry(
        self, call_id: CallId, attempt_number: AttemptNumber, retry_index: int, /
    ) -> bool:
        """Check this prepared wait belongs to the selected capacity retry.

        Returns:
            Whether the call, attempt, retry index, and phase match.
        """
        return (
            self.context.call_id == call_id
            and self.context.failed_attempt_number == attempt_number
            and self.context.retry_index == retry_index
            and self.start_phase == "prepared"
        )


@dataclass(frozen=True)
class Queued:
    """Runnable or gated planned position; history distinguishes a retry."""

    history: CallHistory


@dataclass(frozen=True)
class Attempting:
    """One dispatched invocation, including its supervisor cleanup."""

    history: CallHistory
    attempt_number: AttemptNumber

    def capture(
        self, evidence: AttemptEvidence, assessment: RetryAssessment | None, /
    ) -> Recording:
        """Retain captured evidence without claiming a durable attempt.

        Returns:
            The next state built from the supplied facts.

        Raises:
            ValueError: The supplied facts do not belong to the same lifecycle.
        """
        if evidence.request is not self.history.call.request:
            raise ValueError("attempt request does not belong to call")
        return Recording(
            self.history, AttemptWrite(self.attempt_number, evidence, assessment)
        )


@dataclass(frozen=True)
class Recording:
    """A captured attempt whose required write has not yet settled."""

    history: CallHistory
    attempt: AttemptWrite

    def matches_record(self, record: AttemptRecord, /) -> bool:
        """Check that a durable record belongs to this captured attempt.

        Returns:
            Whether its identity, position, and assessment match.
        """
        call = self.history.call
        return (
            record.run_id == call.run_id
            and record.call_id == call.call_id
            and record.attempt_number == self.attempt.number
            and record.position == call.planned_call.position
            and record.retry_assessment == self.attempt.assessment
        )

    def persisted(
        self,
        record: AttemptRecord,
        config: HarnessConfig,
        stop: StopReason | None,
        capacity_wait: CallWait | None,
        /,
    ) -> ObservingQuota | RetryWait | Queued | Finished | Stopped:
        """Append a durable attempt before any observation or retry decision.

        Returns:
            The next state built from the supplied facts.

        Raises:
            ValueError: The supplied facts do not belong to the same lifecycle.
        """
        if not self.matches_record(record):
            raise ValueError("attempt record does not belong to call")
        history = replace(self.history, attempts=(*self.history.attempts, record))
        if config.quota_wait_enabled and stop is None and _safe_returned(record):
            return ObservingQuota(history, self.attempt.number, self.attempt.evidence)
        return _decide(history, config, stop, capacity_wait)

    def write_failed(self, error: BaseException, /) -> EvidencePending:
        """Keep the original error and the unwritten attempt.

        Returns:
            The next state built from the supplied facts.
        """
        return EvidencePending(self.history, CallEvidenceFailure(self.attempt, error))


@dataclass(frozen=True)
class ObservingQuota:
    """The attempt is durable; the adapter is ingesting its passive evidence."""

    history: CallHistory
    attempt_number: AttemptNumber
    evidence: AttemptEvidence

    def matches_event(self, event: QuotaTelemetryEvent, /) -> bool:
        """Check that telemetry belongs to this call attempt.

        Returns:
            Whether the event's run, call, and attempt identities match.
        """
        call = self.history.call
        return (
            event.run_id == call.run_id
            and event.call_id == call.call_id
            and event.attempt_number == self.attempt_number
        )

    def capture(self, event: QuotaTelemetryEvent, /) -> RecordingTelemetry:
        """Retain the exact telemetry event until its write settles.

        Returns:
            The next state built from the supplied facts.

        Raises:
            ValueError: The supplied facts do not belong to the same lifecycle.
        """
        if not self.matches_event(event):
            raise ValueError("telemetry does not belong to attempt")
        return RecordingTelemetry(self.history, event)


@dataclass(frozen=True)
class RecordingTelemetry:
    """The attempt is durable and its observed telemetry write is pending."""

    history: CallHistory
    event: QuotaTelemetryEvent

    def persisted(
        self,
        config: HarnessConfig,
        stop: StopReason | None,
        capacity_wait: CallWait | None,
        /,
    ) -> RetryWait | Queued | Finished | Stopped:
        """Select a call outcome after telemetry is durable.

        Returns:
            The next state built from the supplied facts.
        """
        return _decide(self.history, config, stop, capacity_wait)

    def write_failed(self, error: BaseException, /) -> EvidencePending:
        """Keep the unwritten telemetry alongside the durable attempt.

        Returns:
            The next state built from the supplied facts.
        """
        return EvidencePending(self.history, CallEvidenceFailure(self.event, error))


@dataclass(frozen=True)
class RetryWait:
    """A capacity delay owned by this call, not the quota gate."""

    history: CallHistory
    wait: CallWait

    def write_failed(
        self, obligation: WaitWrite, error: BaseException, /
    ) -> EvidencePending:
        """Keep the exact failed wait write.

        Returns:
            The next state built from the supplied facts.
        """
        return EvidencePending(self.history, CallEvidenceFailure(obligation, error))

    def started(
        self,
        cancellation: CancelledError | None,
        stop: StopReason | None,
        closure: WaitRecord | None,
        /,
    ) -> RetryWait:
        """Mark the submitted start durable, retaining any required closure.

        Returns:
            The next state built from the supplied facts.

        Raises:
            ValueError: The supplied facts do not belong to the same lifecycle.
        """
        if self.wait.start_phase != "submitted":
            raise ValueError("wait start was not submitted")
        if (cancellation is not None or stop is not None) and closure is None:
            raise ValueError("stopped wait requires closure")
        cancelled = cancellation is not None or (
            stop is not None and stop.cancellation is not None
        )
        if cancelled and closure is not None and closure.end != "cancelled":
            raise ValueError("cancelled wait requires cancelled closure")
        if closure is not None and (
            closure.wait_id != self.wait.wait_id or closure.context != self.wait.context
        ):
            raise ValueError("closure does not belong to wait")
        return replace(
            self, wait=replace(self.wait, start_phase="durable", end_record=closure)
        )

    def matches_closure(self, record: WaitRecord, /) -> bool:
        """Check that a closure belongs to this durably started wait.

        Returns:
            Whether the phase, wait identity, and pending closure match.
        """
        return (
            self.wait.start_phase == "durable"
            and record.wait_id == self.wait.wait_id
            and record.context == self.wait.context
            and (self.wait.end_record is None or self.wait.end_record == record)
        )

    def completed(
        self, record: WaitRecord, stop: StopReason | None, /
    ) -> Queued | Stopped:
        """Append a durable end before requeueing or stopping.

        Returns:
            The next state built from the supplied facts.

        Raises:
            ValueError: The supplied facts do not belong to the same lifecycle.
        """
        if not self.matches_closure(record):
            raise ValueError("closure does not belong to durable wait")
        history = replace(self.history, waits=(*self.history.waits, record))
        if record.end == "cancelled" or (
            stop is not None and stop.cancellation is not None
        ):
            return Stopped(history, "cancelled")
        if stop is not None or record.end != "delay_elapsed":
            return Stopped(history, "failure")
        return Queued(history)


@dataclass(frozen=True)
class Finished:
    """A durable terminal call outcome."""

    history: CallHistory
    outcome: Literal["success", "failure", "cancelled"]


@dataclass(frozen=True)
class EvidencePending:
    """The failed obligation retains the attempt or wait facts for inspection."""

    history: CallHistory
    failure: CallEvidenceFailure


@dataclass(frozen=True)
class Stopped:
    """Stop forbids further dispatch; empty attempt history is not started."""

    history: CallHistory
    outcome: Literal["not_started", "failure", "cancelled"]


type CallState = (
    Queued
    | Attempting
    | Recording
    | ObservingQuota
    | RecordingTelemetry
    | RetryWait
    | Finished
    | EvidencePending
    | Stopped
)


def _decide(
    history: CallHistory,
    config: HarnessConfig,
    stop: StopReason | None,
    wait: CallWait | None,
    /,
) -> RetryWait | Queued | Finished | Stopped:
    """Select the call outcome after required evidence becomes durable.

    Returns:
        The selected call state.
    """
    record = history.attempts[-1]
    if record.control_flow == "cancelled" or record.outcome_kind == "cancelled":
        return Stopped(history, "cancelled")
    if stop is not None:
        return Stopped(
            history, "cancelled" if stop.cancellation is not None else "failure"
        )
    if not _safe_returned(record):
        return Finished(history, "failure")
    if record.outcome_kind == "completed":
        if record.exit_status == 0:
            return Finished(history, "success")
        if record.exit_status is None:
            return Finished(history, "failure")
    if record.outcome_kind not in {"completed", "timed_out", "infrastructure_failure"}:
        return Finished(history, "failure")
    return _retry(history, config, wait)


def _retry(
    history: CallHistory, config: HarnessConfig, wait: CallWait | None, /
) -> RetryWait | Queued | Finished:
    """Select a retry using independent allowances and supplied wait facts.

    Returns:
        The selected retry or terminal state.

    Raises:
        ValueError: The capacity wait does not match the retry.
    """
    record = history.attempts[-1]
    assessment = record.retry_assessment
    if assessment is None or not confident_no_result(assessment):
        return Finished(history, "failure")
    if assessment.retry_class == "quota" and config.quota_wait_enabled:
        return Queued(history)
    if (
        assessment.retry_class == "infrastructure"
        and record.outcome_kind == "completed"
        and not config.retry_nonzero_exit
    ):
        return Finished(history, "failure")
    previous = history.attempts[:-1]
    infrastructure_used = sum(
        r.retry_assessment is not None
        and r.retry_assessment.retry_class == "infrastructure"
        for r in previous
    )
    capacity_used = sum(
        r.retry_assessment is not None and r.retry_assessment.retry_class == "capacity"
        for r in previous
    )
    if infrastructure_retry_allowed(assessment, infrastructure_used, config):
        return Queued(history)
    if capacity_retry_allowed(assessment, capacity_used, config):
        if wait is None or not wait.matches_retry(
            history.call.call_id, record.attempt_number, capacity_used
        ):
            raise ValueError("capacity wait does not match retry")
        return RetryWait(history, wait)
    return Finished(history, "failure")


def _safe_returned(record: ProcessRecord, /) -> bool:
    """Determine whether the returned process has safe, owned cleanup.

    Returns:
        Whether the process was safely returned.
    """
    if (
        record.control_flow != "returned"
        or record.outcome_kind == "cancelled"
        or not safe_process_cleanup(record)
    ):
        return False
    if record.outcome_kind == "completed":
        return record.cleanup is not None and record.cleanup.process == "owned"
    return True
