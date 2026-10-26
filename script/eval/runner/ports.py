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
    """Disjoint planned-call states and dispatched-work outcome counts.

    Queued means not yet dispatched while active; it may be gated by
    concurrency or quota. Stopped-not-started means the stop latch prevents
    dispatch. Evidence-pending means an outcome is known in memory but its
    required durable write failed, so no terminal outcome is claimed. Attempt
    and probe evidence-pending counts follow the same rule. ``attempts_started``
    counts invocations dispatched through ``AttemptCall``; it does not imply
    supervisor acquisition or OS process launch. Probes use the same meaning.

    For a plan of ``N`` calls,
    ``N == calls_queued + calls_stopped_not_started + calls_active +
    calls_retry_wait + calls_evidence_pending + calls_succeeded +
    calls_failed + calls_cancelled``.
    Dispatched attempts partition into active, evidence-pending, succeeded,
    failed, and cancelled invocations; ``retries_started`` is a subset of
    ``attempts_started`` and retries add attempts, never calls. Success means
    safe zero-exit process completion, not reviewer approval. Probe completion
    means a safe, conclusive operational check, including recognized
    exhaustion; unknown or malformed state is a failure. Cancellation and
    evidence-pending remain separate from terminal outcomes.
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
    """Immutable projection of coordinator state and existing observations.

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
    """Classify settled evidence without reading semantic answers."""

    def assess(self, evidence: AttemptEvidence, /) -> RetryAssessment:
        """Return unknown without verified category and confident no-result.

        Never parse answer content or infer absence from nonzero exit or
        capacity text alone.
        """
        ...


class QuotaStatusReader(Protocol):
    """Expose passive ingestion and separate supervised active polling.

    The provider adapter owns required-window completeness and freshness,
    represents missing or malformed required windows explicitly, and does not
    infer reset times. Core policy never interprets provider window IDs.
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
