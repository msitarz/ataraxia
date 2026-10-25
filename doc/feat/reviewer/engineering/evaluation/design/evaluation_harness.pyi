# SPDX-License-Identifier: Apache-2.0
"""Proposed public types for the experimental Evaluation harness.

This file is a design artifact, not an importable implementation. The protocol
owns call inventories, fixed budgets, and reporting rules. Cross-field
invariants below are required contracts for a future implementation.
"""

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, NamedTuple, Protocol

from script.process_supervisor import (
    AttemptFailureEvidence,
    AttemptObservation,
    AttemptRequest,
    AttemptResult,
    AttemptRunner,
    DispatchStop,
)

type Strategy = Literal["A", "B", "C"]
type Effort = Literal["none", "low", "medium", "high"]
type Judgment = Literal["PASS", "VIOLATION", "NOT_APPLICABLE", "UNCERTAIN"]
type CallState = Literal["valid", "failed", "incomplete", "not_started"]
type StopKind = Literal[
    "cancelled",
    "unsafe_cleanup",
    "boundary_refused",
    "resource_exhausted",
    "accounting_invalid",
    "evidence_failure",
    "condition_failure_limit",
    "external_stop",
]

class AssessmentKey(NamedTuple):
    """One exact rule/file/function subject; all three fields form its key."""

    rule_id: str
    file_id: str
    qualified_function_name: str

@dataclass(frozen=True)
class ConditionId:
    """One frozen strategy, effort, and repetition block."""

    strategy: Strategy
    effort: Effort
    repetition: int

@dataclass(frozen=True)
class PublicInput:
    """One exact public input byte sequence and its frozen identity."""

    reference: Path
    content: bytes
    digest: str

@dataclass(frozen=True)
class InputBinding:
    """Exact public model inputs and source/configuration provenance."""

    prepared_input_id: str
    prompt: PublicInput
    sources: tuple[PublicInput, ...]
    instruction: PublicInput
    configuration: PublicInput
    surfaced_tools_digest: str

@dataclass(frozen=True)
class SessionIdentity:
    """Trusted identity; condition effort and requested runtime effort must agree."""

    session_id: str
    condition: ConditionId
    input: InputBinding
    model_id: str
    codex_executable: Path
    codex_version: str
    requested_effort: Effort

    def __post_init__(self) -> None: ...

@dataclass(frozen=True)
class PreparationBinding:
    """Exact authorized calibration identity bound to a planned condition."""

    condition: ConditionId
    codex_executable: Path
    codex_version: str
    model_id: str
    preparation_input_digest: str
    configuration_digest: str
    surfaced_tools_digest: str

@dataclass(frozen=True)
class PlannedCall:
    """One ordered session and its exact assessment denominator."""

    identity: SessionIdentity
    expected_keys: frozenset[AssessmentKey]
    timeout_seconds: float
    cleanup_timeout_seconds: float
    output_limit_bytes: int

@dataclass(frozen=True)
class FrozenRun:
    """Unique frozen plan; concurrency defaults to one and excludes bool/nonpositive."""

    calls: tuple[PlannedCall, ...]
    plan_digest: str
    preparation_bindings: tuple[PreparationBinding, ...]
    max_concurrency: int = 1

    def __post_init__(self) -> None:
        """Reject duplicate identities and mismatched condition bindings."""
        ...

@dataclass(frozen=True)
class ViolationEvidence:
    """Source location, quote, and consequence supporting a VIOLATION."""

    file_id: str
    start_line: int
    end_line: int
    quotation: str
    consequence: str

@dataclass(frozen=True)
class Assessment:
    """One judgment; violations require at least one concrete evidence item."""

    key: AssessmentKey
    judgment: Judgment
    explanation: str
    violation_evidence: tuple[ViolationEvidence, ...]

@dataclass(frozen=True)
class ModelResponse:
    """Internal decoded schema shape; callers validate the original response bytes."""

    session_id: str
    strategy: Strategy
    prepared_input_id: str
    complete: bool
    assessments: tuple[Assessment, ...]

@dataclass(frozen=True)
class ValidatedResult:
    """Identity-bound complete public output, with duplicate checks done first."""

    identity: SessionIdentity
    assessments: Mapping[AssessmentKey, Assessment]
    raw_output: bytes

@dataclass(frozen=True)
class Usage:
    """Raw provider categories; unavailable categories remain None."""

    input_tokens: int | None
    cached_input_tokens: int | None
    cache_write_input_tokens: int | None
    output_tokens: int | None
    reasoning_output_tokens: int | None

@dataclass(frozen=True)
class AttemptCancellation:
    """Persistable cancellation snapshot; original cancellation is re-raised."""

    observation: AttemptObservation
    exit_status: int | None

@dataclass(frozen=True)
class AttemptException:
    """Persistable escaping-error snapshot without replacing the original error."""

    exception_type: str
    diagnostic: str
    supervisor_evidence: AttemptFailureEvidence | None

type AttemptOutcome = AttemptResult | AttemptCancellation | AttemptException

@dataclass(frozen=True)
class AttemptEvidence:
    """One attempt's outcome, argv, usage, timing, and frozen session provenance."""

    identity: SessionIdentity
    attempt_number: int
    argv: tuple[str, ...]
    outcome: AttemptOutcome
    usage: Usage | None
    elapsed_seconds: float | None
    started_utc: str
    completed_utc: str

@dataclass(frozen=True)
class CallTerminal:
    """Exactly one final state for every planned call, including not-started."""

    identity: SessionIdentity
    state: CallState
    reason: str | None

@dataclass(frozen=True)
class StopRecord:
    """Latched stop reason and evidence persistence status."""

    kind: StopKind
    detail: str
    evidence_complete: bool

@dataclass(frozen=True)
class RunSummary:
    """Observed capacity utilization and distinct wall/process durations."""

    configured_concurrency: int
    maximum_active_attempts: int
    mean_active_attempts: float
    wall_seconds_through_cleanup: float
    summed_attempt_seconds: float
    started_utc: str
    completed_utc: str
    planned_calls: int
    valid_calls: int
    failed_calls: int
    incomplete_calls: int
    not_started_calls: int

@dataclass(frozen=True)
class RunEvidence:
    """Public completion view; private labels and prior answers are excluded."""

    calls: tuple[CallTerminal, ...]
    stop: StopRecord | None
    summary: RunSummary
    evidence_complete: bool

class EvidenceSink(Protocol):
    """Persist public artifacts append-only; implementations cannot accept labels."""

    def record_plan(self, run: FrozenRun) -> None: ...
    def record_attempt(self, evidence: AttemptEvidence) -> None: ...
    def record_result(self, result: ValidatedResult) -> None: ...
    def record_call(self, terminal: CallTerminal) -> None: ...
    def record_stop(self, stop: StopRecord) -> None: ...
    def record_summary(self, summary: RunSummary) -> None: ...

@dataclass(frozen=True)
class Estimate:
    """Per-call conservative allowance; unknown measured usage is never zero."""

    raw_input_tokens: int
    raw_output_tokens: int
    evidence_bytes: int
    elapsed_seconds: float
    method: str
    method_version: str

@dataclass(frozen=True)
class CallEstimate:
    """Per-call estimate bound to the exact planned session identity."""

    session_id: str
    estimate: Estimate

@dataclass(frozen=True)
class ResourceReservation:
    """Lease held from atomic dispatch through completed cleanup and settlement."""

    session_id: str
    attempt_number: int
    reserved_input_tokens: int
    reserved_output_tokens: int
    reserved_evidence_bytes: int
    reserved_elapsed_seconds: float
    slot: int

@dataclass(frozen=True)
class ResourceSettlement:
    """Observed raw use; missing usage consumes its conservative reservation."""

    reservation: ResourceReservation
    usage: Usage | None
    evidence_bytes: int
    elapsed_seconds: float
    cleanup_settled: bool

class ResourceLedger(Protocol):
    """Atomically enforce stop, concurrency, and shared resource reservations."""

    def configure(
        self, run: FrozenRun, bounds: RunBounds, base: AcceptedPreflight
    ) -> None: ...
    async def reserve_dispatch(
        self,
        stop: StopLatch,
        call: PlannedCall,
        attempt_number: int,
        estimate: Estimate,
        remaining: tuple[PlannedCall, ...],
    ) -> ResourceReservation | None: ...
    async def settle(self, settlement: ResourceSettlement) -> None: ...

type VerificationOutcome = Literal["confirmed", "disclosed_unavailable", "breached"]

@dataclass(frozen=True)
class VerificationObservation:
    """Method and actual observation for one invocation boundary."""

    area: Literal[
        "model_binding",
        "effective_effort",
        "source_readonly",
        "allowed_inputs",
        "private_answer_separation",
        "runtime_context",
    ]
    method: str
    evidence_reference: str
    observed_digest: str | None
    outcome: VerificationOutcome
    summary: str

@dataclass(frozen=True)
class PreparationEvidence:
    """Retained binding and boundary evidence from authorized preparation."""

    binding: PreparationBinding
    effective_effort: Effort | None
    observations: tuple[VerificationObservation, ...]

@dataclass(frozen=True)
class VerifiedCondition:
    """Binding must match plan/condition; required proof must be confirmed."""

    condition: ConditionId
    plan_digest: str
    binding: PreparationBinding
    requested_effort: Effort
    effective_effort: Effort
    observations: tuple[VerificationObservation, ...]

    def __post_init__(self) -> None: ...

@dataclass(frozen=True)
class ConditionBindingGap:
    """Binding must match plan/condition; only this unverified effort is skipped."""

    condition: ConditionId
    plan_digest: str
    binding: PreparationBinding
    requested_effort: Effort
    reason: str
    observations: tuple[VerificationObservation, ...]

    def __post_init__(self) -> None: ...

@dataclass(frozen=True)
class ProtectionNotEstablished:
    """Refuse scope while required source or answer-boundary proof is absent."""

    condition: ConditionId
    plan_digest: str
    binding: PreparationBinding
    scope: Literal["condition", "run"]
    reason: str
    observations: tuple[VerificationObservation, ...]

    def __post_init__(self) -> None: ...

@dataclass(frozen=True)
class GlobalProtectionBreach:
    """Detected shared source/label/prior-answer failure that stops all dispatch."""

    condition: ConditionId
    plan_digest: str
    binding: PreparationBinding
    reason: str
    observations: tuple[VerificationObservation, ...]

    def __post_init__(self) -> None: ...

type ConditionVerification = (
    VerifiedCondition
    | ConditionBindingGap
    | ProtectionNotEstablished
    | GlobalProtectionBreach
)

class StopLatch(Protocol):
    """Latch the first global stop before evidence persistence is attempted."""

    def request_stop(self, kind: StopKind, detail: str) -> None: ...
    def is_stopped(self) -> bool: ...

@dataclass(frozen=True)
class HarnessPorts:
    """Effects supplied by composition around existing supervisor contracts."""

    run_attempt: AttemptRunner
    call_supervisor: Callable[
        [AttemptRequest, AttemptRunner, DispatchStop], Awaitable[AttemptResult]
    ]
    evidence: EvidenceSink
    resources: ResourceLedger
    stop: StopLatch
    clock: Clock

class Clock(Protocol):
    """Clock for monotonic run bounds and UTC provenance timestamps."""

    def monotonic(self) -> float: ...
    def utc_timestamp(self) -> str: ...

@dataclass(frozen=True)
class RunBounds:
    """Protocol-supplied raw ceilings; unknown values are never zero-valued."""

    trial_deadline_seconds: float
    evidence_limit_bytes: int
    per_attempt_input_token_ceiling: int
    per_attempt_output_token_ceiling: int
    aggregate_raw_token_limit: int
    attempt_limit: int

@dataclass(frozen=True)
class AcceptedPreflight:
    """Receipt must exactly match the supplied plan, bounds, and concurrency."""

    plan_digest: str
    bounds: RunBounds
    max_concurrency: int
    reservations: tuple[CallEstimate, ...]

@dataclass(frozen=True)
class PreflightRefusal:
    """No-launch result with reasons retained for owner review."""

    plan_digest: str
    bounds: RunBounds
    max_concurrency: int
    refusal_reasons: tuple[str, ...]

type PreflightResult = AcceptedPreflight | PreflightRefusal

@dataclass(frozen=True)
class OutputRefusal:
    """Malformed, mismatched, or incomplete raw response; never retryable."""

    reason: Literal[
        "malformed_json",
        "invalid_schema",
        "identity_mismatch",
        "incomplete",
        "duplicate_assessment",
        "foreign_assessment",
        "missing_assessment",
        "invalid_evidence",
    ]
    diagnostic: str

type OutputValidation = ValidatedResult | OutputRefusal

def resolve_codex(executable: str) -> tuple[Path, str]:
    """Resolve executable and version; failure refuses plan creation."""
    ...

def verify_condition(
    condition: ConditionId,
    plan: FrozenRun,
    evidence: PreparationEvidence,
) -> ConditionVerification:
    """Compare retained preparation evidence; this function never launches a call."""
    ...

def preflight(run: FrozenRun, bounds: RunBounds) -> PreflightResult:
    """Validate plan, concurrency, call identities, keys, estimates, and base budget."""
    ...

def validate_output(
    call: PlannedCall,
    raw_output: bytes,
) -> OutputValidation:
    """Decode and validate authoritative bytes before exact-key mapping."""
    ...

async def run_plan(
    run: FrozenRun,
    verifications: tuple[ConditionVerification, ...],
    preflight_result: AcceptedPreflight,
    ports: HarnessPorts,
) -> RunEvidence:
    """Check receipt/verification identities, then execute eligible blocks only."""
    ...

def build_attempt_request(call: PlannedCall) -> AttemptRequest:
    """Build one request using only frozen public inputs and invocation settings."""
    ...
