# SPDX-License-Identifier: Apache-2.0
"""Shared immutable values and persisted boundary records."""

from dataclasses import dataclass
from datetime import datetime, timedelta
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

    position: int = Field(ge=0)
    path: Path


class SeparatorOption(StrictModel):
    """Separator argument at its original command-line position."""

    position: int = Field(ge=0)
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

    @model_validator(mode="after")
    def validate_plan_relationships(self) -> FrozenPlan:
        """Bind calls to configured contexts and instruction choice.

        Returns:
            The validated plan.

        Raises:
            ValueError: The plan's configured contexts or boundaries are inconsistent.
        """
        directory_positions = tuple(
            option.position
            for option in self.configuration.ordered_options
            if isinstance(option, DirectoryOption)
        )
        self._validate_snapshot_coverage(directory_positions)
        if len(self.boundary_bytes) != len(directory_positions) - 1:
            raise ValueError(
                "boundary_bytes must contain one value between each directory"
            )
        self._validate_call_contexts(directory_positions)
        self._validate_instruction_choice()
        return self

    def _validate_snapshot_coverage(self, directory_positions: tuple[int, ...]) -> None:
        """Require at least one source snapshot for each configured directory.

        Raises:
            ValueError: A configured directory has no snapshots or vice versa.
        """
        positions = tuple(snapshot.directory_position for snapshot in self.snapshots)
        groups = tuple(dict.fromkeys(positions))
        if positions != tuple(sorted(positions)) or groups != directory_positions:
            raise ValueError("snapshots must cover every configured directory position")

    def _validate_call_contexts(self, directory_positions: tuple[int, ...]) -> None:
        """Require every planned call to select one source per directory.

        Raises:
            ValueError: There are no calls or a call context is invalid.
        """
        if not self.calls:
            raise ValueError("planned calls must not be empty")
        for call in self.calls:
            self._validate_call_context(call, self.snapshots, directory_positions)

    @staticmethod
    def _validate_call_context(
        call: PlannedCall,
        snapshots: tuple[SourceSnapshot, ...],
        directory_positions: tuple[int, ...],
    ) -> None:
        """Validate one call's ordered source selection across directories.

        Raises:
            ValueError: Indices are invalid or omit/reorder a configured directory.
        """
        indices = call.context_indices
        if len(indices) != len(directory_positions):
            raise ValueError("planned calls must select one context per directory")
        if any(index >= len(snapshots) for index in indices):
            raise ValueError("planned call context index is outside snapshots")
        if len(set(indices)) != len(indices):
            raise ValueError("planned call context indices must be unique")
        positions = tuple(snapshots[index].directory_position for index in indices)
        if positions != directory_positions:
            raise ValueError(
                "planned call contexts must follow configured directory order"
            )

    def _validate_instruction_choice(self) -> None:
        """Keep configured instruction selection and its snapshot in agreement.

        Raises:
            ValueError: Configured instructions are missing or unexpectedly present.
        """
        if self.configuration.instructions_file_path is None:
            if self.instructions_file is not None:
                raise ValueError(
                    "instructions snapshot requires a configured instructions file"
                )
        elif self.instructions_file is None:
            raise ValueError(
                "configured instructions file requires an instructions snapshot"
            )


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
        _parse_utc_timestamp(self.started_at_utc, "started_at_utc")
        if self.ended_at_utc is not None:
            _parse_utc_timestamp(self.ended_at_utc, "ended_at_utc")
        flow_outcomes = {
            "cancelled": "cancelled",
            "raised": "unexpected_exception",
        }
        expected_outcome = flow_outcomes.get(self.control_flow)
        if expected_outcome is not None and self.outcome_kind != expected_outcome:
            raise ValueError("outcome_kind must agree with control_flow")
        if self.control_flow == "returned" and self.outcome_kind in set(
            flow_outcomes.values()
        ):
            raise ValueError("outcome_kind must agree with control_flow")
        elapsed_was_observed = self.elapsed_seconds is not None
        basis_has_observation = self.elapsed_basis == "supervisor_observation"
        if elapsed_was_observed != basis_has_observation:
            raise ValueError("elapsed_seconds must match elapsed_basis")
        return self


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

    @model_validator(mode="after")
    def validate_call_relationships(self) -> CallRecord:
        """Bind source identities and attempts to this scheduled call.

        Returns:
            The validated call record.

        Raises:
            ValueError: Source identities or attempt ownership disagree.
        """
        if len(self.source_paths) != len(self.source_sha256):
            raise ValueError("source_paths and source_sha256 must have equal lengths")
        for attempt in self.attempts:
            if (
                attempt.run_id != self.run_id
                or attempt.call_id != self.call_id
                or attempt.position != self.position
            ):
                raise ValueError("attempt run, call, and position must match its call")
        return self


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

    @model_validator(mode="after")
    def validate_run_relationships(self) -> RunRecord:
        """Require child calls to belong to this run at unique positions.

        Returns:
            The validated run record.

        Raises:
            ValueError: A child call belongs to another run or duplicates a position.
        """
        positions: set[int] = set()
        for call in self.calls:
            if call.run_id != self.run_id:
                raise ValueError("call run_id must match its run record")
            if call.position in positions:
                raise ValueError("run call positions must be unique")
            positions.add(call.position)
        return self


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


def _parse_utc_timestamp(value: str, field: str) -> datetime:
    """Parse a timezone-aware ISO timestamp whose offset is exactly UTC.

    Returns:
        The parsed UTC datetime.

    Raises:
        ValueError: The value is malformed, naive, or has a non-UTC offset.
    """
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO UTC timestamp") from exc
    if timestamp.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must have a UTC offset")
    return timestamp
