# SPDX-License-Identifier: Apache-2.0
"""Historical core model sketch with proposed AC-6/AC-7 extensions.

The pre-existing value declarations correspond to the current
``script/eval/model.py`` runtime contract. Quota, classification, and wait
declarations are proposals only: they are not runtime types or an active
shadowing interface. Review and migrate accepted fields into that one runtime
module before implementation.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from script.process_supervisor import (
    AttemptCancelled,
    AttemptFailureEvidence,
    AttemptRequest,
    AttemptResult,
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
type RetryClass = Literal["infrastructure", "quota", "capacity", "other", "unknown"]
type NoResultBasis = Literal["confident_absence", "present_or_unknown"]
type QuotaState = Literal["available", "exhausted", "unknown", "unavailable"]
type WaitEnd = Literal[
    "reset_reached", "delay_elapsed", "bound", "cancelled", "stop", "unknown"
]
type WaitEventKind = Literal["started", "recheck", "finished"]
type WaitId = str

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
    """CLI settings; validation does not perform I/O or dispatch.

    Proposed AC-6/AC-7 fields below require finite positive supplied wait and
    backoff durations, a cap not below its base, and nonnegative retry
    allowances before dispatch. The capacity allowance defaults to zero and
    quota waiting defaults off; a quota wait limit is optional.
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
    quota_wait_enabled: bool = False
    quota_wait_limit_seconds: float | None = None
    capacity_retry_limit: int = 0
    capacity_backoff_base_seconds: float | None = None
    capacity_backoff_cap_seconds: float | None = None
    instructions_file_path: Path | None

class QuotaWindowObservation(StrictModel):
    """One window's source-backed result; unknown or unavailable stays explicit."""

    state: QuotaState
    reset_at_utc: str | None
    source: str | None
    diagnostic: str | None

class QuotaObservation(StrictModel):
    """Both windows are always represented, even when either is unavailable."""

    observed_at_utc: str
    five_hour: QuotaWindowObservation
    weekly: QuotaWindowObservation
    diagnostic: str | None

class RetryAssessment(StrictModel):
    """Classification and no-result evidence; never inferred from answers."""

    retry_class: RetryClass
    classification_basis: str | None
    no_result_basis: NoResultBasis
    diagnostic: str | None

class QuotaWaitContext(StrictModel):
    """Quota trigger and cumulative bound accounting, known at wait start."""

    kind: Literal["quota"]
    trigger_call_id: CallId
    trigger_attempt_number: AttemptNumber
    cumulative_waited_before_seconds: float
    wait_limit_seconds: float | None
    quota_observation: QuotaObservation
    selected_reset_at_utc: str

class CapacityWaitContext(StrictModel):
    """Call and retry parameters persisted before a capacity sleep begins."""

    kind: Literal["capacity"]
    call_id: CallId
    failed_attempt_number: AttemptNumber
    retry_index: int
    base_seconds: float
    cap_seconds: float
    jitter_bound_seconds: float
    sampled_seconds: float

type WaitContext = QuotaWaitContext | CapacityWaitContext

class WaitRecord(StrictModel):
    """One final summary joined to its live events through stable context ID."""

    wait_id: WaitId
    context: WaitContext
    started_at_utc: str
    ended_at_utc: str | None
    elapsed_seconds: float | None
    end: WaitEnd
    diagnostic: str | None

class WaitEvent(StrictModel):
    """Append-only event persisted when a wait starts and while it proceeds."""

    run_id: RunId
    wait_id: WaitId
    context: WaitContext
    kind: WaitEventKind
    observed_at_utc: str
    elapsed_seconds: float
    quota_observation: QuotaObservation | None
    end: WaitEnd | None
    diagnostic: str | None

class SourceSnapshot(StrictModel):
    """One tracked regular context input and its exact frozen bytes."""

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
    """Read-only Git result, including any configured instruction snapshot."""

    repository_root: Path
    head_commit: str
    sources: tuple[SourceSnapshot, ...]
    instructions_file: InstructionsSnapshot | None

class PlannedCall(StrictModel):
    """One ordered matrix position; identity awaits runtime binding."""

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

@dataclass(frozen=True)
class TokenEstimate:
    """Estimate with a separately labeled input basis and compatibility."""

    model: str
    token_count: int | None
    method: str
    library_version: str | None
    tokenizer_version: str | None
    basis: EstimateBasis
    compatibility: EstimateCompatibility
    diagnostic: str | None

@dataclass(frozen=True)
class CallEstimate:
    """Required context estimate and optional instruction-file estimate."""

    position: int
    context: TokenEstimate
    instructions_file: TokenEstimate | None

@dataclass(frozen=True)
class DryRunReport:
    """Plan and one estimate for every scheduled call."""

    plan: FrozenPlan
    scheduled_call_count: int
    estimates: tuple[CallEstimate, ...]
    cli_binding_known: Literal[False]
    effective_call_identities_known: Literal[False]

@dataclass(frozen=True)
class PreparedEvidence:
    """Exclusive run destination with durable plan and staged instructions."""

    output_directory: Path
    plan_artifact: Path
    model_instructions_file: Path | None

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
    waits: tuple[WaitRecord, ...]

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
    retry_assessment: RetryAssessment | None

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
