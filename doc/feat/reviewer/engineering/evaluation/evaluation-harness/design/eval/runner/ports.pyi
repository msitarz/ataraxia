# SPDX-License-Identifier: Apache-2.0
"""Consumer-owned values and ports used by dispatch and its adapters."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from script.process_supervisor import AttemptRequest, AttemptResult, DispatchStop

from ..model import (  # ruff: ignore[relative-imports]
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

type ProgressRunPhase = Literal["running", "quota_paused", "stopping", "final"]
type ProgressFinalStatus = Literal[
    "success", "failure", "cancelled", "incomplete_evidence"
]

@dataclass(frozen=True)
class ProgressCounts:
    """Disjoint frozen-plan call states and dispatched-work outcome counts.

    Queued means not yet dispatched while the run is active; it may be gated
    by concurrency or quota. Stopped-not-started means the stop latch prevents
    dispatch. Evidence-pending means an outcome is known in
    memory but its required durable write failed, so no terminal outcome is
    claimed. Attempt and probe evidence-pending counts follow the same rule.
    ``attempts_started`` counts invocations dispatched through ``AttemptCall``;
    it does not imply supervisor acquisition or launch of an OS process.
    ``probes_started`` has the same dispatched-invocation meaning.

    Attempt outcome counts are disjoint: success means zero exit with safe
    process completion, not reviewer approval; failure means a settled
    non-cancelled unsuccessful attempt; cancellation has its own count. Probe
    counts are likewise disjoint: completed means a safely settled operational
    check with a conclusive available or exhausted quota state, including a
    recognized provider rate-limit response mapped to exhausted; failed means
    unknown or malformed
    state, timeout, overflow, infrastructure failure, or unsafe process
    outcome; cancellation is separate. Evidence-pending belongs to none of
    these terminal outcome counts.
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
    """One call-local retry wait; concurrent calls may remain active."""

    call_id: CallId
    reason: Literal["infrastructure", "capacity"]
    attempt_number: AttemptNumber
    elapsed_seconds: float
    remaining_seconds: float | None

@dataclass(frozen=True)
class ProgressSnapshot:
    """Immutable consumer projection of coordinator state and observations.

    ``final_status`` is set only when ``phase`` is ``final``. Failed and
    cancelled calls are settled outcomes, not successful completions.
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
        """Present an immutable snapshot without changing run outcomes.

        This synchronous presentation boundary must return promptly and must
        not perform blocking I/O. Implementations handle expected presentation
        errors locally. They must not suppress cancellation,
        KeyboardInterrupt, or SystemExit.
        """
        ...

@dataclass(frozen=True)
class CliBinding:
    """Immutable CLI identity; dry run deliberately has no binding.

    ``quota_scope`` is absent until the provider/account allowance identity is
    verified; no raw account or credential data belongs in this value.
    """

    executable_path: Path
    cli_version: str | None
    runner_version: str
    effective_settings: tuple[tuple[str, SettingValue], ...]
    quota_scope: QuotaScope | None

class CliBindingResolver(Protocol):
    """Resolve CLI identity only on the execution branch."""

    def resolve(self, config: HarnessConfig, /) -> CliBinding:
        """Resolve CLI identity and only a verified provider/allowance scope.

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
        """Return unknown when category or confident no-result evidence is absent.

        Never parse answer content. A nonzero exit or capacity text alone does
        not establish that no semantic result was produced.
        """
        ...

class QuotaStatusReader(Protocol):
    """Separate passive ingestion from supervised active polling.

    Provider adapters correlate settled-attempt telemetry with their source and
    return observations; active polling is a separate supervised invocation
    with its own ephemeral probe evidence. Both paths produce
    provider-neutral observations through this single port. The provider
    adapter owns required-window completeness and freshness, represents missing
    or malformed required windows explicitly, and does not infer reset times.
    Core policy never interprets provider window IDs.
    """

    @property
    def expected_scope(self) -> QuotaScope | None:
        """Verified scope paired with this reader, if known."""
        ...

    async def observe_settled_attempt(
        self,
        evidence: AttemptEvidence,
        /,
    ) -> QuotaObservation:
        """Return source-backed windows from settled attempt evidence, else unknown.

        Preserve sanitized source coordinates and producer provenance on the
        observation. The coordinator retains call/attempt association and checks
        observation scope against its binding.
        """
        ...

    async def poll(
        self, request: QuotaProbeRequest, stop_dispatch: DispatchStop, /
    ) -> QuotaProbeEvidence:
        """Run one separately supervised probe; never reuse an evaluation call."""
        ...

class Runtime(Protocol):
    """Inject clocks, cancellable waits, and jitter for deterministic policy."""

    def utc_now(self) -> str:
        """Return a timezone-aware UTC timestamp in the persisted format."""
        ...

    def monotonic(self) -> float:
        """Return monotonic seconds."""
        ...

    async def sleep(self, seconds: float, /) -> None:
        """Wait asynchronously; cancellation interrupts and zero waits yield.

        Capacity and quota waits use the same cancellable runtime; a zero
        capacity-jitter sample still yields to the event loop.
        """
        ...

    def uniform(self, lower: float, upper: float, /) -> float:
        """Sample full jitter inclusively within supplied finite bounds."""
        ...

@dataclass(frozen=True)
class BoundRun:
    """Plan and calls sharing one resolved CLI and its optional quota scope."""

    plan: FrozenPlan
    binding: CliBinding
    evidence: PreparedEvidence
    calls: tuple[EffectiveCall, ...]
