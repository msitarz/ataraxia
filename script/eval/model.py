# SPDX-License-Identifier: Apache-2.0
"""Shared immutable values and persisted boundary records."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Annotated, Literal

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
type SettingValue = str | int | float | bool | None
type PositiveSeconds = Annotated[float, Field(gt=0, allow_inf_nan=False)]
type NonnegativeSeconds = Annotated[float, Field(ge=0, allow_inf_nan=False)]
type NonnegativeBytes = Annotated[int, Field(ge=0)]


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

    position: int
    path: Path


class SeparatorOption(StrictModel):
    """Separator argument at its original command-line position."""

    position: int
    value: str


type OrderedOption = DirectoryOption | SeparatorOption


class HarnessConfig(StrictModel):
    """CLI settings; validation does not perform I/O or dispatch."""

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
    retry_limit: int = Field(default=0, ge=0)
    retry_nonzero_exit: bool = False
    instructions_file_path: Path | None

    @model_validator(mode="after")
    def validate_relationships(self) -> HarnessConfig:
        """Enforce config relationships that do not require external effects.

        Returns:
            The validated configuration.

        Raises:
            ValueError: A matrix dimension, output destination, or deadline is invalid.
        """
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


class SourceSnapshot(StrictModel):
    """One tracked regular context input and its exact frozen bytes."""

    directory_position: int = Field(ge=0)
    repository_path: str
    commit_blob_sha: str
    content_sha256: str
    content: bytes

    @model_validator(mode="after")
    def content_digest_matches(self) -> SourceSnapshot:
        """Bind source provenance to its exact bytes.

        Returns:
            The validated source snapshot.

        Raises:
            ValueError: The recorded digest does not match the content.
        """
        if self.content_sha256 != sha256(self.content).hexdigest():
            raise ValueError("content_sha256 must match content")
        return self


class InstructionsSnapshot(StrictModel):
    """Tracked instruction input, separate from generic context files."""

    repository_path: str
    commit_blob_sha: str
    content_sha256: str
    content: bytes

    @model_validator(mode="after")
    def content_digest_matches(self) -> InstructionsSnapshot:
        """Bind instruction provenance to its exact bytes.

        Returns:
            The validated instruction snapshot.

        Raises:
            ValueError: The recorded digest does not match the content.
        """
        if self.content_sha256 != sha256(self.content).hexdigest():
            raise ValueError("content_sha256 must match content")
        return self


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
    context_indices: tuple[int, ...]
    model: str
    effort: str
    prompt_sha256: str
    prompt: bytes

    @model_validator(mode="after")
    def prompt_digest_matches(self) -> PlannedCall:
        """Bind the stored prompt digest to the exact composed bytes.

        Returns:
            The validated planned call.

        Raises:
            ValueError: The digest does not match or an index is negative.
        """
        if self.prompt_sha256 != sha256(self.prompt).hexdigest():
            raise ValueError("prompt_sha256 must match prompt")
        if any(index < 0 for index in self.context_indices):
            raise ValueError("context_indices must be nonnegative")
        return self


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


class AttemptRecord(StrictModel):
    """Persisted projection of one supervisor observation."""

    run_id: RunId
    call_id: CallId
    position: int = Field(ge=0)
    attempt_number: AttemptNumber = Field(ge=1)
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

    @model_validator(mode="after")
    def validate_observation(self) -> AttemptRecord:
        """Keep saved execution bounds and elapsed-time basis consistent.

        Returns:
            The validated attempt record.

        Raises:
            ValueError: Grace exceeds cleanup or elapsed data contradicts its basis.
        """
        if self.grace_seconds >= self.cleanup_timeout_seconds:
            raise ValueError("grace_seconds must be less than cleanup_timeout_seconds")
        elapsed_was_observed = self.elapsed_seconds is not None
        basis_has_observation = self.elapsed_basis == "supervisor_observation"
        if elapsed_was_observed != basis_has_observation:
            raise ValueError("elapsed_seconds must match elapsed_basis")
        return self


class CallRecord(StrictModel):
    """Persisted state and source identity for one scheduled call."""

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
