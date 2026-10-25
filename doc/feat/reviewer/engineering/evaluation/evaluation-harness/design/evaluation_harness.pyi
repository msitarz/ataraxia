# SPDX-License-Identifier: Apache-2.0
"""Exploratory shared boundary for the generic evaluation harness.

This is not an importable runtime module. See ../architecture.md for ownership
and effects; the Work README remains the behavior contract. The supervisor's
outcome and failure types are imported from their active module.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict

from script.process_supervisor import (
    AttemptCancelled,
    AttemptFailureEvidence,
    AttemptRequest,
    AttemptResult,
    DispatchStop,
)

type RunId = str
type CallId = str
type AttemptNumber = int
type EstimateCompatibility = Literal["exact", "approximate", "unknown"]
type EstimateBasis = Literal["supplied_context", "instructions_file"]
type CallState = Literal["not_started", "running", "complete", "failed"]
type RunState = Literal["complete", "incomplete"]
type ControlFlow = Literal["returned", "cancelled", "raised"]
type SettingValue = str | int | float | bool | None

class StrictModel(BaseModel):
    """Raw configuration and persisted records reject extras and coercion."""

    model_config: ConfigDict = ConfigDict(extra="forbid", strict=True, frozen=True)

class DirectoryOption(StrictModel):
    """Directory argument at its original command-line position."""

    position: int
    path: Path

class SeparatorOption(StrictModel):
    """Separator argument at its original command-line position."""

    position: int
    value: str

type OrderedOption = DirectoryOption | SeparatorOption

class HarnessConfig(StrictModel):
    """CLI settings; validators enforce values but perform no I/O or dispatch.

    Zero output bytes disables the cap. Retry limit defaults to zero, and
    nonzero exit retry requires explicit opt-in.
    """

    ordered_options: tuple[OrderedOption, ...]
    models: tuple[str, ...]
    efforts: tuple[str, ...]
    concurrency: int
    output_directory: Path | None
    dry_run: bool
    timeout_seconds: float
    cleanup_timeout_seconds: float
    grace_seconds: float
    output_limit_bytes: int
    retry_limit: int = 0
    retry_nonzero_exit: bool = False
    instructions_file_path: Path | None

class SourceSnapshot(StrictModel):
    """One tracked regular input and its exact frozen bytes."""

    directory_position: int
    repository_path: str
    commit_blob_sha: str
    content_sha256: str
    content: bytes

class InstructionsSnapshot(StrictModel):
    """Tracked instruction input, separate from generic context files."""

    repository_path: str
    commit_blob_sha: str
    content_sha256: str
    content: bytes

@dataclass(frozen=True)
class FrozenInputs:
    """Read-only Git result, including any separately configured instruction."""

    repository_root: Path
    head_commit: str
    sources: tuple[SourceSnapshot, ...]
    instructions_file: InstructionsSnapshot | None

class RepositoryReader(Protocol):
    """Read-only Git and source boundary; it does not compose or plan calls."""

    def freeze(self, config: HarnessConfig, /) -> FrozenInputs:
        """Validate repository inputs and return commit-checked snapshots."""
        ...

class PlannedCall(StrictModel):
    """One ordered matrix position; effective identity awaits runtime binding."""

    position: int
    context_indices: tuple[int, ...]
    model: str
    effort: str
    prompt_sha256: str
    prompt: bytes

class FrozenPlan(StrictModel):
    """Pure composition, configuration, instruction choice, and call matrix.

    A missing instructions file means Codex defaults are preserved; their
    automatic bytes are unavailable to the harness.
    """

    run_id: RunId
    configuration: HarnessConfig
    repository_root: Path
    head_commit: str
    snapshots: tuple[SourceSnapshot, ...]
    boundary_bytes: tuple[bytes, ...]
    instructions_file: InstructionsSnapshot | None
    calls: tuple[PlannedCall, ...]

class PlanBuilder(Protocol):
    """Pure composer and matrix planner; performs no I/O."""

    def plan(self, inputs: FrozenInputs, config: HarnessConfig, /) -> FrozenPlan:
        """Compose exact snapshot bytes and return the complete ordered plan."""
        ...

@dataclass(frozen=True)
class TokenEstimate:
    """Estimate for exact bytes, with an explicit basis and compatibility."""

    model: str
    token_count: int | None
    method: str
    library_version: str | None
    tokenizer_version: str | None
    basis: EstimateBasis
    compatibility: EstimateCompatibility
    diagnostic: str | None

class TokenEstimator(Protocol):
    """Local estimator port; it cannot dispatch model calls."""

    def estimate(
        self, content: bytes, model: str, basis: EstimateBasis, /
    ) -> TokenEstimate:
        """Return an estimate or an explicit unknown value for supplied bytes."""
        ...

@dataclass(frozen=True)
class CallEstimate:
    """Required context estimate and separate optional instruction estimate."""

    position: int
    context: TokenEstimate
    instructions_file: TokenEstimate | None

@dataclass(frozen=True)
class DryRunReport:
    """Plan plus one explicit estimate for each scheduled call."""

    plan: FrozenPlan
    scheduled_call_count: int
    estimates: tuple[CallEstimate, ...]
    cli_binding_known: Literal[False]
    effective_call_identities_known: Literal[False]

class CliBindingResolver(Protocol):
    """Resolve runtime CLI identity and observable settings during execution."""

    def resolve(self, config: HarnessConfig, /) -> CliBinding:
        """Resolve the absolute executable path, version, and effective settings."""
        ...

@dataclass(frozen=True)
class CliBinding:
    """Execution-only binding; dry run deliberately has no instance."""

    executable_path: Path
    cli_version: str | None
    runner_version: str
    effective_settings: tuple[tuple[str, SettingValue], ...]

@dataclass(frozen=True)
class EffectiveCall:
    """One planned call bound to settings, identity, and its supervisor request."""

    run_id: RunId
    call_id: CallId
    planned_call: PlannedCall
    request: AttemptRequest

@dataclass(frozen=True)
class PreparedEvidence:
    """Exclusive run destination with durable plan and staged instructions."""

    output_directory: Path
    plan_artifact: Path
    model_instructions_file: Path | None

class AttemptRequestBuilder(Protocol):
    """Purely build a request from frozen bytes and their staged artifact path."""

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

@dataclass(frozen=True)
class AttemptEvidence:
    """In-memory supervisor outcome associated with its planned call."""

    control_flow: ControlFlow
    outcome: AttemptResult | AttemptCancelled | AttemptFailureEvidence | None
    error_type: str | None
    diagnostic: str | None
    request: AttemptRequest
    started_at_utc: str
    ended_at_utc: str | None
    usage_telemetry: bytes | None

class RunRecord(StrictModel):
    run_id: RunId
    repository_root: str
    head_commit: str
    state: RunState
    runner_version: str
    codex_path: str | None
    cli_version: str | None
    effective_settings: tuple[tuple[str, SettingValue], ...]
    calls: tuple[CallRecord, ...]

class CallRecord(StrictModel):
    run_id: RunId
    call_id: CallId
    position: int
    state: CallState
    source_paths: tuple[str, ...]
    source_sha256: tuple[str, ...]
    boundary_bytes_hex: tuple[str, ...]
    prompt_sha256: str
    model: str
    effort: str
    effective_settings_sha256: str
    attempts: tuple[AttemptRecord, ...]

class AttemptRecord(StrictModel):
    run_id: RunId
    call_id: CallId
    position: int
    attempt_number: AttemptNumber
    control_flow: ControlFlow
    outcome_kind: Literal[
        "completed",
        "timed_out",
        "output_limit_exceeded",
        "infrastructure_failure",
        "cancelled",
        "unexpected_exception",
        "no_observation",
    ]
    started_at_utc: str
    ended_at_utc: str | None
    argv: tuple[str, ...]
    cwd: str
    timeout_seconds: float
    cleanup_timeout_seconds: float
    grace_seconds: float
    output_limit_bytes: int
    elapsed_seconds: float | None
    elapsed_basis: Literal["supervisor_observation", "unavailable"]
    exit_status: int | None
    termination_reason: str | None
    cleanup: CleanupRecord | None
    stdout_artifact: str | None
    stderr_artifact: str | None
    usage_telemetry: bytes | None
    error_type: str | None
    diagnostic: str | None

class SignalRecord(StrictModel):
    """Serialized OS signal observation retained by the supervisor."""

    signal: Literal["SIGTERM", "SIGKILL"]
    outcome: Literal["sent", "no_target", "failed", "unknown"]
    diagnostic: str | None

class CleanupRecord(StrictModel):
    """Structured persistence projection of supervisor cleanup evidence."""

    process: Literal["not_started", "owned", "acquisition_uncertain"]
    signals: tuple[SignalRecord, ...]
    direct_wait: Literal["not_started", "reaped", "failed", "expired", "unknown"]
    wait_diagnostic: str | None

class EvidenceStore(Protocol):
    """Exclusive, append-only run evidence boundary."""

    def create(self, output_directory: Path, plan: FrozenPlan, /) -> PreparedEvidence:
        """Exclusively create run storage and persist plan/instructions pre-dispatch.

        Returns paths to the durable plan and staged model instruction file.
        No supervisor process may launch before this call succeeds.
        """
        ...

    def record_attempt(
        self,
        run_id: RunId,
        call_id: CallId,
        position: int,
        attempt_number: AttemptNumber,
        evidence: AttemptEvidence,
        /,
    ) -> AttemptRecord:
        """Persist an explicitly associated attempt without replacing evidence."""
        ...

    def finalize(self, record: RunRecord, /) -> None:
        """Persist truthful final accounting; a failure leaves the run incomplete."""
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

@dataclass(frozen=True)
class Coordinator:
    """Own run concurrency, global stop, retries, and not-started accounting."""

    attempt: AttemptCall

    async def run(
        self,
        bound_run: BoundRun,
        evidence: EvidenceStore,
        config: HarnessConfig,
        /,
    ) -> RunRecord:
        """Run bound calls concurrently under one config and evidence adapter."""
        ...

@dataclass(frozen=True)
class BoundRun:
    """Plan, resolved CLI, staged evidence paths, and built effective calls."""

    plan: FrozenPlan
    binding: CliBinding
    evidence: PreparedEvidence
    calls: tuple[EffectiveCall, ...]

@dataclass(frozen=True)
class Composition:
    """Concrete adapters assembled once by the CLI entry point."""

    repository: RepositoryReader
    planner: PlanBuilder
    estimator: TokenEstimator
    binding_resolver: CliBindingResolver
    request_builder: AttemptRequestBuilder
    coordinator: Coordinator
    evidence: EvidenceStore

    async def execute(self, config: HarnessConfig, /) -> DryRunReport | RunRecord:
        """Plan and estimate; execution persists plan/instructions before dispatch.

        Dry run returns before CLI binding, evidence creation, and request
        construction. Execution resolves binding, creates evidence, builds
        bound calls, then passes the same evidence adapter to the coordinator.
        """
        ...
