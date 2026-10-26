# SPDX-License-Identifier: Apache-2.0
"""Shared immutable values and persisted boundary records."""

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal, NewType

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
type AttemptOutcomeKind = Literal[
    "completed",
    "timed_out",
    "output_limit_exceeded",
    "infrastructure_failure",
    "cancelled",
    "unexpected_exception",
    "no_observation",
]
type SettingValue = str | int | float | bool | None
type PositiveSeconds = Annotated[float, Field(gt=0, allow_inf_nan=False)]
type NonnegativeSeconds = Annotated[float, Field(ge=0, allow_inf_nan=False)]
type NonnegativeBytes = Annotated[int, Field(ge=0)]
type NonnegativeIndex = Annotated[int, Field(ge=0)]
type RetryClass = Literal["infrastructure", "quota", "capacity", "other", "unknown"]
type NoResultBasis = Literal["confident_absence", "present_or_unknown"]
type QuotaState = Literal["available", "exhausted", "unknown", "unavailable"]
type WaitEnd = Literal[
    "quota_available", "delay_elapsed", "bound", "cancelled", "stop", "unknown"
]
type WaitEventKind = Literal["started", "recheck", "finished"]
type WaitId = str
QuotaProviderId = NewType("QuotaProviderId", str)
QuotaAllowanceId = NewType("QuotaAllowanceId", str)
QuotaWindowId = NewType("QuotaWindowId", str)
QuotaProbeId = NewType("QuotaProbeId", str)
type QuotaProbeReason = Literal["periodic", "reset_hint"]
type QuotaProbeCancelCause = Literal["cancelled", "stop", "superseded"]


class StrictModel(BaseModel):
    """Raw configuration and persisted records reject extras and coercion."""

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=True,
        ser_json_bytes="base64",
        val_json_bytes="base64",
    )


class DirectoryOption(StrictModel):
    """Directory argument at its original command-line position."""

    position: int = Field(ge=0)
    path: Path


class SeparatorOption(StrictModel):
    """Separator argument at its original command-line position."""

    position: int = Field(ge=0)
    value: str


type OrderedOption = DirectoryOption | SeparatorOption


class HarnessConfig(StrictModel):
    """CLI settings; validation does not perform I/O or dispatch.

    Quota waiting and capacity retries default off. Enabled quota waiting
    rejects a zero probe budget; ``None`` leaves the harness probe count
    uncapped. Positive capacity retry allowances require finite positive
    backoff base and cap values, with the cap at least as large as the base.
    Progress refresh interval and any supplied wait/backoff durations are
    finite and positive.
    """

    ordered_options: tuple[OrderedOption, ...]
    models: tuple[str, ...]
    efforts: tuple[str, ...]
    concurrency: int = Field(gt=0)
    output_directory: Path | None
    dry_run: bool
    timeout_seconds: PositiveSeconds
    cleanup_timeout_seconds: PositiveSeconds
    grace_seconds: NonnegativeSeconds
    output_limit_bytes: NonnegativeBytes
    quiet: bool = False
    progress_interval_seconds: PositiveSeconds = 1.0
    retry_limit: int = Field(default=0, ge=0)
    retry_nonzero_exit: bool = False
    quota_wait_enabled: bool = False
    quota_wait_limit_seconds: PositiveSeconds | None = None
    quota_poll_interval_seconds: PositiveSeconds = 60.0
    quota_probe_budget: NonnegativeIndex | None = None
    capacity_retry_limit: int = Field(default=0, ge=0)
    capacity_backoff_base_seconds: PositiveSeconds | None = None
    capacity_backoff_cap_seconds: PositiveSeconds | None = None
    instructions_file_path: Path | None

    @model_validator(mode="after")
    def validate_relationships(self) -> HarnessConfig:
        """Enforce config relationships that do not require external effects.

        Returns:
            The validated configuration.

        Raises:
            ValueError: A matrix dimension, output destination, or deadline is invalid.
        """
        positions = tuple(option.position for option in self.ordered_options)
        if positions != tuple(sorted(set(positions))):
            raise ValueError("ordered option positions must be unique and increasing")
        for index, option in enumerate(self.ordered_options):
            if not isinstance(option, SeparatorOption):
                continue
            if (
                index == 0
                or index == len(self.ordered_options) - 1
                or not isinstance(self.ordered_options[index - 1], DirectoryOption)
                or not isinstance(self.ordered_options[index + 1], DirectoryOption)
            ):
                raise ValueError("separators must occur singly between directories")
            _validate_separator_escapes(option.value)
        has_directory = any(
            isinstance(option, DirectoryOption) for option in self.ordered_options
        )
        if not has_directory:
            raise ValueError("at least one directory is required")
        if not self.models:
            raise ValueError("at least one model is required")
        if not self.efforts:
            raise ValueError("at least one effort is required")
        if not self.dry_run and self.output_directory is None:
            raise ValueError("execution requires an output directory")
        if self.grace_seconds >= self.cleanup_timeout_seconds:
            raise ValueError("grace_seconds must be less than cleanup_timeout_seconds")
        return self

    @model_validator(mode="after")
    def validate_runner_relationships(self) -> HarnessConfig:
        """Enforce quota and capacity relationships before dispatch.

        Returns:
            The validated configuration.

        Raises:
            ValueError: A quota budget or capacity retry relationship is invalid.
        """
        if self.quota_wait_enabled and self.quota_probe_budget == 0:
            raise ValueError("enabled quota waiting requires a positive probe budget")
        if self.capacity_retry_limit > 0 and (
            self.capacity_backoff_base_seconds is None
            or self.capacity_backoff_cap_seconds is None
        ):
            raise ValueError("capacity retries require backoff base and cap durations")
        if (
            self.capacity_backoff_base_seconds is not None
            and self.capacity_backoff_cap_seconds is not None
            and self.capacity_backoff_cap_seconds < self.capacity_backoff_base_seconds
        ):
            raise ValueError("capacity backoff cap must be at least its base")
        return self


class SourceSnapshot(StrictModel):
    """One tracked regular context input and its exact frozen bytes."""

    directory_position: int = Field(ge=0)
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

    position: int = Field(ge=0)
    context_indices: tuple[NonnegativeIndex, ...]
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
    """Estimate with input basis, compatibility, and any approximation diagnostic."""

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


class QuotaScope(StrictModel):
    """Opaque provider and allowance identity safe to retain in evidence."""

    provider_id: QuotaProviderId
    allowance_id: QuotaAllowanceId


class QuotaWindowObservation(StrictModel):
    """One provider-specific window with source provenance and optional usage."""

    window_id: QuotaWindowId
    state: QuotaState
    usage_percent: float | None
    reset_at_utc: str | None
    source_observed_at_utc: str | None
    source_sequence: int | None
    source: str | None
    diagnostic: str | None


class QuotaObservation(StrictModel):
    """Provider-neutral windows from one source snapshot and verified scope."""

    scope: QuotaScope | None
    read_at_utc: str
    source_coordinate: str | None
    windows: tuple[QuotaWindowObservation, ...]
    diagnostic: str | None


class RetryAssessment(StrictModel):
    """Runner-owned classification and explicit no-result basis."""

    retry_class: RetryClass
    classification_basis: str | None
    no_result_basis: NoResultBasis
    diagnostic: str | None


class QuotaWaitContext(StrictModel):
    """One global quota pause and its scoped provider observation."""

    kind: Literal["quota"]
    trigger_call_id: CallId
    trigger_attempt_number: AttemptNumber
    cumulative_waited_before_seconds: NonnegativeSeconds
    wait_limit_seconds: PositiveSeconds | None
    quota_observation: QuotaObservation
    selected_reset_at_utc: str | None


class CapacityWaitContext(StrictModel):
    """One call-local capacity retry delay and its sampled bounds."""

    kind: Literal["capacity"]
    call_id: CallId
    failed_attempt_number: AttemptNumber
    retry_index: int
    base_seconds: PositiveSeconds
    cap_seconds: PositiveSeconds
    jitter_bound_seconds: NonnegativeSeconds
    sampled_seconds: NonnegativeSeconds


type WaitContext = QuotaWaitContext | CapacityWaitContext


class QuotaProbeSchedule(StrictModel):
    """Durable cadence decision before a quota check becomes due."""

    run_id: RunId
    probe_id: QuotaProbeId
    scope: QuotaScope
    reason: QuotaProbeReason
    created_at_utc: str
    due_at_utc: str
    interval_seconds: PositiveSeconds
    reset_hint_at_utc: str | None


class QuotaProbeRequest(StrictModel):
    """One dispatched quota check associated with its current pause."""

    schedule: QuotaProbeSchedule
    pause_wait_id: WaitId | None
    poll_started_at_utc: str
    scheduled_wait_seconds: NonnegativeSeconds
    scheduled_wait_elapsed_basis: Literal["monotonic"]


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


type ProcessEvidence = AttemptEvidence


@dataclass(frozen=True)
class QuotaProbeEvidence:
    """Quota assessment composed with ephemeral supervisor process evidence."""

    request: QuotaProbeRequest
    process: ProcessEvidence
    quota_state: QuotaState
    observation: QuotaObservation | None
    classification_basis: str | None


class QuotaProbeScheduled(StrictModel):
    """Append-only cadence decision; it represents no launched process."""

    kind: Literal["scheduled"]
    schedule: QuotaProbeSchedule


class QuotaProbeStarted(StrictModel):
    """Actual dispatch event written before supervisor invocation."""

    kind: Literal["started"]
    request: QuotaProbeRequest


class QuotaProbeCancelled(StrictModel):
    """Scheduled wait ended before dispatch, without a process record."""

    kind: Literal["cancelled"]
    schedule: QuotaProbeSchedule
    cause: QuotaProbeCancelCause
    ended_at_utc: str
    elapsed_seconds: NonnegativeSeconds
    elapsed_basis: Literal["monotonic"]


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


class ProcessRecord(StrictModel):
    """Serializable projection shared by evaluation attempts and quota probes."""

    control_flow: ControlFlow
    outcome_kind: Literal[
        "completed",
        "timed_out",
        "output_limit_exceeded",
        "infrastructure_failure",
        "cancelled",
        "unexpected_exception",
        "no_observation",
        "not_started",
    ]
    started_at_utc: str
    ended_at_utc: str | None
    argv: tuple[str, ...]
    cwd: str
    timeout_seconds: PositiveSeconds
    cleanup_timeout_seconds: PositiveSeconds
    grace_seconds: NonnegativeSeconds
    output_limit_bytes: NonnegativeBytes
    elapsed_seconds: NonnegativeSeconds | None
    elapsed_basis: Literal["supervisor_observation", "unavailable"]
    exit_status: int | None
    termination_reason: str | None
    cleanup: CleanupRecord | None
    stdout_artifact: str | None
    stderr_artifact: str | None
    usage_telemetry: bytes | None
    error_type: str | None
    diagnostic: str | None


class AttemptRecord(ProcessRecord):
    """Shared process projection with evaluation identity and classification."""

    run_id: RunId
    call_id: CallId
    position: int = Field(ge=0)
    attempt_number: AttemptNumber = Field(ge=1)
    outcome_kind: AttemptOutcomeKind
    retry_assessment: RetryAssessment | None = None


class QuotaProbeRecord(ProcessRecord):
    """Shared process projection with quota probe identity and assessment."""

    request: QuotaProbeRequest
    quota_state: QuotaState
    observation: QuotaObservation | None
    classification_basis: str | None


class QuotaProbeSettled(StrictModel):
    """Persisted process projection written before quota resumption."""

    kind: Literal["settled"]
    record: QuotaProbeRecord


type QuotaProbeLifecycleInput = (
    QuotaProbeScheduled | QuotaProbeStarted | QuotaProbeCancelled
)
type QuotaProbeEvent = QuotaProbeLifecycleInput | QuotaProbeSettled


class QuotaTelemetryEvent(StrictModel):
    """Provider-neutral observation associated with a settled evaluation attempt."""

    run_id: RunId
    call_id: CallId
    attempt_number: AttemptNumber
    observation: QuotaObservation


class WaitRecord(StrictModel):
    """Final wait summary joined to live events through a stable ID."""

    wait_id: WaitId
    context: WaitContext
    started_at_utc: str
    ended_at_utc: str | None
    elapsed_seconds: NonnegativeSeconds | None
    end: WaitEnd
    diagnostic: str | None


class WaitEvent(StrictModel):
    """Append-only event persisted as a wait starts and proceeds."""

    run_id: RunId
    wait_id: WaitId
    context: WaitContext
    kind: WaitEventKind
    observed_at_utc: str
    elapsed_seconds: NonnegativeSeconds
    quota_observation: QuotaObservation | None
    end: WaitEnd | None
    diagnostic: str | None


class CallRecord(StrictModel):
    """Persisted state and source identity for one scheduled call."""

    run_id: RunId
    call_id: CallId
    position: int = Field(ge=0)
    state: CallState
    source_paths: tuple[str, ...]
    source_sha256: tuple[str, ...]
    boundary_bytes_hex: tuple[str, ...]
    prompt_sha256: str
    model: str
    effort: str
    effective_settings_sha256: str
    attempts: tuple[AttemptRecord, ...]


class RunRecord(StrictModel):
    """Persisted summary of one harness run."""

    run_id: RunId
    repository_root: str
    head_commit: str
    state: RunState
    runner_version: str
    codex_path: str | None
    cli_version: str | None
    effective_settings: tuple[tuple[str, SettingValue], ...]
    calls: tuple[CallRecord, ...]
    waits: tuple[WaitRecord, ...] = ()


def _validate_separator_escapes(value: str) -> None:
    """Reject unsupported escapes without decoding the separator value.

    Raises:
        ValueError: The separator includes an unknown or incomplete escape.
    """
    supported = {"n", "r", "t", "\\"}
    index = 0
    while index < len(value):
        if value[index] != "\\":
            index += 1
            continue
        if index + 1 == len(value) or value[index + 1] not in supported:
            raise ValueError("separator contains an unknown or dangling escape")
        index += 2
