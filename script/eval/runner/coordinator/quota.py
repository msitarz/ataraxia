# SPDX-License-Identifier: Apache-2.0
"""Pure quota recovery decisions over durable and sampled facts."""

from asyncio import CancelledError
from dataclasses import replace
from datetime import datetime

from script.eval.model import (
    HarnessConfig,
    QuotaObservation,
    QuotaProbeEvidence,
    QuotaProbeRecord,
    QuotaProbeRequest,
    WaitEnd,
    WaitRecord,
)
from script.eval.runner.policy import quota_probe_allowed, safe_process_cleanup

from .state import (
    Draining,
    Open,
    PreparingProbe,
    ProbeDispatchEvent,
    ProbeEvidencePending,
    ProbeNotDispatched,
    Probing,
    QuotaEvidencePending,
    QuotaHistory,
    QuotaStopped,
    RecordingProbe,
    StopReason,
    Waiting,
    WaitWrite,
)


def quota_wait_started(
    state: Draining,
    waiting: Waiting,
    cancellation: CancelledError | None,
    stop: StopReason | None,
    closure: WaitRecord | None,
    /,
) -> Waiting:
    """Retain a durable start and any closure required by cancellation.

    Returns:
        The next state built from the supplied facts.

    Raises:
        ValueError: The supplied facts do not belong to the same lifecycle.
    """
    if waiting.context != state.context or waiting.start_phase != "submitted":
        raise ValueError("submitted wait does not match pause")
    if (cancellation is not None or stop is not None) and closure is None:
        raise ValueError("stopped wait requires closure")
    cancelled = cancellation is not None or (
        stop is not None and stop.cancellation is not None
    )
    if cancelled and closure is not None and closure.end != "cancelled":
        raise ValueError("cancelled wait requires cancelled closure")
    if closure is not None and (
        closure.wait_id != waiting.wait_id or closure.context != waiting.context
    ):
        raise ValueError("closure does not belong to wait")
    return replace(waiting, start_phase="durable", end_record=closure)


def probe_dispatch_gate(
    state: PreparingProbe,
    config: HarnessConfig,
    probes_used: int,
    remaining_seconds: float | None,
    stop: StopReason | None,
    cancellation: CancelledError | None,
    ended_at_utc: str,
    elapsed_seconds: float,
    /,
) -> PreparingProbe | ProbeNotDispatched:
    """Gate a prepared probe using newly sampled policy and control facts.

    Returns:
        The next state built from the supplied facts.
    """
    cause = (
        "cancelled"
        if cancellation is not None
        or (stop is not None and stop.cancellation is not None)
        else "stop"
        if stop is not None
        else "bound"
        if (remaining_seconds is not None and remaining_seconds <= 0)
        or not quota_probe_allowed(config, probes_used)
        else None
    )
    if cause is None:
        return state
    return ProbeNotDispatched(state.preparation, cause, ended_at_utc, elapsed_seconds)


def probe_dispatched(state: PreparingProbe, request: QuotaProbeRequest, /) -> Probing:
    """Retain the exact request at actual invocation.

    Returns:
        The next state built from the supplied facts.

    Raises:
        ValueError: The supplied facts do not belong to the same lifecycle.
    """
    if (
        request.schedule != state.preparation.schedule
        or request.pause_wait_id != state.preparation.pause_wait_id
        or request.pause_wait_id != state.waiting.wait_id
        or request.schedule.scope != state.waiting.context.quota_observation.scope
    ):
        raise ValueError("request does not belong to prepared probe")
    return Probing(state.waiting, request)


def capture_probe(
    state: Probing, evidence: QuotaProbeEvidence | None, error: BaseException | None, /
) -> RecordingProbe | ProbeEvidencePending:
    """Keep exact-request evidence, or retain an unresolved obligation.

    Returns:
        The next state built from the supplied facts.
    """
    if evidence is None or evidence.request is not state.request:
        return ProbeEvidencePending(
            state.waiting,
            state.request,
            None,
            error
            if error is not None
            else ValueError("missing or mismatched probe evidence"),
        )
    return RecordingProbe(state.waiting, evidence)


def _fresh(
    observation: QuotaObservation | None, waiting: Waiting, now_utc: str, /
) -> bool:
    if (
        observation is None
        or observation.scope is None
        or observation.scope != waiting.context.quota_observation.scope
        or observation.valid_until_utc is None
        or not observation.windows
    ):
        return False
    if any(
        window.state not in {"available", "exhausted"} for window in observation.windows
    ):
        return False
    try:
        expiry = datetime.fromisoformat(
            observation.valid_until_utc.replace("Z", "+00:00")
        )
        now = datetime.fromisoformat(now_utc.replace("Z", "+00:00"))
    except ValueError:
        return False
    return expiry.tzinfo is not None and now.tzinfo is not None and now <= expiry


def probe_persisted(
    state: RecordingProbe,
    history: QuotaHistory,
    record: QuotaProbeRecord,
    stop: StopReason | None,
    remaining_seconds: float | None,
    now_utc: str,
    monotonic_now: float,
    /,
) -> tuple[QuotaHistory, Waiting]:
    """Append a durable probe and retain a pending closure when required.

    Returns:
        The next state built from the supplied facts.

    Raises:
        ValueError: The supplied facts do not belong to the same lifecycle.
    """
    if (
        record.request is not state.evidence.request
        or record.quota_state != state.evidence.quota_state
        or record.observation != state.evidence.observation
    ):
        raise ValueError("probe record does not match request")
    history = replace(history, probes=(*history.probes, record))
    waiting = replace(
        state.waiting, observation=record.observation or state.waiting.observation
    )
    end = (
        "cancelled"
        if stop is not None and stop.cancellation is not None
        else "stop"
        if stop is not None
        else "bound"
        if remaining_seconds is not None and remaining_seconds <= 0
        else None
    )
    if end is None:
        end = _probe_end(record, waiting, now_utc)
    if end is not None:
        closure = WaitRecord(
            wait_id=waiting.wait_id,
            context=waiting.context,
            started_at_utc=waiting.started_at_utc,
            ended_at_utc=now_utc,
            elapsed_seconds=max(0.0, monotonic_now - waiting.started_monotonic),
            end=end,
            diagnostic=None,
        )
        waiting = replace(waiting, end_record=closure)
    return history, waiting


def _probe_end(
    record: QuotaProbeRecord, waiting: Waiting, now_utc: str, /
) -> WaitEnd | None:
    observation = record.observation
    if record.control_flow != "returned" or record.outcome_kind != "completed":
        return "unknown"
    if record.cleanup is None or record.cleanup.process != "owned":
        return "unknown"
    if not safe_process_cleanup(record) or not _fresh(observation, waiting, now_utc):
        return "unknown"
    if observation is None:
        return "unknown"
    if record.quota_state == "exhausted" and any(
        window.state == "exhausted" for window in observation.windows
    ):
        return None
    if (
        record.quota_state == "available"
        and record.exit_status == 0
        and all(window.state == "available" for window in observation.windows)
    ):
        return "quota_available"
    return "unknown"


def quota_wait_completed(
    state: Waiting,
    history: QuotaHistory,
    record: WaitRecord,
    stop: StopReason | None,
    remaining_seconds: float | None,
    now_utc: str,
    /,
) -> tuple[QuotaHistory, Open | QuotaStopped]:
    """Open only after durable closure and a still-fresh scoped observation.

    Returns:
        The next state built from the supplied facts.

    Raises:
        ValueError: The supplied facts do not belong to the same lifecycle.
    """
    if (
        state.start_phase != "durable"
        or state.end_record != record
        or record.wait_id != state.wait_id
        or record.context != state.context
    ):
        raise ValueError("closure does not belong to durable wait")
    history = replace(history, waits=(*history.waits, record))
    if stop is not None or (remaining_seconds is not None and remaining_seconds <= 0):
        return history, QuotaStopped()
    if (
        record.end == "quota_available"
        and _fresh(state.observation, state, now_utc)
        and all(window.state == "available" for window in state.observation.windows)
    ):
        return history, Open()
    return history, QuotaStopped()


def quota_write_failed(
    state: Waiting | PreparingProbe | Probing | RecordingProbe | ProbeEvidencePending,
    obligation: WaitWrite | ProbeDispatchEvent,
    error: BaseException,
    /,
) -> QuotaEvidencePending:
    """Retain the failed journal input and any dispatched probe.

    Returns:
        The next state built from the supplied facts.
    """
    if isinstance(state, Waiting):
        return QuotaEvidencePending(state, obligation, error, None)
    if isinstance(state, PreparingProbe):
        return QuotaEvidencePending(state.waiting, obligation, error, None)
    return QuotaEvidencePending(state.waiting, obligation, error, state)


def probe_write_failed(
    state: RecordingProbe, error: BaseException, /
) -> ProbeEvidencePending:
    """Retain captured probe evidence and the original write error.

    Returns:
        The next state built from the supplied facts.
    """
    return ProbeEvidencePending(
        state.waiting, state.evidence.request, state.evidence, error
    )
