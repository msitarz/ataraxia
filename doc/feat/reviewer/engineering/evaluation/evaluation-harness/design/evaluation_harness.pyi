# SPDX-License-Identifier: Apache-2.0
"""Exploratory shared boundary for the generic evaluation harness.

This is not an importable runtime module. See ../architecture.md for ownership
and effects; the Work README remains the behavior contract. The supervisor's
types are imported from their active module and are not redeclared here.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict

from script.process_supervisor import AttemptRequest, AttemptResult, DispatchStop

type RunId = str
type CallId = str
type AttemptId = str
type EstimateCompatibility = Literal["exact", "approximate", "unknown"]
type CallState = Literal["not_started", "running", "complete", "failed"]
type RunState = Literal["complete", "incomplete"]
type ControlFlow = Literal["returned", "cancelled", "raised"]

@dataclass(frozen=True)
class DirectoryOption:
    """Directory argument at its original command-line position."""

    position: int
    path: Path

@dataclass(frozen=True)
class SeparatorOption:
    """Separator argument at its original command-line position."""

    position: int
    value: str

type OrderedOption = DirectoryOption | SeparatorOption

class StrictModel(BaseModel):
    """Base for raw configuration and persisted records; frozen, reject extras."""

    model_config: ConfigDict = ConfigDict(extra="forbid", frozen=True)

class HarnessConfig(StrictModel):
    """Validated CLI configuration; does not perform I/O or process effects.

    output_limit_bytes accepts zero, which disables the byte cap. retry_limit
    is finite and nonnegative, defaulting to zero at the CLI boundary.
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
    retry_limit: int

@dataclass(frozen=True)
class SourceSnapshot:
    """One tracked regular input and its exact frozen bytes."""

    repository_path: str
    commit_blob_sha: str
    content_sha256: str
    content: bytes

@dataclass(frozen=True)
class TokenEstimate:
    """Estimate and method metadata for supplied prompt bytes."""

    token_count: int | None
    method: str
    library_version: str | None
    tokenizer_version: str | None
    compatibility: EstimateCompatibility

class TokenEstimator(Protocol):
    """Local estimator port; it cannot dispatch model calls."""

    def estimate(self, prompt: bytes, model: str, /) -> TokenEstimate:
        """Estimate supplied prompt bytes for the requested model."""
        ...

@dataclass(frozen=True)
class PlannedCall:
    """One scheduled position, distinct from effective call identity."""

    position: int
    call_id: CallId
    context_indices: tuple[int, ...]
    model: str
    effort: str
    effective_settings_sha256: str
    prompt_sha256: str
    prompt: bytes

@dataclass(frozen=True)
class FrozenPlan:
    """Complete ordered matrix and source provenance prepared before dispatch."""

    run_id: RunId
    repository_root: Path
    head_commit: str
    snapshots: tuple[SourceSnapshot, ...]
    boundary_bytes: tuple[bytes, ...]
    calls: tuple[PlannedCall, ...]

@dataclass(frozen=True)
class AttemptEvidence:
    """One supervisor outcome and exact raw stream observations."""

    attempt_id: AttemptId
    started_at_utc: str
    ended_at_utc: str | None
    elapsed_seconds: float | None
    control_flow: ControlFlow
    result: AttemptResult | None
    error_type: str | None
    diagnostic: str | None
    stdout: bytes | None
    stderr: bytes | None
    usage_telemetry: bytes | None
    exit_status: int | None
    termination_reason: str | None
    cleanup_observations: bytes

@dataclass(frozen=True)
class CallEvidence:
    """Final status for one planned call and all of its attempts."""

    call_id: CallId
    position: int
    state: CallState
    attempts: tuple[AttemptEvidence, ...]

@dataclass(frozen=True)
class RunEvidence:
    """Run-level provenance and truthful planned-call accounting."""

    run_id: RunId
    head_commit: str
    state: RunState
    calls: tuple[CallEvidence, ...]
    stop_reason: str | None

class RunRecord(StrictModel):
    """Strict serialized run provenance and frozen-plan metadata."""

    run_id: RunId
    repository_root: str
    head_commit: str
    runner_version: str
    codex_path: str
    cli_version: str | None
    invocation_settings: dict[str, str | int | float | bool | None]

class CallRecord(StrictModel):
    """Strict serialized effective call and scheduled-position record."""

    run_id: RunId
    call_id: CallId
    position: int
    source_paths: tuple[str, ...]
    source_sha256: tuple[str, ...]
    boundary_bytes_hex: tuple[str, ...]
    prompt_sha256: str
    model: str
    effort: str
    effective_settings_sha256: str

class AttemptRecord(StrictModel):
    """Strict serialized attempt metadata, separate from raw stream artifacts."""

    run_id: RunId
    call_id: CallId
    attempt_id: AttemptId
    argv: tuple[str, ...]
    cwd: str
    started_at_utc: str
    ended_at_utc: str | None
    elapsed_seconds: float | None
    control_flow: ControlFlow
    exit_status: int | None
    termination_reason: str | None
    cleanup_observations: bytes
    error_type: str | None
    diagnostic: str | None

class EvidenceStore(Protocol):
    """Exclusive, append-only run evidence boundary."""

    def create(self, output_directory: Path, plan: FrozenPlan, /) -> None:
        """Exclusively create a new run destination and record its frozen plan."""
        ...

    def record_attempt(self, evidence: AttemptEvidence, /) -> None:
        """Persist one attempt; failure stops dispatch and cannot erase control flow."""
        ...

    def finalize(self, evidence: RunEvidence, /) -> None:
        """Persist final accounting; failures leave the run incomplete."""
        ...

@dataclass(frozen=True)
class RetryPolicy:
    """Finite, caller-owned retry eligibility; default limit is zero."""

    limit: int = 0
    retry_nonzero_exit: bool = False

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
    """Own ordered dispatch, stop state, retries, and not-started accounting."""

    attempt: AttemptCall
    evidence: EvidenceStore
    concurrency: int
    retry_policy: RetryPolicy

    async def run(self, plan: FrozenPlan, config: HarnessConfig, /) -> RunEvidence:
        """Run a frozen plan and account for every call and attempt."""
        ...

class RepositoryReader(Protocol):
    """Read-only Git and source boundary used before plan dispatch."""

    def freeze(self, config: HarnessConfig, /) -> FrozenPlan:
        """Validate repository inputs and return commit-checked snapshots."""
        ...

@dataclass(frozen=True)
class Composition:
    """Concrete adapters assembled once by the CLI entry point."""

    repository: RepositoryReader
    estimator: TokenEstimator
    attempt: AttemptCall
    evidence: EvidenceStore

    async def execute(self, config: HarnessConfig, /) -> RunEvidence | FrozenPlan:
        """Prepare a plan, then either report dry-run data or execute it."""
        ...
