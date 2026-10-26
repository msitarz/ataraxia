# SPDX-License-Identifier: Apache-2.0
"""Consumer-owned values and ports used by dispatch and its adapters."""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

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
    RetryAssessment,
    RunId,
    SettingValue,
)

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
        call_id: CallId,
        attempt_number: AttemptNumber,
        evidence: AttemptEvidence,
        expected_scope: QuotaScope,
        /,
    ) -> QuotaObservation:
        """Return source-backed windows for this attempt, else unknown.

        Preserve sanitized source coordinates and producer provenance on the
        observation; provider-specific invocation identifiers stay in adapters.
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
