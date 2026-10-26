# SPDX-License-Identifier: Apache-2.0
"""Consumer-owned values and ports used by dispatch and its adapters."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from script.eval.model import (
    AttemptEvidence,
    AttemptNumber,
    CallId,
    FrozenPlan,
    HarnessConfig,
    PlannedCall,
    PreparedEvidence,
    QuotaObservation,
    QuotaProbeEvidence,
    QuotaProbeRequest,
    QuotaScope,
    QuotaWindowId,
    RetryAssessment,
    RetryClass,
    RunId,
    SettingValue,
)
from script.process_supervisor import AttemptRequest, AttemptResult, DispatchStop

type ProgressRunPhase = Literal["running", "quota_paused", "stopping", "final"]
type ProgressFinalStatus = Literal[
    "success", "failure", "cancelled", "incomplete_evidence"
]


@dataclass(frozen=True)
class ProgressCounts:
    """Disjoint call states and separate attempt and probe counts.

    Attributes:
        calls_queued: Planned calls awaiting dispatch while the run is active.
            A call may be waiting for concurrency or quota.
        calls_stopped_not_started: Calls never dispatched because stopping
            prevents further dispatch.
        calls_active: Calls with work currently in progress.
        calls_retry_wait: Calls waiting for a retry.
        calls_evidence_pending: Calls whose outcome is known in memory, but
            whose required durable evidence write failed.
        calls_succeeded: Calls with a successfully settled attempt.
        calls_failed: Calls with a settled unsuccessful outcome.
        calls_cancelled: Calls ended by cancellation.
        attempts_started: Attempt invocations dispatched through ``AttemptCall``.
            This does not mean the supervisor acquired or launched an OS process.
        retries_started: Dispatched retry invocations, included in
            ``attempts_started``.
        attempts_active: Dispatched attempts still in progress.
        attempts_evidence_pending: Attempt outcomes known in memory, but with
            a failed required durable evidence write.
        attempts_succeeded: Attempts with zero exit and safe process completion;
            this does not mean reviewer approval.
        attempts_failed: Settled, unsuccessful, non-cancelled attempts.
        attempts_cancelled: Attempts ended by cancellation.
        probes_started: Probe invocations dispatched; this does not imply OS
            process launch.
        probes_active: Dispatched probes still in progress.
        probes_evidence_pending: Probe outcomes known in memory, but with a
            failed required durable evidence write.
        probes_completed: Safely settled operational checks with a conclusive
            available or exhausted quota state. A recognized provider rate-limit
            response mapped to exhausted is conclusive.
        probes_failed: Probes with unknown or malformed state, timeout,
            overflow, infrastructure failure, or an unsafe process outcome.
        probes_cancelled: Probes ended by cancellation.

    Counting rules:
        * Call states partition planned calls: queued, stopped-not-started,
          active, retry-wait, evidence-pending, succeeded, failed, or cancelled.
        * Evidence-pending is not a terminal outcome; it records a failed write
          of required durable evidence.
        * Attempt and probe outcome counts are disjoint. Evidence-pending is
          separate from active and terminal outcomes.
        * Each dispatched attempt is active, evidence-pending, succeeded,
          failed, or cancelled. Probe counts use the same partition, with
          completed in place of succeeded.
        * Retries add attempts, never calls.
    """

    calls_queued: int
    calls_stopped_not_started: int
    calls_active: int
    calls_retry_wait: int
    calls_evidence_pending: int
    calls_succeeded: int
    calls_failed: int
    calls_cancelled: int
    attempts_started: int
    retries_started: int
    attempts_active: int
    attempts_evidence_pending: int
    attempts_succeeded: int
    attempts_failed: int
    attempts_cancelled: int
    probes_started: int
    probes_active: int
    probes_evidence_pending: int
    probes_completed: int
    probes_failed: int
    probes_cancelled: int


@dataclass(frozen=True)
class CallWait:
    """One call-local retry wait; other calls may remain active."""

    call_id: CallId
    reason: Literal["infrastructure", "capacity"]
    attempt_number: AttemptNumber
    elapsed_seconds: float
    remaining_seconds: float | None


@dataclass(frozen=True)
class ProgressSnapshot:
    """Immutable consumer projection of coordinator state and observations.

    ``final_status`` is set only when ``phase`` is ``final``. Failed and
    cancelled calls are settled outcomes, not successful completions. Quota
    observations and producer-based window ages are reused; taking a snapshot
    performs no quota reads, model calls, or input reads.
    """

    run_id: RunId
    phase: ProgressRunPhase
    final_status: ProgressFinalStatus | None
    counts: ProgressCounts
    retry_reasons: tuple[tuple[RetryClass, int], ...]
    call_waits: tuple[CallWait, ...]
    quota_observation: QuotaObservation | None
    quota_window_ages_seconds: tuple[tuple[QuotaWindowId, float | None], ...]


class ProgressSink(Protocol):
    """Present snapshots without delaying evaluation or cancellation."""

    def publish(self, snapshot: ProgressSnapshot, /) -> None:
        """Present a snapshot promptly without blocking I/O or changing outcome.

        Implementations handle expected presentation errors locally. They must
        not suppress cancellation, ``KeyboardInterrupt``, or ``SystemExit``.
        """
        ...


@dataclass(frozen=True)
class CliBinding:
    """Resolved immutable CLI identity; dry run deliberately has no binding.

    ``quota_scope`` is absent until provider/account allowance identity is
    verified. Raw account or credential data does not belong in this value.
    """

    executable_path: Path
    cli_version: str | None
    runner_version: str
    effective_settings: tuple[tuple[str, SettingValue], ...]
    quota_scope: QuotaScope | None


class CliBindingResolver(Protocol):
    """Resolve CLI identity only on the execution branch."""

    def resolve(self, config: HarnessConfig, /) -> CliBinding:
        """Resolve identity and only a verified provider/allowance scope.

        Return ``quota_scope=None`` when that identity cannot be verified.
        """
        ...


@dataclass(frozen=True)
class EffectiveCall:
    """One frozen planned position bound to its supervisor request."""

    run_id: RunId
    call_id: CallId
    planned_call: PlannedCall
    request: AttemptRequest


class AttemptRequestBuilder(Protocol):
    """Build an effective call without reading mutable input paths."""

    def build(
        self,
        plan: FrozenPlan,
        call: PlannedCall,
        binding: CliBinding,
        evidence: PreparedEvidence,
        config: HarnessConfig,
        /,
    ) -> EffectiveCall:
        """Hash frozen effective inputs and build argv without opening paths."""
        ...


class AttemptCall(Protocol):
    """Adapt one invocation to the existing public supervisor boundary."""

    async def __call__(
        self, request: AttemptRequest, stop_dispatch: DispatchStop, /
    ) -> AttemptResult:
        """Run exactly one attempt through ``call_supervisor``."""
        ...


class OutcomeClassifier(Protocol):
    """Classify settled evidence without reading semantic answers.

    A nonzero exit or capacity-like text alone does not establish retry
    eligibility; return unknown until explicit signals and no-result evidence
    have been verified.
    """

    def assess(self, evidence: AttemptEvidence, /) -> RetryAssessment:
        """Return unknown when category or confident no-result is absent.

        Never parse answer content. A nonzero exit or capacity text alone does
        not establish that no semantic result was produced.
        """
        ...


class QuotaStatusReader(Protocol):
    """Separate passive ingestion from supervised active polling.

    Provider adapters correlate settled-attempt telemetry with their source and
    return observations; active polling is a separate supervised invocation
    with its own ephemeral probe evidence. Both paths produce provider-neutral
    observations through this single port. The provider adapter owns
    required-window completeness and freshness, represents missing or malformed
    required windows explicitly, and does not infer reset times. Core policy
    never interprets provider window IDs.
    """

    @property
    def expected_scope(self) -> QuotaScope | None:
        """Verified scope paired with this reader, if known."""
        ...

    async def observe_settled_attempt(
        self, evidence: AttemptEvidence, /
    ) -> QuotaObservation:
        """Return source-backed observation or unknown for settled evidence.

        Preserve sanitized source coordinates and producer provenance. The
        coordinator retains call/attempt association and checks scope against
        its binding.
        """
        ...

    async def poll(
        self, request: QuotaProbeRequest, stop_dispatch: DispatchStop, /
    ) -> QuotaProbeEvidence:
        """Run one separately supervised probe, never reuse an evaluation."""
        ...


class Runtime(Protocol):
    """Inject clocks, cancellable waits, and jitter for deterministic policy."""

    def utc_now(self) -> str:
        """Return timezone-aware UTC in the persisted timestamp format."""
        ...

    def monotonic(self) -> float:
        """Return monotonic seconds."""
        ...

    async def sleep(self, seconds: float, /) -> None:
        """Wait asynchronously; cancellation interrupts and zero waits yield.

        Capacity and quota waits share this cancellable runtime; a zero
        capacity-jitter sample still yields to the event loop.
        """
        ...

    def uniform(self, lower: float, upper: float, /) -> float:
        """Sample full jitter inclusively within supplied finite bounds."""
        ...


@dataclass(frozen=True)
class BoundRun:
    """Plan and calls sharing one resolved CLI and optional quota scope."""

    plan: FrozenPlan
    binding: CliBinding
    evidence: PreparedEvidence
    calls: tuple[EffectiveCall, ...]
