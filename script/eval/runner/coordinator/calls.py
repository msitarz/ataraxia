# SPDX-License-Identifier: Apache-2.0
"""Pure call settlement decisions over captured and durable facts."""

from asyncio import CancelledError
from dataclasses import replace

from script.eval.model import (
    AttemptEvidence,
    AttemptRecord,
    HarnessConfig,
    ProcessRecord,
    QuotaTelemetryEvent,
    RetryAssessment,
    WaitRecord,
)
from script.eval.runner.policy import (
    capacity_retry_allowed,
    confident_no_result,
    infrastructure_retry_allowed,
)

from .state import (
    Attempting,
    AttemptWrite,
    CallEvidenceFailure,
    CallHistory,
    CallWait,
    EvidencePending,
    Finished,
    ObservingQuota,
    Queued,
    Recording,
    RecordingTelemetry,
    RetryWait,
    Stopped,
    StopReason,
    WaitWrite,
)


def capture_attempt(
    state: Attempting, evidence: AttemptEvidence, assessment: RetryAssessment | None, /
) -> Recording:
    """Retain captured evidence without claiming a durable attempt.

    Returns:
        The next state built from the supplied facts.

    Raises:
        ValueError: The supplied facts do not belong to the same lifecycle.
    """
    if evidence.request is not state.history.call.request:
        raise ValueError("attempt request does not belong to call")
    return Recording(
        state.history, AttemptWrite(state.attempt_number, evidence, assessment)
    )


def attempt_persisted(
    state: Recording,
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
    call = state.history.call
    if (
        (record.run_id, record.call_id, record.attempt_number)
        != (
            call.run_id,
            call.call_id,
            state.attempt.number,
        )
        or record.position != call.planned_call.position
        or record.retry_assessment != state.attempt.assessment
    ):
        raise ValueError("attempt record does not belong to call")
    history = replace(state.history, attempts=(*state.history.attempts, record))
    if config.quota_wait_enabled and stop is None and _safe_returned(record):
        return ObservingQuota(history, state.attempt.number, state.attempt.evidence)
    return _decide(history, config, stop, capacity_wait)


def capture_telemetry(
    state: ObservingQuota, event: QuotaTelemetryEvent, /
) -> RecordingTelemetry:
    """Retain the exact telemetry event until its write settles.

    Returns:
        The next state built from the supplied facts.

    Raises:
        ValueError: The supplied facts do not belong to the same lifecycle.
    """
    call = state.history.call
    if (event.run_id, event.call_id, event.attempt_number) != (
        call.run_id,
        call.call_id,
        state.attempt_number,
    ):
        raise ValueError("telemetry does not belong to attempt")
    return RecordingTelemetry(state.history, event)


def telemetry_persisted(
    state: RecordingTelemetry,
    config: HarnessConfig,
    stop: StopReason | None,
    capacity_wait: CallWait | None,
    /,
) -> RetryWait | Queued | Finished | Stopped:
    """Select a call outcome after telemetry is durable.

    Returns:
        The next state built from the supplied facts.
    """
    return _decide(state.history, config, stop, capacity_wait)


def _decide(
    history: CallHistory,
    config: HarnessConfig,
    stop: StopReason | None,
    wait: CallWait | None,
    /,
) -> RetryWait | Queued | Finished | Stopped:
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
        if (
            wait is None
            or wait.context.call_id != history.call.call_id
            or wait.context.failed_attempt_number != record.attempt_number
            or wait.context.retry_index != capacity_used
            or wait.start_phase != "prepared"
        ):
            raise ValueError("capacity wait does not match retry")
        return RetryWait(history, wait)
    return Finished(history, "failure")


def _safe_returned(record: ProcessRecord, /) -> bool:
    if (
        record.control_flow != "returned"
        or record.outcome_kind == "cancelled"
        or not _safe_cleanup(record)
    ):
        return False
    if record.outcome_kind == "completed":
        return record.cleanup is not None and record.cleanup.process == "owned"
    return True


def _safe_cleanup(record: ProcessRecord, /) -> bool:
    cleanup = record.cleanup
    if cleanup is None or cleanup.wait_diagnostic is not None:
        return False
    if cleanup.process == "not_started":
        return not cleanup.signals and cleanup.direct_wait == "not_started"
    return (
        cleanup.process == "owned"
        and cleanup.direct_wait == "reaped"
        and tuple(item.signal for item in cleanup.signals)
        in {("SIGKILL",), ("SIGTERM", "SIGKILL")}
        and all(
            item.outcome in {"sent", "no_target"} and item.diagnostic is None
            for item in cleanup.signals
        )
    )


def attempt_write_failed(state: Recording, error: BaseException, /) -> EvidencePending:
    """Keep the original error and the unwritten attempt.

    Returns:
        The next state built from the supplied facts.
    """
    return EvidencePending(state.history, CallEvidenceFailure(state.attempt, error))


def telemetry_write_failed(
    state: RecordingTelemetry, error: BaseException, /
) -> EvidencePending:
    """Keep the unwritten telemetry alongside the durable attempt.

    Returns:
        The next state built from the supplied facts.
    """
    return EvidencePending(state.history, CallEvidenceFailure(state.event, error))


def call_wait_write_failed(
    state: RetryWait, obligation: WaitWrite, error: BaseException, /
) -> EvidencePending:
    """Keep the exact failed wait write.

    Returns:
        The next state built from the supplied facts.
    """
    return EvidencePending(state.history, CallEvidenceFailure(obligation, error))


def call_wait_started(
    state: RetryWait,
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
    if state.wait.start_phase != "submitted":
        raise ValueError("wait start was not submitted")
    if (cancellation is not None or stop is not None) and closure is None:
        raise ValueError("stopped wait requires closure")
    if cancellation is not None and closure is not None and closure.end != "cancelled":
        raise ValueError("cancelled wait requires cancelled closure")
    if closure is not None and (
        closure.wait_id != state.wait.wait_id or closure.context != state.wait.context
    ):
        raise ValueError("closure does not belong to wait")
    return replace(
        state, wait=replace(state.wait, start_phase="durable", end_record=closure)
    )


def call_wait_completed(
    state: RetryWait, record: WaitRecord, stop: StopReason | None, /
) -> Queued | Stopped:
    """Append a durable end before requeueing or stopping.

    Returns:
        The next state built from the supplied facts.

    Raises:
        ValueError: The supplied facts do not belong to the same lifecycle.
    """
    if (
        state.wait.start_phase != "durable"
        or record.wait_id != state.wait.wait_id
        or record.context != state.wait.context
        or (state.wait.end_record is not None and state.wait.end_record != record)
    ):
        raise ValueError("closure does not belong to durable wait")
    history = replace(state.history, waits=(*state.history.waits, record))
    if record.end == "cancelled" or (
        stop is not None and stop.cancellation is not None
    ):
        return Stopped(history, "cancelled")
    if stop is not None or record.end != "delay_elapsed":
        return Stopped(history, "failure")
    return Queued(history)
