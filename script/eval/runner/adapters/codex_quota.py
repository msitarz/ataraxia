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
from typing import BinaryIO, Protocol
from uuid import UUID

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
    latest_ordinals: dict[str, int] = field(default_factory=dict)

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
        async with self.lock:
            prior_ordinal = self.latest_ordinals.get(coordinate)
            issue = _ordering_issue(
                coordinate,
                timestamp,
                sequence,
                prior_ordinal,
                self.latest_timestamp,
                self.latest_ordinals,
            )
            if issue is not None:
                return _as_unknown(observation, issue)
            self.latest_timestamp = timestamp
            self.latest_ordinals[coordinate] = sequence
        return observation


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
    latest_ordinals: dict[str, int],
    /,
) -> str | None:
    """Return a precise reason when one source snapshot regresses ordering."""
    if prior_ordinal is not None and sequence <= prior_ordinal:
        return "quota source sequence did not advance"
    if latest_timestamp is None:
        return None
    if timestamp < latest_timestamp:
        return "quota snapshot is older than a prior observation"
    if timestamp == latest_timestamp and coordinate not in latest_ordinals:
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
    rows = _decode_selected_rows(snapshot.content)
    if rows is None:
        return _unknown_observation(
            None,
            read_at_utc,
            snapshot.source_coordinate,
            "session telemetry is malformed",
        )
    session_scope, identity_issue = _session_scope(rows, snapshot, scope)
    if identity_issue is not None:
        return _unknown_observation(
            None, read_at_utc, snapshot.source_coordinate, identity_issue
        )
    token_rows = _token_count_rows(rows)
    if not token_rows:
        return _unknown_observation(
            None,
            read_at_utc,
            snapshot.source_coordinate,
            "session telemetry is incomplete",
        )
    latest = _latest_rate_limit_record(token_rows, read_at, max_observation_age_seconds)
    if latest is None:
        return _unknown_observation(
            session_scope,
            read_at_utc,
            snapshot.source_coordinate,
            "rate-limit rows are malformed, stale, or out of order",
        )
    source_sequence, observed_at, limits = latest
    if not _has_supported_allowance_shape(limits):
        return _unknown_observation(
            session_scope,
            read_at_utc,
            snapshot.source_coordinate,
            "rate-limit allowance fields are unsupported",
        )
    windows = _quota_windows(source_sequence, observed_at, limits)
    if windows is None:
        return _unknown_observation(
            session_scope,
            read_at_utc,
            snapshot.source_coordinate,
            "required quota windows are incomplete",
        )
    return QuotaObservation(
        scope=session_scope,
        read_at_utc=_format_timestamp(read_at),
        source_coordinate=snapshot.source_coordinate,
        windows=windows,
        diagnostic=None,
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
    rows: list[dict[str, object]],
    snapshot: RawCodexSessionSnapshot,
    expected_scope: QuotaScope | None,
    /,
) -> tuple[QuotaScope | None, str | None]:
    """Validate one supported session identity against the configured scope.

    Returns:
        The matching scope and no issue, or an unscoped failure diagnostic.
    """
    requested_thread_id = _canonical_uuid(snapshot.requested_thread_id)
    metadata = [row for row in rows if row.get("type") == "session_meta"]
    if requested_thread_id is None or len(metadata) != 1:
        return None, "session metadata or requested thread identity is incomplete"
    payload = metadata[0].get("payload")
    if not isinstance(payload, dict):
        return None, "session metadata is malformed"
    if (
        payload.get("id") != requested_thread_id
        or payload.get("session_id") != requested_thread_id
    ):
        return None, "session identity does not match the invocation"
    if payload.get("cli_version") != "0.164.0":
        return None, "session CLI version is unsupported"
    provider = payload.get("model_provider")
    account_id = payload.get("creator_account_id")
    user_id = payload.get("creator_user_id")
    if (
        not isinstance(provider, str)
        or not isinstance(account_id, str)
        or not isinstance(user_id, str)
    ):
        return None, "session quota identity is incomplete"
    if not provider.strip() or not account_id.strip() or not user_id.strip():
        return None, "session quota identity is incomplete"
    try:
        observed_scope = codex_quota_scope_from_identity(provider, account_id, user_id)
    except ValueError:
        return None, "session provider is unsupported"
    if expected_scope is None or observed_scope != expected_scope:
        return None, "session quota scope is not verified"
    return expected_scope, None


def _token_count_rows(rows: list[dict[str, object]], /) -> list[dict[str, object]]:
    """Select token-count events while leaving unrelated rows opaque.

    Returns:
        The selected raw event envelopes.
    """
    return [
        row
        for row in rows
        if row.get("type") == "event_msg"
        and isinstance(row.get("payload"), dict)
        and row["payload"].get("type") == "token_count"
    ]


def _latest_rate_limit_record(
    rows: list[dict[str, object]],
    read_at: datetime,
    max_age: float,
    /,
) -> tuple[int, datetime, dict[str, object]] | None:
    """Validate row order and return one recent complete rate-limit record.

    Returns:
        The latest source sequence, timestamp, and quota object when valid.
    """
    parsed = [_parse_rate_limit_row(row) for row in rows]
    if any(record is None for record in parsed):
        return None
    records = [record for record in parsed if record is not None]
    for earlier, later in pairwise(records):
        if later[0] <= earlier[0] or later[1] < earlier[1]:
            return None
    latest = records[-1]
    age = (read_at - latest[1]).total_seconds()
    return latest if 0 <= age <= max_age else None


def _quota_windows(
    sequence: int, observed_at: datetime, limits: dict[str, object], /
) -> tuple[QuotaWindowObservation, ...] | None:
    """Create the required provider-neutral Codex quota windows.

    Returns:
        Both required windows or ``None`` when either source window is invalid.
    """
    primary = _parse_window(limits.get("primary"), "primary", 300)
    secondary = _parse_window(limits.get("secondary"), "secondary", 10080)
    if primary is None or secondary is None:
        return None
    return tuple(
        QuotaWindowObservation(
            window_id=QuotaWindowId(window_id),
            state="exhausted" if usage >= 100 else "available",
            usage_percent=usage,
            reset_at_utc=reset_at,
            source_observed_at_utc=_format_timestamp(observed_at),
            source_sequence=sequence,
            source="codex-cli-0.164.0-session",
            diagnostic=None,
        )
        for window_id, usage, reset_at in (primary, secondary)
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
        f"model_reasoning_effort={json.dumps('none')}",
        "-c",
        f"model_instructions_file={json.dumps(str(settings.probe_instructions_file))}",
        "-c",
        "agents.enabled=false",
        "-c",
        "skills.bundled.enabled=false",
        "-c",
        "memories.use_memories=false",
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
    """Require fresh scoped telemetry and a successful probe to resume dispatch.

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
    if (
        attempt.control_flow != "returned"
        or not isinstance(attempt.outcome, Completed)
        or attempt.outcome.exit_status != 0
        or attempt.ended_at_utc is None
    ):
        return "unknown", "probe process did not complete successfully"
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


def _parse_rate_limit_row(
    row: dict[str, object], /
) -> tuple[int, datetime, dict[str, object]] | None:
    """Validate the consumed envelope and timestamp/ordinal pair.

    Returns:
        A valid ordinal, producer timestamp, and rate-limit object.
    """
    ordinal = row.get("ordinal")
    timestamp = _parse_timestamp(row.get("timestamp"))
    payload = row.get("payload")
    if not isinstance(ordinal, int) or isinstance(ordinal, bool) or ordinal < 0:
        return None
    if timestamp is None or not isinstance(payload, dict):
        return None
    if payload.get("type") != "token_count":
        return None
    limits = payload.get("rate_limits")
    if not isinstance(limits, dict) or limits.get("limit_id") != "codex":
        return None
    return ordinal, timestamp, limits


def _has_supported_allowance_shape(limits: dict[str, object], /) -> bool:
    """Reject unsupported additional limits or balances.

    Returns:
        Whether the source represents only the two modeled quota windows.
    """
    required_fields = {
        "credits",
        "individual_limit",
        "spend_control_reached",
        "rate_limit_reached_type",
    }
    if not required_fields.issubset(limits):
        return False
    credits = limits.get("credits")
    if not isinstance(credits, dict):
        return False
    balance = credits.get("balance")
    if not isinstance(balance, str):
        return False
    try:
        parsed_balance = Decimal(balance)
    except InvalidOperation:
        return False
    return (
        credits.get("has_credits") is False
        and credits.get("unlimited") is False
        and parsed_balance.is_finite()
        and parsed_balance == 0
        and limits.get("individual_limit") is None
        and limits.get("spend_control_reached") is None
        and limits.get("rate_limit_reached_type") is None
    )


def _parse_window(
    value: object, window: str, expected_minutes: int, /
) -> tuple[str, float, str] | None:
    """Validate one fixed Codex quota-window record.

    Returns:
        The normalized window ID, usage percentage, and reset hint.
    """
    if not isinstance(value, dict):
        return None
    used_percent = value.get("used_percent")
    window_minutes = value.get("window_minutes")
    resets_at = value.get("resets_at")
    if isinstance(used_percent, bool) or not isinstance(used_percent, (int, float)):
        return None
    try:
        usage = float(used_percent)
    except OverflowError:
        return None
    if not math.isfinite(usage) or usage < 0:
        return None
    if isinstance(window_minutes, bool) or not isinstance(window_minutes, int):
        return None
    if window_minutes != expected_minutes:
        return None
    if isinstance(resets_at, bool) or not isinstance(resets_at, int):
        return None
    try:
        reset = datetime.fromtimestamp(resets_at, UTC)
    except OverflowError, OSError, ValueError:
        return None
    return (
        f"codex_{window}_{window_minutes}m",
        usage,
        _format_timestamp(reset),
    )


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
