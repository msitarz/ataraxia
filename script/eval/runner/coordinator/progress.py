# SPDX-License-Identifier: Apache-2.0
"""Pure projection of coordinator state and durable evidence."""

from collections import Counter
from dataclasses import dataclass
from datetime import datetime

from script.eval.model import (
    ProcessRecord,
    QuotaObservation,
    QuotaProbeRecord,
    QuotaWindowId,
    RetryClass,
    RunId,
)
from script.eval.runner.policy import safe_process_cleanup
from script.eval.runner.ports import (
    CallWait,
    ProgressCounts,
    ProgressFinalStatus,
    ProgressRunPhase,
    ProgressSnapshot,
)

from .call_states import (
    Attempting,
    AttemptWrite,
    CallState,
    EvidencePending,
    Finished,
    ObservingQuota,
    Queued,
    Recording,
    RecordingTelemetry,
    RetryWait,
    Stopped,
)
from .quota_states import (
    ProbeEvidencePending,
    Probing,
    QuotaEvidencePending,
    QuotaHistory,
    QuotaState,
    RecordingProbe,
)


@dataclass(frozen=True)
class ProgressView:
    """Coherent owner state and explicit clocks for one projection."""

    run_id: RunId
    phase: ProgressRunPhase
    final_status: ProgressFinalStatus | None
    calls: tuple[CallState, ...]
    quota: QuotaState
    probes: QuotaHistory
    observation: QuotaObservation | None
    monotonic_now: float
    utc_now: str


def project(view: ProgressView, /) -> ProgressSnapshot:
    """Derive separate call, attempt, and probe counts without effects.

    Retry reasons count dispatched retries by the preceding durable attempt's
    classification. A waiting retry is not counted until it is dispatched.

    Returns:
        An immutable consumer snapshot of the supplied facts.
    """
    counts: Counter[str] = Counter()
    reasons: Counter[RetryClass] = Counter()
    waits: list[CallWait] = []
    for state in view.calls:
        _count_call(state, counts, reasons)
        if isinstance(state, RetryWait):
            elapsed = max(0.0, view.monotonic_now - state.wait.started_monotonic)
            waits.append(
                CallWait(
                    state.history.call.call_id,
                    "capacity",
                    state.wait.context.failed_attempt_number,
                    elapsed,
                    max(0.0, state.wait.context.sampled_seconds - elapsed),
                )
            )
    for record in view.probes.probes:
        counts["probes_started"] += 1
        counts[_probe_outcome(record)] += 1
    probe = (
        view.quota.probe if isinstance(view.quota, QuotaEvidencePending) else view.quota
    )
    if isinstance(probe, Probing | RecordingProbe | ProbeEvidencePending):
        counts["probes_started"] += 1
        counts[
            "probes_evidence_pending"
            if isinstance(probe, ProbeEvidencePending)
            else "probes_active"
        ] += 1
    return ProgressSnapshot(
        view.run_id,
        view.phase,
        view.final_status,
        _counts(counts),
        tuple(sorted(reasons.items())),
        tuple(waits),
        view.observation,
        _window_ages(view.observation, view.utc_now),
    )


def _count_call(
    state: CallState, counts: Counter[str], reasons: Counter[RetryClass]
) -> None:
    history = state.history
    if isinstance(state, Queued):
        bucket = "calls_queued"
    elif isinstance(
        state, Attempting | Recording | ObservingQuota | RecordingTelemetry
    ):
        bucket = "calls_active"
    elif isinstance(state, RetryWait):
        bucket = "calls_retry_wait"
    elif isinstance(state, EvidencePending):
        bucket = "calls_evidence_pending"
    elif isinstance(state, Stopped) and not history.attempts:
        bucket = "calls_stopped_not_started"
    else:
        assert isinstance(state, Finished | Stopped)
        bucket = {
            "success": "calls_succeeded",
            "failure": "calls_failed",
            "cancelled": "calls_cancelled",
            "not_started": "calls_stopped_not_started",
        }[state.outcome]
    counts[bucket] += 1
    _count_attempts(state, counts, reasons)


def _count_attempts(
    state: CallState, counts: Counter[str], reasons: Counter[RetryClass]
) -> None:
    history = state.history
    for record in history.attempts:
        counts["attempts_started"] += 1
        if record.control_flow == "cancelled" or record.outcome_kind == "cancelled":
            counts["attempts_cancelled"] += 1
        elif _safe_completion(record) and record.exit_status == 0:
            counts["attempts_succeeded"] += 1
        else:
            counts["attempts_failed"] += 1
    current = isinstance(state, Attempting | Recording) or (
        isinstance(state, EvidencePending)
        and isinstance(state.failure.obligation, AttemptWrite)
    )
    if current:
        counts["attempts_started"] += 1
        counts[
            "attempts_evidence_pending"
            if isinstance(state, EvidencePending)
            else "attempts_active"
        ] += 1
    started = len(history.attempts) + int(current)
    counts["retries_started"] += max(0, started - 1)
    for record in history.attempts[: max(0, started - 1)]:
        if record.retry_assessment is not None:
            reasons[record.retry_assessment.retry_class] += 1


def _safe_completion(record: ProcessRecord) -> bool:
    """Return whether a completed process has safe owned cleanup."""
    return (
        record.control_flow == "returned"
        and record.outcome_kind == "completed"
        and record.cleanup is not None
        and record.cleanup.process == "owned"
        and safe_process_cleanup(record)
    )


def _probe_outcome(record: QuotaProbeRecord) -> str:
    if record.control_flow == "cancelled" or record.outcome_kind == "cancelled":
        return "probes_cancelled"
    if _safe_completion(record) and (
        record.quota_state == "exhausted"
        or (record.quota_state == "available" and record.exit_status == 0)
    ):
        return "probes_completed"
    return "probes_failed"


def _window_ages(
    observation: QuotaObservation | None, now: str
) -> tuple[tuple[QuotaWindowId, float | None], ...]:
    if observation is None:
        return ()
    return tuple(
        (window.window_id, _age(window.source_observed_at_utc, now))
        for window in observation.windows
    )


def _age(timestamp: str | None, now: str) -> float | None:
    if timestamp is None:
        return None
    try:
        observed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        current = datetime.fromisoformat(now.replace("Z", "+00:00"))
        if observed.utcoffset() is None or current.utcoffset() is None:
            return None
        seconds = (current - observed).total_seconds()
    except ValueError, OverflowError:
        return None
    return seconds if seconds >= 0 else None


def _counts(counts: Counter[str]) -> ProgressCounts:
    return ProgressCounts(**{
        field: counts[field] for field in ProgressCounts.__dataclass_fields__
    })
