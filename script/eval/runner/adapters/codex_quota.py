# SPDX-License-Identifier: Apache-2.0
"""Codex quota telemetry and supervised polling for the evaluation runner.

This adapter supports the reviewed CLI 0.164.0 source shape and fails closed
when runtime identity, completeness, freshness, or scope cannot be verified.
"""

import asyncio
from asyncio import CancelledError
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import hashlib
from itertools import pairwise
import json
import math
import os
from pathlib import Path
from typing import BinaryIO, Literal, Protocol
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    ValidationInfo,
    field_validator,
)

from script.eval.model import (
    AttemptEvidence,
    QuotaAllowanceId,
    QuotaObservation,
    QuotaProbeEvidence,
    QuotaProbeRequest,
    QuotaProviderId,
    QuotaScope,
    QuotaState,
    QuotaWindowId,
    QuotaWindowObservation,
)
from script.eval.runner.adapters.codex import _toml_string
from script.eval.runner.ports import (
    AttemptCall,
    QuotaStatusReader,
    Runtime,
)
from script.eval.runner.quota_evidence import attach_quota_probe_evidence
from script.process_supervisor import (
    AttemptCancelled,
    AttemptFailureEvidence,
    AttemptRequest,
    AttemptResult,
    Completed,
    DispatchStop,
    InfrastructureFailure,
    OutputLimitExceeded,
    TimedOut,
    failure_evidence,
)


class RawCodexQuotaStatusSource(Protocol):
    """Read one opaque local session selected by its invocation thread ID."""

    async def read_session_for_thread(
        self, thread_id: str, /
    ) -> RawCodexSessionSnapshot | None:
        """Return only the source snapshot associated with this thread ID."""
        ...


@dataclass(frozen=True)
class RawCodexSessionSnapshot:
    """Selected metadata and quota rows from one untrusted rollout.

    ``content`` contains only the consumed ``session_meta`` and
    ``token_count`` rows, never the transcript's messages. The source
    coordinate is a stable opaque digest rather than a local path.
    """

    content: bytes = field(repr=False)
    source_coordinate: str
    requested_thread_id: str | None = field(default=None, repr=False)


class _RawModel(BaseModel):
    """Validate consumed fields while ignoring opaque producer extensions."""

    model_config = ConfigDict(
        extra="ignore", frozen=True, strict=True, hide_input_in_errors=True
    )


class _RawMetadata(_RawModel):
    """Identity fields consumed from the session metadata payload."""

    id: str = Field(repr=False, description="Invocation thread identifier.")
    session_id: str = Field(repr=False, description="Session identifier.")
    model_provider: str = Field(
        repr=False, description="Provider associated with the session."
    )
    cli_version: str = Field(
        repr=False, description="CLI version that produced the session."
    )
    creator_account_id: str = Field(
        repr=False, description="Creator account identifier."
    )
    creator_user_id: str = Field(repr=False, description="Creator user identifier.")

    @field_validator(
        "id",
        "session_id",
        "model_provider",
        "cli_version",
        "creator_account_id",
        "creator_user_id",
    )
    @classmethod
    def _nonempty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("identity field is empty")
        return value

    @field_validator("id", "session_id")
    @classmethod
    def _uuid(cls, value: str) -> str:
        if _canonical_uuid(value) is None:
            raise ValueError("identity is not a UUID")
        return value


class _RawMetadataRow(_RawModel):
    """Consumed session metadata envelope."""

    type: Literal["session_meta"] = Field(repr=False, description="Metadata row kind.")
    payload: _RawMetadata = Field(repr=False, description="Session identity fields.")


class _RawWindow(_RawModel):
    """Required usage and optional reset hint for one quota window."""

    used_percent: float = Field(description="Consumed percentage of the window.")
    window_minutes: int = Field(description="Duration of the quota window in minutes.")
    resets_at: str | None = Field(
        default=None, description="Optional canonical reset hint."
    )

    @field_validator("used_percent", mode="before")
    @classmethod
    def _usage(cls, value: object) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("usage must be numeric")
        try:
            usage = float(value)
        except OverflowError as error:
            raise ValueError("usage is out of range") from error
        if not math.isfinite(usage) or usage < 0:
            raise ValueError("usage must be finite and nonnegative")
        return usage

    @field_validator("resets_at", mode="before")
    @classmethod
    def _reset(cls, value: object) -> str | None:
        return _optional_reset_timestamp(value)


class _RawCredits(_RawModel):
    """Consumed credit state for the supported allowance shape."""

    has_credits: bool = Field(description="Whether credits are available.")
    unlimited: bool = Field(description="Whether credits are unlimited.")
    balance: str = Field(description="Decimal credit balance.")

    @field_validator("has_credits", "unlimited")
    @classmethod
    def _disabled(cls, value: bool) -> bool:
        if value:
            raise ValueError("credits are unsupported")
        return value

    @field_validator("balance")
    @classmethod
    def _zero_balance(cls, value: str) -> str:
        try:
            balance = Decimal(value)
        except InvalidOperation as error:
            raise ValueError("credit balance is invalid") from error
        if not balance.is_finite() or balance != 0:
            raise ValueError("credit balance is unsupported")
        return value


class _RawLimits(_RawModel):
    """Consumed limits for the supported Codex allowance."""

    limit_id: Literal["codex"] = Field(description="Allowance identifier.")
    credits: _RawCredits = Field(description="Credit balance state.")
    individual_limit: None = Field(description="Unsupported individual limit.")
    spend_control_reached: None = Field(description="Unsupported spend control.")
    rate_limit_reached_type: None = Field(description="Unsupported limit type.")
    primary: _RawWindow = Field(description="Five-hour usage window.")
    secondary: _RawWindow = Field(description="Weekly usage window.")

    @field_validator("primary", "secondary")
    @classmethod
    def _window_duration(cls, value: _RawWindow, info: ValidationInfo) -> _RawWindow:
        expected = 300 if info.field_name == "primary" else 10080
        if value.window_minutes != expected:
            raise ValueError("unsupported window duration")
        return value


class _RawTokenPayload(_RawModel):
    """Consumed token-count payload."""

    type: Literal["token_count"] = Field(description="Token event kind.")
    rate_limits: _RawLimits = Field(description="Observed allowance limits.")


class _RawTokenRow(_RawModel):
    """Consumed token-count row and its producer ordering facts."""

    type: Literal["event_msg"] = Field(description="Event envelope kind.")
    timestamp: datetime = Field(description="Aware producer timestamp in UTC.")
    ordinal: int = Field(ge=0, description="Nonnegative producer sequence number.")
    payload: _RawTokenPayload = Field(description="Token-count quota fields.")

    @field_validator("timestamp", mode="before")
    @classmethod
    def _timestamp(cls, value: object) -> datetime:
        timestamp = _parse_timestamp(value)
        if timestamp is None:
            raise ValueError("producer timestamp is invalid")
        return timestamp


@dataclass(frozen=True, repr=False)
class _SessionMetadata:
    """Validated identity fields consumed from one session metadata row."""

    id: str
    session_id: str
    model_provider: str
    cli_version: str
    creator_account_id: str
    creator_user_id: str


@dataclass(frozen=True)
class _QuotaWindowValues:
    """Validated usage with an optional, non-authoritative reset hint."""

    usage_percent: float
    reset_at_utc: str | None


@dataclass(frozen=True)
class _TokenCountRecord:
    """Validated quota facts from one ordered token-count event."""

    timestamp: datetime
    sequence: int
    primary: _QuotaWindowValues
    secondary: _QuotaWindowValues


@dataclass(frozen=True)
class _SessionTelemetry:
    """Small validated projection of one selected CLI rollout."""

    metadata: _SessionMetadata
    token_counts: tuple[_TokenCountRecord, ...]


@dataclass(frozen=True)
class LocalCodexQuotaStatusSource:
    """Look up one exact rollout under an explicitly configured sessions root.

    Only directory entries matching the requested thread UUID suffix are
    opened. No other rollout files are opened.
    """

    sessions_directory: Path

    async def read_session_for_thread(
        self, thread_id: str, /
    ) -> RawCodexSessionSnapshot | None:
        """Read selected telemetry without blocking the event loop.

        Returns:
            The selected rollout rows, or ``None`` when lookup is ambiguous,
            unavailable, malformed, or unsafe.
        """
        return await asyncio.to_thread(self._read_session_for_thread, thread_id)

    def _read_session_for_thread(
        self, thread_id: str, /
    ) -> RawCodexSessionSnapshot | None:
        """Perform exact-name lookup and retain only consumed rows.

        Returns:
            The selected row projection or ``None`` when it cannot be trusted.
        """
        normalized_thread_id = _canonical_uuid(thread_id)
        if normalized_thread_id is None:
            return None
        try:
            root = self.sessions_directory.resolve(strict=True)
            if not root.is_dir():
                return None
            candidates = tuple(
                root.glob(f"*/*/*/rollout-*-{normalized_thread_id}.jsonl")
            )
        except OSError:
            return None
        if len(candidates) != 1:
            return None
        return _read_candidate(root, candidates[0], normalized_thread_id)


@dataclass(frozen=True)
class CodexQuotaSettings:
    """Probe CLI identity, staged instructions, isolated cwd, and limits.

    Callers provide an existing empty read-only cwd and frozen nonempty
    instruction file. This value object checks path absoluteness only; it does
    not read or verify those staged paths.
    """

    executable_path: Path
    empty_read_only_cwd: Path
    probe_instructions_file: Path
    timeout_seconds: float
    cleanup_timeout_seconds: float
    output_limit_bytes: int
    grace_seconds: float

    def __post_init__(self) -> None:
        """Require absolute paths while leaving staged-file reads to callers.

        Raises:
            ValueError: A CLI, cwd, or frozen instruction path is relative.
        """
        if not self.executable_path.is_absolute():
            raise ValueError("executable_path must be absolute")
        if not self.empty_read_only_cwd.is_absolute():
            raise ValueError("empty_read_only_cwd must be absolute")
        if not self.probe_instructions_file.is_absolute():
            raise ValueError("probe_instructions_file must be absolute")


type ExtractThreadId = Callable[[bytes | None], str | None]
type NormalizeSession = Callable[
    [RawCodexSessionSnapshot | None, QuotaScope | None, str, float], QuotaObservation
]
type BuildProbeRequest = Callable[
    [QuotaProbeRequest, CodexQuotaSettings], AttemptRequest
]
type AssessProbe = Callable[
    [AttemptEvidence, QuotaObservation | None], tuple[QuotaState, str | None]
]


@dataclass(frozen=True, kw_only=True)
class CodexQuotaStatusReader(QuotaStatusReader):
    """Read passive telemetry and expose separate, supervised quota polls.

    Responsibilities:

    - correlate settled invocation telemetry to its private source lookup;
    - normalize source data to provider-neutral scoped observations;
    - run a separate probe through the injected supervisor call;
    - associate process facts and quota assessment with probe evidence.

    Thread IDs remain private to this adapter. The local source opens only the
    exact UUID-suffixed rollout candidate. The normalizer accepts the observed
    Codex CLI 0.164.0 schema and fails closed on unrecognized or incomplete
    input. The probe uses the caller's frozen nonempty instruction file and
    receives a fixed minimal prompt.
    """

    source: RawCodexQuotaStatusSource
    quota_scope: QuotaScope | None
    settings: CodexQuotaSettings
    attempt_call: AttemptCall
    runtime: Runtime
    max_observation_age_seconds: float = 60.0
    extract_thread_id: ExtractThreadId | None = None
    normalize_session: NormalizeSession | None = None
    build_probe_request: BuildProbeRequest | None = None
    assess_probe: AssessProbe | None = None
    _ordering: _ObservationOrdering = field(
        default_factory=lambda: _ObservationOrdering(), compare=False, repr=False
    )

    def __post_init__(self) -> None:
        """Reject an unbounded or invalid source-freshness allowance.

        Raises:
            ValueError: The observation-age allowance is not finite and positive.
        """
        age = self.max_observation_age_seconds
        if isinstance(age, bool) or not isinstance(age, (int, float)):
            raise ValueError("max_observation_age_seconds must be finite and positive")
        if not math.isfinite(age) or age <= 0:
            raise ValueError("max_observation_age_seconds must be finite and positive")

    @property
    def expected_scope(self) -> QuotaScope | None:
        """The verified scope paired with this reader, when known."""
        return self.quota_scope

    async def observe_settled_attempt(
        self, evidence: AttemptEvidence, /
    ) -> QuotaObservation:
        """Look up this attempt's source session and normalize it once.

        Returns:
            The injected provider-neutral observation.
        """
        return await self._observe_telemetry(evidence)

    async def poll(
        self, request: QuotaProbeRequest, stop_dispatch: DispatchStop, /
    ) -> QuotaProbeEvidence:
        """Run a separate supervised poll and retain facts on raised errors.

        If cancellation or another exception escapes after dispatch, attach its
        available process and quota facts to that same exception. Callers use
        the original request object with ``quota_probe_evidence``. A missing
        match is incomplete evidence and cannot establish availability.

        Returns:
            The process evidence paired with its normalized quota observation.

        Raises:
            ValueError: The requested quota scope is absent or does not match
                this reader's verified scope.
        """
        if self.expected_scope is None or request.schedule.scope != self.expected_scope:
            raise ValueError(
                "quota probe request does not match the reader's verified scope"
            )
        build_request = self.build_probe_request or _build_probe_attempt_request
        assess_probe = self.assess_probe or _assess_probe
        attempt_request = build_request(request, self.settings)
        started_at_utc = self.runtime.utc_now()
        outcome: AttemptResult | None = None
        attempt: AttemptEvidence | None = None
        ended_at_utc: str | None = None
        observation: QuotaObservation | None = None
        try:
            outcome = await self.attempt_call(attempt_request, stop_dispatch)
            ended_at_utc = self.runtime.utc_now()
            attempt = _attempt_evidence(
                attempt_request, outcome, started_at_utc, ended_at_utc
            )
            observation = await self._observe_telemetry(attempt)
            quota_state, classification_basis = assess_probe(attempt, observation)
            return QuotaProbeEvidence(
                request=request,
                process=attempt,
                quota_state=quota_state,
                observation=observation,
                classification_basis=classification_basis,
            )
        except BaseException as error:
            if ended_at_utc is None:
                ended_at_utc = _read_end_time(self.runtime)
            if attempt is None:
                attempt = _attempt_evidence_for_error(
                    attempt_request,
                    outcome,
                    error,
                    started_at_utc,
                    ended_at_utc,
                )
            attach_quota_probe_evidence(
                error,
                QuotaProbeEvidence(
                    request=request,
                    process=attempt,
                    quota_state="unknown",
                    observation=observation,
                    classification_basis="probe assessment did not complete",
                ),
            )
            raise

    async def _observe_telemetry(self, attempt: AttemptEvidence, /) -> QuotaObservation:
        """Correlate captured thread telemetry and normalize its source.

        Returns:
            The injected source-backed observation.
        """
        extract_thread_id = self.extract_thread_id or _extract_thread_id
        normalize_session = self.normalize_session or _normalize_session
        thread_id = extract_thread_id(attempt.usage_telemetry)
        snapshot = (
            await self.source.read_session_for_thread(thread_id)
            if thread_id is not None
            else None
        )
        observation = normalize_session(
            snapshot,
            self.expected_scope,
            self.runtime.utc_now(),
            self.max_observation_age_seconds,
        )
        return await self._ordering.accept(observation, self.expected_scope)


@dataclass
class _ObservationOrdering:
    """Reject delayed snapshots before they can replace newer quota state."""

    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    latest_timestamp: datetime | None = None
    latest_coordinate: str | None = None
    latest_snapshots: dict[
        str,
        tuple[
            datetime,
            int,
            tuple[tuple[str, str, float | None, str | None], ...],
        ],
    ] = field(default_factory=dict)

    async def accept(
        self, observation: QuotaObservation, expected_scope: QuotaScope | None, /
    ) -> QuotaObservation:
        """Apply one cross-read freshness order to scoped complete snapshots.

        Returns:
            The observation or an unknown copy when its source order regresses.
        """
        if expected_scope is None or observation.scope != expected_scope:
            return _as_unknown(
                observation, "quota observation does not match the verified scope"
            ).model_copy(update={"scope": None})
        if not _has_complete_windows(observation):
            return observation
        order = _observation_order_key(observation)
        if isinstance(order, str):
            return _as_unknown(observation, order)
        return await self._accept_ordered(observation, order)

    async def _accept_ordered(
        self,
        observation: QuotaObservation,
        order: tuple[str, datetime, int],
        /,
    ) -> QuotaObservation:
        """Compare and retain a validated source-order key atomically.

        Returns:
            The observation or an unknown copy on ordering regression.
        """
        coordinate, timestamp, sequence = order
        signature = _observation_signature(observation)
        async with self.lock:
            prior = self.latest_snapshots.get(coordinate)
            if prior is not None and (timestamp, sequence) == prior[:2]:
                if signature == prior[2]:
                    latest_timestamp = self.latest_timestamp
                    if latest_timestamp is not None and timestamp < latest_timestamp:
                        return _as_unknown(
                            observation,
                            "quota snapshot is older than a prior observation",
                        )
                    if (
                        latest_timestamp is not None
                        and timestamp == latest_timestamp
                        and coordinate != self.latest_coordinate
                    ):
                        return _as_unknown(
                            observation,
                            "quota snapshots have ambiguous equal timestamps",
                        )
                    return observation
                return _as_unknown(
                    observation, "quota source repeated an ordinal with changed facts"
                )
            prior_ordinal = None if prior is None else prior[1]
            issue = _ordering_issue(
                coordinate,
                timestamp,
                sequence,
                prior_ordinal,
                self.latest_timestamp,
                self.latest_coordinate,
            )
            if issue is not None:
                return _as_unknown(observation, issue)
            self.latest_timestamp = timestamp
            self.latest_coordinate = coordinate
            self.latest_snapshots[coordinate] = (timestamp, sequence, signature)
        return observation


def _observation_signature(
    observation: QuotaObservation, /
) -> tuple[tuple[str, str, float | None, str | None], ...]:
    """Retain usage and reset facts for same-ordinal conflict detection.

    Returns:
        Stable window facts used to detect a changed source record.
    """
    return tuple(
        (
            str(window.window_id),
            window.state,
            window.usage_percent,
            window.reset_at_utc,
        )
        for window in observation.windows
    )


def _has_complete_windows(observation: QuotaObservation, /) -> bool:
    """Check whether ordering can apply to a complete observation.

    Returns:
        Whether all windows have a known availability state.
    """
    return bool(observation.windows) and all(
        window.state in {"available", "exhausted"} for window in observation.windows
    )


def _observation_order_key(
    observation: QuotaObservation, /
) -> tuple[str, datetime, int] | str:
    """Validate the common producer timestamp and ordinal across windows.

    Returns:
        A validated order key or an explanatory diagnostic.
    """
    coordinates = {observation.source_coordinate}
    timestamps = {window.source_observed_at_utc for window in observation.windows}
    sequences = {window.source_sequence for window in observation.windows}
    if len(coordinates) != 1 or len(timestamps) != 1 or len(sequences) != 1:
        return "quota windows do not share one source record"
    coordinate = next(iter(coordinates))
    timestamp_text = next(iter(timestamps))
    sequence = next(iter(sequences))
    if coordinate is None or timestamp_text is None or sequence is None:
        return "quota source ordering is unavailable"
    timestamp = _parse_timestamp(timestamp_text)
    if timestamp is None:
        return "quota source timestamp is invalid"
    return coordinate, timestamp, sequence


def _ordering_issue(
    coordinate: str,
    timestamp: datetime,
    sequence: int,
    prior_ordinal: int | None,
    latest_timestamp: datetime | None,
    latest_coordinate: str | None,
    /,
) -> str | None:
    """Return a precise reason when one source snapshot regresses ordering."""
    if prior_ordinal is not None and sequence <= prior_ordinal:
        return "quota source sequence did not advance"
    if latest_timestamp is None:
        return None
    if timestamp < latest_timestamp:
        return "quota snapshot is older than a prior observation"
    if timestamp == latest_timestamp and coordinate != latest_coordinate:
        return "quota snapshots have ambiguous equal timestamps"
    return None


def codex_quota_scope_from_identity(
    model_provider: str,
    creator_account_id: str,
    creator_user_id: str,
    /,
) -> QuotaScope:
    """Create an opaque Codex allowance scope from trusted session identity.

    The raw identity values are used only to derive a stable, domain-separated
    digest. Callers must not log or persist them. This helper does not read local
    authentication state or establish that two invocations use this identity.

    Returns:
        A stable scope with an opaque, versioned allowance identifier.

    Raises:
        ValueError: An identity field is missing, empty, or unsupported.
    """
    if (
        not isinstance(model_provider, str)
        or not isinstance(creator_account_id, str)
        or not isinstance(creator_user_id, str)
    ):
        raise ValueError("Codex quota identity fields must be nonempty strings")
    if (
        not model_provider.strip()
        or not creator_account_id.strip()
        or not creator_user_id.strip()
    ):
        raise ValueError("Codex quota identity fields must be nonempty strings")
    if model_provider != "openai":
        raise ValueError("Codex quota scope requires the OpenAI provider")
    canonical = json.dumps(
        {
            "domain": "ataraxia.codex-quota-scope.v1",
            "provider": model_provider,
            "account": creator_account_id,
            "user": creator_user_id,
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    digest = hashlib.sha256(canonical).hexdigest()
    return QuotaScope(
        provider_id=QuotaProviderId("codex"),
        allowance_id=QuotaAllowanceId(f"sha256-v1:{digest}"),
    )


def _canonical_uuid(value: object, /) -> str | None:
    """Validate and canonicalize a UUID for exact filename matching.

    Returns:
        A canonical UUID string or ``None`` when the value is not a UUID.
    """
    if not isinstance(value, str):
        return None
    try:
        parsed = UUID(value)
    except ValueError:
        return None
    canonical = str(parsed)
    return canonical if value.lower() == canonical else None


def _read_candidate(
    root: Path, candidate: Path, thread_id: str, /
) -> RawCodexSessionSnapshot | None:
    """Validate and read one candidate without exposing its local path.

    Returns:
        The selected snapshot or ``None`` when its path or contents are unsafe.
    """
    resolved = _resolve_candidate(root, candidate)
    if resolved is None:
        return None
    try:
        stat_before = resolved.stat()
        selected_rows = _read_selected_rows(resolved)
        stat_after = resolved.stat()
    except OSError:
        return None
    if (
        stat_before.st_size != stat_after.st_size
        or stat_before.st_mtime_ns != stat_after.st_mtime_ns
        or selected_rows is None
    ):
        return None
    return RawCodexSessionSnapshot(
        content=selected_rows,
        source_coordinate=_source_coordinate(root, resolved),
        requested_thread_id=thread_id,
    )


def _resolve_candidate(root: Path, candidate: Path, /) -> Path | None:
    """Resolve a candidate only when it is a nonsymlink file under root.

    Returns:
        The resolved file or ``None`` when the candidate is unsafe.
    """
    try:
        if candidate.is_symlink():
            return None
        resolved = candidate.resolve(strict=True)
    except OSError:
        return None
    if not resolved.is_relative_to(root) or not resolved.is_file():
        return None
    return resolved


def _source_coordinate(root: Path, path: Path, /) -> str:
    """Hash a repository-local source path without retaining the path itself.

    Returns:
        A stable digest suitable for per-source ordering.
    """
    relative = path.relative_to(root).as_posix().encode("utf-8")
    digest = hashlib.sha256(b"ataraxia.codex-session-coordinate.v1\0" + relative)
    return f"codex-session-sha256:{digest.hexdigest()}"


def _read_selected_rows(path: Path, /) -> bytes | None:
    """Read one stable rollout while retaining only consumed telemetry rows.

    Returns:
        Projected metadata and quota JSONL, or ``None`` if the read is unsafe.
    """
    maximum_line_bytes = 8 * 1024 * 1024
    maximum_rollout_bytes = 128 * 1024 * 1024
    try:
        with path.open("rb") as stream:
            before = os.fstat(stream.fileno())
            if before.st_size > maximum_rollout_bytes:
                return None
            collected = _collect_selected_rows(stream, maximum_line_bytes)
            after = os.fstat(stream.fileno())
    except OSError:
        return None
    if collected is None:
        return None
    selected_rows, metadata_count = collected
    if metadata_count != 1 or before.st_size != after.st_size:
        return None
    if before.st_mtime_ns != after.st_mtime_ns:
        return None
    return b"\n".join(selected_rows)


def _collect_selected_rows(
    stream: BinaryIO, maximum_line_bytes: int, /
) -> tuple[list[bytes], int] | None:
    """Project the metadata and quota rows from one opened rollout.

    Returns:
        Selected rows and the metadata count, or ``None`` on malformed input.
    """
    selected: list[bytes] = []
    metadata_count = 0
    while line := stream.readline(maximum_line_bytes + 1):
        if len(line) > maximum_line_bytes:
            return None
        try:
            row = json.loads(line)
        except UnicodeDecodeError, json.JSONDecodeError:
            return None
        if not isinstance(row, dict):
            return None
        try:
            projected, is_metadata = _project_rollout_row(row)
        except ValueError:
            return None
        if projected is None:
            continue
        metadata_count += is_metadata
        if metadata_count > 1:
            return None
        selected.append(projected)
        if len(selected) > 4096:
            return None
    return selected, metadata_count


def _project_rollout_row(row: dict[str, object], /) -> tuple[bytes | None, int]:
    """Project one consumed row and ignore unrelated well-formed row kinds.

    Returns:
        The encoded consumed row and whether it is session metadata.

    Raises:
        ValueError: A consumed row's envelope cannot be inspected safely.
    """
    row_type = row.get("type")
    if row_type == "session_meta":
        payload = row.get("payload")
        if not isinstance(payload, dict):
            raise ValueError("session metadata payload must be an object")
        selected = {
            key: payload.get(key)
            for key in (
                "id",
                "session_id",
                "model_provider",
                "cli_version",
                "creator_account_id",
                "creator_user_id",
            )
        }
        return _encode_selected_row({"type": "session_meta", "payload": selected}), 1
    if row_type != "event_msg":
        return None, 0
    payload = row.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("event message payload must be an object")
    if payload.get("type") != "token_count":
        return None, 0
    return _encode_token_count_row(row, payload), 0


def _encode_token_count_row(
    row: dict[str, object], payload: dict[str, object], /
) -> bytes:
    """Encode only a quota event's envelope and quota-limit object.

    Returns:
        Canonical JSON bytes containing only the selected quota event fields.
    """
    limits = payload.get("rate_limits")
    return _encode_selected_row({
        "type": "event_msg",
        "timestamp": row.get("timestamp"),
        "ordinal": row.get("ordinal"),
        "payload": {
            "type": "token_count",
            "rate_limits": limits if isinstance(limits, dict) else None,
        },
    })


def _encode_selected_row(row: dict[str, object], /) -> bytes:
    """Encode a projected telemetry row using deterministic JSON bytes.

    Returns:
        The encoded row.
    """
    return json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _attempt_evidence(
    request: AttemptRequest,
    outcome: AttemptResult,
    started_at_utc: str,
    ended_at_utc: str,
    /,
) -> AttemptEvidence:
    """Retain a returned result and its captured stdout bytes.

    Returns:
        Process evidence for the exact request and returned result.
    """
    output = outcome.observation.output
    return AttemptEvidence(
        control_flow="returned",
        outcome=outcome,
        error_type=None,
        diagnostic=None,
        request=request,
        started_at_utc=started_at_utc,
        ended_at_utc=ended_at_utc,
        usage_telemetry=None if output is None else output.stdout,
    )


def _attempt_evidence_for_error(
    request: AttemptRequest,
    outcome: AttemptResult | None,
    error: BaseException,
    started_at_utc: str,
    ended_at_utc: str | None,
    /,
) -> AttemptEvidence:
    """Preserve supervisor facts while describing the original raised flow.

    Returns:
        Available process evidence associated with the original error.
    """
    settled_outcome: AttemptResult | AttemptCancelled | AttemptFailureEvidence | None
    if outcome is not None:
        settled_outcome = outcome
    elif isinstance(error, AttemptCancelled):
        settled_outcome = error
    else:
        attached_result = vars(error).get("process_supervisor_outcome")
        settled_outcome = (
            attached_result
            if isinstance(
                attached_result,
                (Completed, TimedOut, OutputLimitExceeded, InfrastructureFailure),
            )
            else failure_evidence(error)
        )
    observation = None if settled_outcome is None else settled_outcome.observation
    usage_telemetry = (
        None
        if observation is None or observation.output is None
        else observation.output.stdout
    )
    return AttemptEvidence(
        control_flow=(
            "returned"
            if outcome is not None
            else "cancelled"
            if isinstance(error, CancelledError)
            else "raised"
        ),
        outcome=settled_outcome,
        error_type=None if outcome is not None else type(error).__name__,
        diagnostic=None if outcome is not None else _error_diagnostic(error),
        request=request,
        started_at_utc=started_at_utc,
        ended_at_utc=ended_at_utc,
        usage_telemetry=usage_telemetry,
    )


def _read_end_time(runtime: Runtime, /) -> str | None:
    """Read an end time without replacing the primary exception.

    Returns:
        The observed timestamp or ``None`` if the clock fails.
    """
    try:
        return runtime.utc_now()
    except Exception:
        return None


def _error_diagnostic(error: BaseException, /) -> str:
    """Format an error without letting a broken ``__str__`` mask it.

    Returns:
        The exception's display text or a safe fallback.
    """
    try:
        return str(error)
    except Exception:
        return "exception diagnostic unavailable"


def _extract_thread_id(usage_telemetry: bytes | None, /) -> str | None:
    """Extract one canonical thread ID from captured ``codex exec --json``.

    Returns:
        The invocation UUID or ``None`` when output is invalid or ambiguous.
    """
    if usage_telemetry is None:
        return None
    try:
        text = usage_telemetry.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return None
    thread_ids: list[str] = []
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            return None
        if not isinstance(event, dict):
            return None
        if event.get("type") == "thread.started":
            thread_id = _canonical_uuid(event.get("thread_id"))
            if thread_id is None:
                return None
            thread_ids.append(thread_id)
    if len(thread_ids) != 1:
        return None
    return thread_ids[0]


def _normalize_session(
    snapshot: RawCodexSessionSnapshot | None,
    scope: QuotaScope | None,
    read_at_utc: str,
    max_observation_age_seconds: float,
    /,
) -> QuotaObservation:
    """Validate the observed 0.164.0 schema and normalize both quota windows.

    Returns:
        A scoped observation only when session identity matches the binding.
    """
    read_at = _parse_timestamp(read_at_utc)
    if read_at is None or not _valid_age_limit(max_observation_age_seconds):
        reason = (
            "reader clock is invalid"
            if read_at is None
            else "freshness bound is invalid"
        )
        return _unknown_observation(scope, read_at_utc, None, reason)
    if snapshot is None or not snapshot.content or not snapshot.source_coordinate:
        return _unknown_observation(
            None, read_at_utc, None, "session telemetry is unavailable"
        )
    telemetry = _parse_session_telemetry(snapshot.content)
    if telemetry is None:
        return _unknown_observation(
            None,
            read_at_utc,
            snapshot.source_coordinate,
            "session telemetry is malformed or incomplete",
        )
    session_scope, identity_issue = _session_scope(telemetry.metadata, snapshot, scope)
    if identity_issue is not None or session_scope is None:
        return _unknown_observation(
            None,
            read_at_utc,
            snapshot.source_coordinate,
            identity_issue or "session quota scope is unavailable",
        )
    latest, ordering_issue = _latest_rate_limit_record(telemetry.token_counts)
    if latest is None:
        return _unknown_observation(
            session_scope,
            read_at_utc,
            snapshot.source_coordinate,
            ordering_issue or "session telemetry is incomplete",
        )
    age = (read_at - latest.timestamp).total_seconds()
    if age < 0:
        return _observation_from_record(
            session_scope,
            _format_timestamp(read_at),
            snapshot.source_coordinate,
            latest,
            "unknown",
            "quota source timestamp is in the future",
        )
    if age > max_observation_age_seconds:
        return _observation_from_record(
            session_scope,
            _format_timestamp(read_at),
            snapshot.source_coordinate,
            latest,
            "unknown",
            "quota source observation is stale",
        )
    return _observation_from_record(
        session_scope,
        _format_timestamp(read_at),
        snapshot.source_coordinate,
        latest,
        None,
        None,
    )


def _valid_age_limit(value: object, /) -> bool:
    """Check a runtime freshness bound without accepting booleans.

    Returns:
        Whether the value is finite and positive.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value) and value > 0
    except OverflowError:
        return False


def _session_scope(
    metadata: _SessionMetadata,
    snapshot: RawCodexSessionSnapshot,
    expected_scope: QuotaScope | None,
    /,
) -> tuple[QuotaScope | None, str | None]:
    """Validate one supported session identity against the configured scope.

    Returns:
        The matching scope and no issue, or an unscoped failure diagnostic.
    """
    requested_thread_id = _canonical_uuid(snapshot.requested_thread_id)
    if (
        requested_thread_id is None
        or metadata.id != requested_thread_id
        or metadata.session_id != requested_thread_id
    ):
        return None, "session identity does not match the invocation"
    if metadata.cli_version != "0.164.0":
        return None, "session CLI version is unsupported"
    try:
        observed_scope = codex_quota_scope_from_identity(
            metadata.model_provider,
            metadata.creator_account_id,
            metadata.creator_user_id,
        )
    except ValueError:
        return None, "session provider is unsupported"
    if expected_scope is None or observed_scope != expected_scope:
        return None, "session quota scope is not verified"
    return expected_scope, None


def _parse_session_telemetry(content: bytes, /) -> _SessionTelemetry | None:
    """Validate selected JSONL rows once at the adapter raw-data boundary.

    Returns:
        Typed consumed fields, or None for malformed or incomplete data.
    """
    rows = _decode_selected_rows(content)
    if rows is None:
        return None
    metadata = _parse_metadata_rows(rows)
    token_counts = _parse_quota_rows(rows)
    if metadata is None or token_counts is None:
        return None
    return _SessionTelemetry(metadata, token_counts)


def _parse_metadata_rows(rows: list[dict[str, object]], /) -> _SessionMetadata | None:
    """Require one valid session identity record from selected rollout rows.

    Returns:
        The validated identity or None when it is missing, duplicate, or invalid.
    """
    metadata: _SessionMetadata | None = None
    for row in rows:
        if row.get("type") == "session_meta":
            if metadata is not None:
                return None
            metadata = _parse_session_metadata(row)
            if metadata is None:
                return None
    return metadata


def _parse_quota_rows(
    rows: list[dict[str, object]], /
) -> tuple[_TokenCountRecord, ...] | None:
    """Require each consumed token-count event to validate into typed facts.

    Returns:
        Validated events, or None when they are missing or malformed.
    """
    token_counts: list[_TokenCountRecord] = []
    for row in rows:
        if _is_token_count_row(row):
            record = _parse_token_count_record(row)
            if record is None:
                return None
            token_counts.append(record)
    return tuple(token_counts) if token_counts else None


def _is_token_count_row(row: dict[str, object], /) -> bool:
    """Identify the consumed token-count event envelope.

    Returns:
        Whether the row is a token-count event.
    """
    payload = row.get("payload")
    return (
        row.get("type") == "event_msg"
        and isinstance(payload, dict)
        and payload.get("type") == "token_count"
    )


def _parse_session_metadata(row: dict[str, object], /) -> _SessionMetadata | None:
    """Validate consumed identity fields without retaining untrusted extensions.

    Returns:
        The identity, or None when the consumed fields are invalid.
    """
    try:
        payload = _RawMetadataRow.model_validate(row).payload
    except ValidationError:
        return None
    return _SessionMetadata(
        id=payload.id,
        session_id=payload.session_id,
        model_provider=payload.model_provider,
        cli_version=payload.cli_version,
        creator_account_id=payload.creator_account_id,
        creator_user_id=payload.creator_user_id,
    )


def _latest_rate_limit_record(
    records: tuple[_TokenCountRecord, ...],
    /,
) -> tuple[_TokenCountRecord | None, str | None]:
    """Validate producer order and select its newest typed quota record.

    Returns:
        The newest row, or an ordering/incompleteness diagnostic.
    """
    for earlier, later in pairwise(records):
        if later.sequence <= earlier.sequence or later.timestamp < earlier.timestamp:
            return None, "rate-limit rows are out of source order"
    return (records[-1], None) if records else (None, "session telemetry is incomplete")


def _observation_from_record(
    scope: QuotaScope,
    read_at_utc: str,
    coordinate: str,
    record: _TokenCountRecord,
    state: QuotaState | None,
    diagnostic: str | None,
    /,
) -> QuotaObservation:
    """Project a validated quota record while retaining source facts.

    Returns:
        A provider-neutral observation preserving optional reset hints.
    """
    windows = tuple(
        QuotaWindowObservation(
            window_id=QuotaWindowId(window_id),
            state=(
                "unknown"
                if state == "unknown"
                else "exhausted"
                if values.usage_percent >= 100
                else "available"
            ),
            usage_percent=values.usage_percent,
            reset_at_utc=values.reset_at_utc,
            source_observed_at_utc=_format_timestamp(record.timestamp),
            source_sequence=record.sequence,
            source="codex-cli-0.164.0-session",
            diagnostic=diagnostic,
        )
        for window_id, values in (
            ("codex_primary_300m", record.primary),
            ("codex_secondary_10080m", record.secondary),
        )
    )
    return QuotaObservation(
        scope=scope,
        read_at_utc=read_at_utc,
        source_coordinate=coordinate,
        windows=windows,
        diagnostic=diagnostic,
    )


def _build_probe_attempt_request(
    request: QuotaProbeRequest,
    settings: CodexQuotaSettings,
    /,
) -> AttemptRequest:
    """Build the fixed, supervised Codex quota poll request.

    The requested disables are bounded to known CLI feature controls and an
    ignored user config. No verified global MCP-server clear is available, so
    this recipe makes no claim that every MCP server is disabled.

    Returns:
        The exact process request passed to the public supervisor boundary.
    """
    del request
    config_args = (
        "-c",
        f"model_reasoning_effort={_toml_string('none')}",
        "-c",
        "model_instructions_file="
        + _toml_string(str(settings.probe_instructions_file)),
        "-c",
        "agents.enabled=false",
        "-c",
        "skills.bundled.enabled=false",
        "-c",
        "memories.use_memories=false",
        "-c",
        'approval_policy="never"',
        "-c",
        'web_search="disabled"',
        "-c",
        "tools.experimental_request_user_input.enabled=false",
    )
    disabled_features = (
        "plugins",
        "apps",
        "shell_tool",
        "multi_agent",
        "browser_use",
        "computer_use",
        "image_generation",
        "view_image",
        "sleep_tool",
        "code_mode",
        "skill_search",
    )
    feature_args = tuple(
        item for feature in disabled_features for item in ("--disable", feature)
    )
    argv = (
        str(settings.executable_path),
        "exec",
        "--json",
        "--color",
        "never",
        "--ignore-user-config",
        "--sandbox",
        "read-only",
        "--skip-git-repo-check",
        "--cd",
        str(settings.empty_read_only_cwd),
        "-m",
        "gpt-6-luna",
        *config_args,
        *feature_args,
        "--",
        "Check the current Codex quota. Reply READY.",
    )
    return AttemptRequest(
        argv=argv,
        cwd=settings.empty_read_only_cwd,
        timeout_seconds=settings.timeout_seconds,
        cleanup_timeout_seconds=settings.cleanup_timeout_seconds,
        output_limit_bytes=settings.output_limit_bytes,
        stdin="devnull",
        grace_seconds=settings.grace_seconds,
    )


def _assess_probe(
    attempt: AttemptEvidence,
    observation: QuotaObservation | None,
    /,
) -> tuple[QuotaState, str | None]:
    """Require fresh scoped telemetry and safe process settlement.

    Returns:
        The conservative state and its classification basis.
    """
    if observation is None or observation.scope is None or not observation.windows:
        return "unknown", "probe has no complete scoped quota observation"
    required_windows = {"codex_primary_300m", "codex_secondary_10080m"}
    if {window.window_id for window in observation.windows} != required_windows:
        return "unknown", "probe does not contain both required quota windows"
    if any(
        window.state in {"unknown", "unavailable"} for window in observation.windows
    ):
        return "unknown", "probe quota observation is incomplete"
    outcome = attempt.outcome
    if (
        attempt.control_flow != "returned"
        or not isinstance(outcome, Completed)
        or not outcome.observation.cleanup.dispatch_permitted
        or attempt.ended_at_utc is None
    ):
        return "unknown", "probe process did not settle safely"
    source_times = {
        _parse_timestamp(window.source_observed_at_utc)
        for window in observation.windows
    }
    started = _parse_timestamp(attempt.started_at_utc)
    ended = _parse_timestamp(attempt.ended_at_utc)
    source_time = next(iter(source_times)) if len(source_times) == 1 else None
    if (
        source_time is None
        or started is None
        or ended is None
        or not started <= source_time <= ended
    ):
        return "unknown", "probe telemetry was not produced during this probe"
    if any(window.state == "exhausted" for window in observation.windows):
        return "exhausted", "fresh scoped telemetry reports an exhausted Codex window"
    if outcome.exit_status != 0:
        return "unknown", "available quota telemetry accompanied a failed probe"
    return "available", "successful probe produced fresh scoped available windows"


def _decode_selected_rows(content: bytes, /) -> list[dict[str, object]] | None:
    """Decode projected JSONL rows while retaining no transcript content.

    Returns:
        Decoded projected row objects or ``None`` on invalid UTF-8 or JSON.
    """
    try:
        text = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return None
    rows: list[dict[str, object]] = []
    for line in text.splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            return None
        if not isinstance(row, dict):
            return None
        rows.append(row)
    return rows


def _parse_token_count_record(row: dict[str, object], /) -> _TokenCountRecord | None:
    """Validate one consumed token-count event into typed quota values.

    Returns:
        The quota record, or None when the consumed fields are invalid.
    """
    try:
        record = _RawTokenRow.model_validate(row)
    except ValidationError:
        return None
    limits = record.payload.rate_limits
    return _TokenCountRecord(
        record.timestamp,
        record.ordinal,
        _QuotaWindowValues(limits.primary.used_percent, limits.primary.resets_at),
        _QuotaWindowValues(limits.secondary.used_percent, limits.secondary.resets_at),
    )


def _optional_reset_timestamp(value: object, /) -> str | None:
    """Parse an optional reset hint without invalidating usage telemetry.

    Returns:
        A canonical UTC hint, or None when the hint is missing or invalid.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    try:
        reset = datetime.fromtimestamp(value, UTC)
    except OverflowError, OSError, ValueError:
        return None
    return _format_timestamp(reset)


def _unknown_observation(
    scope: QuotaScope | None,
    read_at_utc: str,
    coordinate: str | None,
    diagnostic: str,
    /,
) -> QuotaObservation:
    """Create an explicit unscoped-or-scoped unknown observation.

    Returns:
        Both required Codex windows with unknown state and the diagnostic.
    """
    return QuotaObservation(
        scope=scope,
        read_at_utc=read_at_utc,
        source_coordinate=coordinate,
        windows=(
            QuotaWindowObservation(
                window_id=QuotaWindowId("codex_primary_300m"),
                state="unknown",
                usage_percent=None,
                reset_at_utc=None,
                source_observed_at_utc=None,
                source_sequence=None,
                source="codex-cli-0.164.0-session",
                diagnostic=diagnostic,
            ),
            QuotaWindowObservation(
                window_id=QuotaWindowId("codex_secondary_10080m"),
                state="unknown",
                usage_percent=None,
                reset_at_utc=None,
                source_observed_at_utc=None,
                source_sequence=None,
                source="codex-cli-0.164.0-session",
                diagnostic=diagnostic,
            ),
        ),
        diagnostic=diagnostic,
    )


def _as_unknown(observation: QuotaObservation, diagnostic: str, /) -> QuotaObservation:
    """Preserve source facts while making every window inconclusive.

    Returns:
        An observation copy with every window state set to unknown.
    """
    return observation.model_copy(
        update={
            "windows": tuple(
                window.model_copy(update={"state": "unknown", "diagnostic": diagnostic})
                for window in observation.windows
            ),
            "diagnostic": diagnostic,
        }
    )


def _parse_timestamp(value: object, /) -> datetime | None:
    """Parse an aware ISO timestamp and normalize it to UTC.

    Returns:
        The UTC timestamp or ``None`` when the value is malformed or naive.
    """
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(UTC)


def _format_timestamp(value: datetime, /) -> str:
    """Serialize an aware timestamp as a canonical UTC string.

    Returns:
        An ISO-8601 UTC timestamp ending in ``Z``.
    """
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
