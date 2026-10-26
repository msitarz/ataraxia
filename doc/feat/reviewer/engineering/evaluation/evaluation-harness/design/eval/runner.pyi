# SPDX-License-Identifier: Apache-2.0
"""Runtime binding, request construction, and bounded async dispatch."""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from script.process_supervisor import AttemptRequest, AttemptResult, DispatchStop

from .evidence import EvidenceStore
from .model import (
    AttemptEvidence,
    CallId,
    FrozenPlan,
    HarnessConfig,
    PlannedCall,
    PreparedEvidence,
    QuotaObservation,
    RetryAssessment,
    RunId,
    RunRecord,
    SettingValue,
)

@dataclass(frozen=True)
class CliBinding:
    """Execution-only binding; dry run deliberately has no instance."""

    executable_path: Path
    cli_version: str | None
    runner_version: str
    effective_settings: tuple[tuple[str, SettingValue], ...]

class CliBindingResolver(Protocol):
    """Resolve runtime CLI identity and observable settings at execution time."""

    def resolve(self, config: HarnessConfig, /) -> CliBinding:
        """Resolve the absolute executable path, version, and effective settings."""
        ...

@dataclass(frozen=True)
class EffectiveCall:
    """One planned call bound to settings, identity, and supervisor request."""

    run_id: RunId
    call_id: CallId
    planned_call: PlannedCall
    request: AttemptRequest

class AttemptRequestBuilder(Protocol):
    """Purely build a request from frozen values and a staged artifact path."""

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
    """Adapter to the existing public supervisor boundary."""

    async def __call__(
        self,
        request: AttemptRequest,
        stop_dispatch: DispatchStop,
        /,
    ) -> AttemptResult:
        """Run exactly one attempt through call_supervisor."""
        ...

class OutcomeClassifier(Protocol):
    """Classify only structured supervisor and verified CLI observations."""

    def assess(self, evidence: AttemptEvidence, /) -> RetryAssessment:
        """Return unknown when category or confident no-result basis is absent.

        Never parse answer content. A nonzero exit or capacity text alone does
        not establish that no semantic result was produced.
        """
        ...

class QuotaStatusReader(Protocol):
    """Read source-backed five-hour and weekly status or explicit unknown."""

    async def read(self) -> QuotaObservation:
        """Return unavailable/unknown fields rather than guessed reset values."""
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
        """Wait asynchronously; cancellation must interrupt the wait."""
        ...

class RandomSource(Protocol):
    """Inject full-jitter sampling without coupling policy to global randomness."""

    def uniform(self, lower: float, upper: float, /) -> float:
        """Sample inclusively within the supplied finite bounds."""
        ...

@dataclass(frozen=True)
class BoundRun:
    """Plan, resolved CLI, staged evidence paths, and built effective calls."""

    plan: FrozenPlan
    binding: CliBinding
    evidence: PreparedEvidence
    calls: tuple[EffectiveCall, ...]

@dataclass(frozen=True)
class Coordinator:
    """Own run concurrency, global stop, retries, and not-started accounting."""

    attempt: AttemptCall
    classifier: OutcomeClassifier
    quota_status: QuotaStatusReader
    waiter: AsyncWaiter
    random_source: RandomSource

    async def run(
        self,
        bound_run: BoundRun,
        evidence: EvidenceStore,
        config: HarnessConfig,
        /,
    ) -> RunRecord:
        """Run bound calls concurrently under one config and evidence adapter."""
        ...
