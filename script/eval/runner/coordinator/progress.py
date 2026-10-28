# SPDX-License-Identifier: Apache-2.0
"""Pure projection of coordinator state and durable evidence."""

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, assert_never

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

type CallBucket = Literal[
    "calls_queued",
    "calls_stopped_not_started",
    "calls_active",
    "calls_retry_wait",
    "calls_evidence_pending",
    "calls_succeeded",
    "calls_failed",
    "calls_cancelled",
]
type AttemptBucket = Literal[
    "attempts_started",
    "retries_started",
    "attempts_active",
    "attempts_evidence_pending",
    "attempts_succeeded",
    "attempts_failed",
    "attempts_cancelled",
]
type ProbeBucket = Literal[
    "probes_started",
    "probes_active",
    "probes_evidence_pending",
    "probes_completed",
    "probes_failed",
    "probes_cancelled",
]
type Bucket = CallBucket | AttemptBucket | ProbeBucket


@dataclass(frozen=True)
class ProgressView:
    """Capture coherent owner states and durable histories with explicit clocks.

    Monotonic time measures waits; UTC time measures producer observation age.
    """

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
    counts: Counter[Bucket] = Counter()
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
    state: CallState, counts: Counter[Bucket], reasons: Counter[RetryClass]
) -> None:
    """Count one call state and its durable and current attempts."""
    history = state.history
    bucket: CallBucket
    match state:
        case Queued():
            bucket = "calls_queued"
        case Attempting() | Recording() | ObservingQuota() | RecordingTelemetry():
            bucket = "calls_active"
        case RetryWait():
            bucket = "calls_retry_wait"
        case EvidencePending():
            bucket = "calls_evidence_pending"
        case Finished(outcome=outcome):
            bucket = _terminal_call_bucket(outcome)
        case Stopped(outcome=outcome):
            bucket = (
                "calls_stopped_not_started"
                if not history.attempts
                else _terminal_call_bucket(outcome)
            )
        case unexpected:
            assert_never(unexpected)
    counts[bucket] += 1
    _count_attempts(state, counts, reasons)


def _terminal_call_bucket(
    outcome: Literal["success", "failure", "cancelled", "not_started"],
) -> CallBucket:
    """Map a settled outcome to its call bucket.

    Returns:
        The corresponding disjoint call bucket.
    """
    match outcome:
        case "success":
            return "calls_succeeded"
        case "failure":
            return "calls_failed"
        case "cancelled":
            return "calls_cancelled"
        case "not_started":
            return "calls_stopped_not_started"
        case other:
            assert_never(other)


def _count_attempts(
    state: CallState, counts: Counter[Bucket], reasons: Counter[RetryClass]
) -> None:
    """Count durable outcomes and at most one current dispatched attempt."""
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


def _probe_outcome(record: QuotaProbeRecord) -> ProbeBucket:
    """Select the terminal bucket for one durable probe record.

    Returns:
        The completed, failed, or cancelled probe bucket.
    """
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
    """Pair each observed window with age from its producer timestamp.

    Returns:
        Window identities and their ages, or unknown ages.
    """
    if observation is None:
        return ()
    return tuple(
        (window.window_id, _age(window.source_observed_at_utc, now))
        for window in observation.windows
    )


def _age(timestamp: str | None, now: str) -> float | None:
    """Return elapsed seconds or unknown for unusable producer time."""
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


def _counts(counts: Counter[Bucket]) -> ProgressCounts:
    """Build the consumer value from the finite projection buckets.

    Returns:
        Counts for every consumer field.
    """
    return ProgressCounts(
        calls_queued=counts["calls_queued"],
        calls_stopped_not_started=counts["calls_stopped_not_started"],
        calls_active=counts["calls_active"],
        calls_retry_wait=counts["calls_retry_wait"],
        calls_evidence_pending=counts["calls_evidence_pending"],
        calls_succeeded=counts["calls_succeeded"],
        calls_failed=counts["calls_failed"],
        calls_cancelled=counts["calls_cancelled"],
        attempts_started=counts["attempts_started"],
        retries_started=counts["retries_started"],
        attempts_active=counts["attempts_active"],
        attempts_evidence_pending=counts["attempts_evidence_pending"],
        attempts_succeeded=counts["attempts_succeeded"],
        attempts_failed=counts["attempts_failed"],
        attempts_cancelled=counts["attempts_cancelled"],
        probes_started=counts["probes_started"],
        probes_active=counts["probes_active"],
        probes_evidence_pending=counts["probes_evidence_pending"],
        probes_completed=counts["probes_completed"],
        probes_failed=counts["probes_failed"],
        probes_cancelled=counts["probes_cancelled"],
    )
