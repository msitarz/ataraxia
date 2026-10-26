# SPDX-License-Identifier: Apache-2.0
"""Consumer-owned values and ports used by dispatch and its adapters."""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from script.eval.model import (
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
from script.process_supervisor import AttemptRequest, AttemptResult, DispatchStop

class CliBinding(Protocol):
    """Execution-only CLI identity; dry run deliberately has no binding."""

    executable_path: Path
    cli_version: str | None
    runner_version: str
    effective_settings: tuple[tuple[str, SettingValue], ...]

class CliBindingResolver(Protocol):
    """Resolve CLI identity only on the execution branch."""

    def resolve(self, config: HarnessConfig, /) -> CliBinding: ...

class AttemptRequestBuilder(Protocol):
    """Build an effective call from frozen inputs and staged evidence paths."""

    def build(
        self,
        plan: FrozenPlan,
        call: PlannedCall,
        binding: CliBinding,
        evidence: PreparedEvidence,
        config: HarnessConfig,
        /,
    ) -> EffectiveCall: ...

class AttemptCall(Protocol):
    """Invoke exactly one request through the existing supervisor."""

    async def __call__(
        self, request: AttemptRequest, stop_dispatch: DispatchStop, /
    ) -> AttemptResult: ...

class OutcomeClassifier(Protocol):
    """Classify settled supervisor evidence without reading semantic answers."""

    def assess(self, evidence: AttemptEvidence, /) -> RetryAssessment: ...

class QuotaStatusReader(Protocol):
    """Return both source-backed quota windows or explicit unknown observations."""

    async def read(self) -> QuotaObservation: ...

class AsyncWaiter(Protocol):
    """Inject UTC and monotonic clocks plus cancellable async waiting."""

    def utc_now(self) -> str: ...
    def monotonic(self) -> float: ...
    async def sleep(self, seconds: float, /) -> None: ...

class RandomSource(Protocol):
    """Inject the capacity policy's full-jitter sample."""

    def uniform(self, lower: float, upper: float, /) -> float: ...

class Runtime(AsyncWaiter, RandomSource, Protocol):
    """Combined runtime dependency used by the coordinator."""

@dataclass(frozen=True)
class EffectiveCall:
    """One frozen planned position bound to its supervisor request."""

    run_id: RunId
    call_id: CallId
    planned_call: PlannedCall
    request: AttemptRequest

@dataclass(frozen=True)
class BoundRun:
    """Execution binding and calls assembled before coordinator dispatch."""

    plan: FrozenPlan
    binding: CliBinding
    evidence: PreparedEvidence
    calls: tuple[EffectiveCall, ...]
