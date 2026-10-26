# SPDX-License-Identifier: Apache-2.0
"""Consumer-owned values and ports used by dispatch and its adapters."""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from script.process_supervisor import AttemptRequest, AttemptResult, DispatchStop

from ..model import (  # ruff: ignore[relative-imports]
    AttemptEvidence,
    CallId,
    FrozenPlan,
    HarnessConfig,
    PlannedCall,
    PreparedEvidence,
    QuotaObservation,
    RetryAssessment,
    RunId,
    SettingValue,
)

@dataclass(frozen=True)
class CliBinding:
    """Immutable CLI identity; dry run deliberately has no binding."""

    executable_path: Path
    cli_version: str | None
    runner_version: str
    effective_settings: tuple[tuple[str, SettingValue], ...]

class CliBindingResolver(Protocol):
    """Resolve CLI identity only on the execution branch."""

    def resolve(self, config: HarnessConfig, /) -> CliBinding:
        """Resolve the absolute executable path, version, and effective settings."""
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
    """Return both source-backed windows or explicit unknown observations.

    Always represent five-hour and weekly windows. Map missing or malformed
    source fields to unknown or unavailable observations in their window
    positions; never omit a window or infer reset times.
    """

    async def read(self) -> QuotaObservation:
        """Return unavailable or unknown fields rather than guessed reset values."""
        ...

class AsyncWaiter(Protocol):
    """Inject clocks and cancellable waits for deterministic policy checks."""

    def utc_now(self) -> str:
        """Return a timezone-aware UTC timestamp in the persisted format."""
        ...

    def monotonic(self) -> float:
        """Return monotonic seconds."""
        ...

    async def sleep(self, seconds: float, /) -> None:
        """Wait asynchronously; cancellation interrupts and zero waits yield."""
        ...

class RandomSource(Protocol):
    """Inject full-jitter sampling without coupling policy to global randomness."""

    def uniform(self, lower: float, upper: float, /) -> float:
        """Sample inclusively within the supplied finite bounds."""
        ...

class Runtime(AsyncWaiter, RandomSource, Protocol):
    """Combined runtime dependency used by the coordinator."""

@dataclass(frozen=True)
class BoundRun:
    """Plan, resolved CLI, staged evidence paths, and built effective calls."""

    plan: FrozenPlan
    binding: CliBinding
    evidence: PreparedEvidence
    calls: tuple[EffectiveCall, ...]
