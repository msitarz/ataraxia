# SPDX-License-Identifier: Apache-2.0
"""Historical core snapshot with proposal-only runner model extensions.

The pre-existing value declarations correspond to the current
``script/eval/model.py`` runtime contract. Quota, classification, and wait
and probe-lifecycle declarations, plus the shared ``ProcessRecord`` base, are
proposals for AC-6 through AC-8: they are not runtime types or an active
shadowing interface. Review and migrate accepted fields into that one runtime
module before implementation. ``AttemptEvidence`` retains its current field
shape and is aliased as process-neutral ``ProcessEvidence`` for probe
composition. Runtime attempt records are not yet projected through the proposed
shared base, and the runtime model has no quota lifecycle record yet.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Literal, NewType

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
type ProcessOutcomeKind = Literal[
    "completed",
    "timed_out",
    "output_limit_exceeded",
    "infrastructure_failure",
    "cancelled",
    "unexpected_exception",
    "no_observation",
    "not_started",
]
type SettingValue = str | int | float | bool | None
type RetryClass = Literal["infrastructure", "quota", "capacity", "other", "unknown"]
type NoResultBasis = Literal["confident_absence", "present_or_unknown"]
type QuotaState = Literal["available", "exhausted", "unknown", "unavailable"]
QuotaProviderId = NewType("QuotaProviderId", str)
QuotaAllowanceId = NewType("QuotaAllowanceId", str)
QuotaWindowId = NewType("QuotaWindowId", str)
type WaitEnd = Literal[
    "quota_available",
    "delay_elapsed",
    "bound",
    "cancelled",
    "stop",
    "unknown",
]
type WaitEventKind = Literal["started", "recheck", "finished"]
type WaitId = str
QuotaProbeId = NewType("QuotaProbeId", str)
type QuotaProbeReason = Literal["periodic", "reset_hint"]
type QuotaProbeCancelCause = Literal["cancelled", "stop", "superseded"]

class StrictModel(BaseModel):
    """Raw configuration and persisted records reject extras and coercion."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid", strict=True, frozen=True
    )

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
    quota waiting defaults off; its wait limit is optional. The poll interval
    is finite and positive, while ``quota_probe_budget`` is an optional finite
    operational cap. Enabling quota waiting explicitly authorizes polling;
    ``None`` adds no harness probe-count cap, a positive value caps probes, and
    zero refuses enabled polling. With quota waiting disabled, the budget may
    be absent and no probe or session read occurs.

    ``progress_interval_seconds`` is finite and positive; it throttles routine
    terminal refreshes, while meaningful transitions bypass the throttle.
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
    quiet: bool = False
    progress_interval_seconds: float = 1.0
    retry_limit: int = 0
    retry_nonzero_exit: bool = False
    quota_wait_enabled: bool = False
    quota_wait_limit_seconds: float | None = None
    quota_poll_interval_seconds: float = 60.0
    quota_probe_budget: int | None = None
    capacity_retry_limit: int = 0
    capacity_backoff_base_seconds: float | None = None
    capacity_backoff_cap_seconds: float | None = None
    instructions_file_path: Path | None

class QuotaScope(StrictModel):
    """Opaque provider and allowance identity safe to retain in run evidence.

    ``allowance_id`` is a stable, nonsecret identifier for one account/allowance
    combination within the provider; it is not a raw account name, credential,
    or token.
    """

    provider_id: QuotaProviderId
    allowance_id: QuotaAllowanceId

class QuotaWindowObservation(StrictModel):
    """One provider-specific blocking window with explicit source evidence.

    ``usage_percent`` is normalized to used percent in [0, 100] only when the
    source supplies used or remaining percentage; otherwise it stays unknown.
    ``source`` and ``diagnostic`` are sanitized descriptors, never raw account
    identity or credentials.
    """

    window_id: QuotaWindowId
    state: QuotaState
    usage_percent: float | None
    reset_at_utc: str | None
    source_observed_at_utc: str | None
    source_sequence: int | None
    source: str | None
    diagnostic: str | None

class QuotaObservation(StrictModel):
    """Provider-neutral windows for one source snapshot and verified scope.

    A missing scope is inconclusive and cannot authorize a wait. Required
    window completeness and freshness are defined by the provider adapter.
    ``read_at_utc`` is harness read time; source coordinate, producer timestamp,
    and within-source sequence retain provenance and order evidence. A delayed
    older snapshot cannot supersede a newer observation. Rereading never
    refreshes source age.
    Diagnostics are sanitized and contain no account identity or credentials.
    """

    scope: QuotaScope | None
    read_at_utc: str
    source_coordinate: str | None
    windows: tuple[QuotaWindowObservation, ...]
    diagnostic: str | None

class RetryAssessment(StrictModel):
    """Classification and no-result evidence; never inferred from answers."""

    retry_class: RetryClass
    classification_basis: str | None
    no_result_basis: NoResultBasis
    diagnostic: str | None

class QuotaWaitContext(StrictModel):
    """One global pause and cumulative accounting with scoped observations.

    The nested observation scope must match the triggering call's bound CLI
    scope. ``selected_reset_at_utc`` is an optional scheduling hint only; its
    arrival never establishes availability or ends the pause successfully.
    """

    kind: Literal["quota"]
    trigger_call_id: CallId
    trigger_attempt_number: AttemptNumber
    cumulative_waited_before_seconds: float
    wait_limit_seconds: float | None
    quota_observation: QuotaObservation
    selected_reset_at_utc: str | None

class QuotaProbeSchedule(StrictModel):
    """Durable cadence decision made before the check becomes due.

    One probe ID joins schedule, start, and settlement. The stored due time,
    interval, and optional reset hint explain cadence without a wait ID. This
    schedule makes no call for its own probe until the due time; passive
    observation of a settled evaluation may continue during the wait.
    """

    run_id: RunId
    probe_id: QuotaProbeId
    scope: QuotaScope
    reason: QuotaProbeReason
    created_at_utc: str
    due_at_utc: str
    interval_seconds: float
    reset_hint_at_utc: str | None

class QuotaProbeRequest(StrictModel):
    """One dispatched check associated with the pause it may confirm.

    The current pause ID is captured at actual dispatch, after active
    evaluations settle and persist. A probe launched earlier may settle but
    cannot reopen this newer pause. Coordinator start time differs from the
    paired process supervisor start time. The request retains the monotonic
    duration from schedule creation to actual dispatch.
    """

    schedule: QuotaProbeSchedule
    pause_wait_id: WaitId | None
    poll_started_at_utc: str
    scheduled_wait_seconds: float
    scheduled_wait_elapsed_basis: Literal["monotonic"]

@dataclass(frozen=True)
class AttemptEvidence:
    """Process-level supervisor evidence; evaluation identity is associated later."""

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
    """Probe assessment composed with shared ephemeral process evidence.

    Supervisor objects and exceptions stay inside ``process``. A completed
    process does not imply quota availability; the scoped observation must also
    be fresh and source-backed. Non-successful process kinds leave quota state
    unknown or unavailable while retaining their original process outcome.
    """

    request: QuotaProbeRequest
    process: ProcessEvidence
    quota_state: QuotaState
    observation: QuotaObservation | None
    classification_basis: str | None

class ProcessRecord(StrictModel):
    """Shared serializable projection of one supervised process outcome.

    It carries no run/call/attempt or probe identity. The evidence boundary
    projects live supervisor objects into scalar outcomes, cleanup records, and
    stream artifact references; exceptions remain represented by type and
    diagnostic rather than serialized objects. ``started_at_utc`` is when the
    supervisor process attempt starts, distinct from a probe's coordinator-side
    ``poll_started_at_utc``. ``no_observation`` and ``not_started`` remain
    distinct process outcomes; quota ``unknown`` and ``unavailable`` are stored
    separately on ``QuotaProbeRecord.quota_state``.
    """

    outcome_kind: ProcessOutcomeKind
    control_flow: ControlFlow
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

class QuotaProbeRecord(ProcessRecord):
    """Process projection plus logical probe identity and quota assessment.

    Unsafe cleanup and uncertain acquisition are determined from the shared
    cleanup/process fields; they never replace the quota state.
    """

    request: QuotaProbeRequest
    quota_state: QuotaState
    observation: QuotaObservation | None
    classification_basis: str | None

class QuotaProbeStarted(StrictModel):
    """Durable actual-dispatch event written before supervisor invocation."""

    kind: Literal["started"]
    request: QuotaProbeRequest

class QuotaProbeSettled(StrictModel):
    """Durable settled probe evidence written before any resumption."""

    kind: Literal["settled"]
    record: QuotaProbeRecord

class QuotaProbeScheduled(StrictModel):
    """Durable cadence decision; it represents no launched process."""

    kind: Literal["scheduled"]
    schedule: QuotaProbeSchedule

class QuotaProbeCancelled(StrictModel):
    """Scheduled wait ended before dispatch, with no process record."""

    kind: Literal["cancelled"]
    schedule: QuotaProbeSchedule
    cause: QuotaProbeCancelCause
    ended_at_utc: str
    elapsed_seconds: float
    elapsed_basis: Literal["monotonic"]

type QuotaProbeEvent = (
    QuotaProbeScheduled | QuotaProbeStarted | QuotaProbeSettled | QuotaProbeCancelled
)
type QuotaProbeLifecycleInput = (
    QuotaProbeScheduled | QuotaProbeStarted | QuotaProbeCancelled
)

class QuotaTelemetryEvent(StrictModel):
    """Provider-neutral observation correlated to one settled attempt."""

    run_id: RunId
    call_id: CallId
    attempt_number: AttemptNumber
    observation: QuotaObservation

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

class AttemptRecord(ProcessRecord):
    """Shared process projection plus evaluation identity and retry assessment."""

    run_id: RunId
    call_id: CallId
    position: int
    attempt_number: AttemptNumber
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
