# SPDX-License-Identifier: Apache-2.0
"""Fail-closed adapter boundary for source-backed Codex quota observations."""

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from script.process_supervisor import AttemptRequest, DispatchStop

from ...model import (  # ruff: ignore[relative-imports]
    AttemptEvidence,
    AttemptNumber,
    CallId,
    QuotaProbeRequest,
    QuotaProbeResult,
    QuotaScope,
    QuotaTelemetrySnapshot,
    QuotaWindowId,
    QuotaWindowObservation,
    RunId,
)
from ..ports import (  # ruff: ignore[relative-imports]
    AttemptCall,
    QuotaStatusReader,
    Runtime,
)

class RawCodexQuotaStatusSource(Protocol):
    """Injected local-session lookup; schema and discovery remain unverified."""

    async def read_session_for_thread(
        self, thread_id: str, /
    ) -> RawCodexSessionSnapshot | None:
        """Return only the session associated with this invocation's thread ID."""
        ...

@dataclass(frozen=True)
class RawCodexSessionSnapshot:
    """Untrusted session bytes and a sanitized source coordinate."""

    content: bytes
    source_coordinate: str

@dataclass(frozen=True)
class CodexQuotaSettings:
    """Probe CLI identity and finite supervisor limits; recipe remains unverified."""

    executable_path: Path
    empty_read_only_cwd: Path
    timeout_seconds: float
    cleanup_timeout_seconds: float
    output_limit_bytes: int
    grace_seconds: float

@dataclass
class CodexQuotaStatusReader(QuotaStatusReader):
    """One Codex adapter for passive session ingestion and active supervised polls.

    It owns fixed Luna/none probe request construction, invocation through the
    injected existing supervisor call, thread-ID extraction and local-session
    correlation, and mapping of both required five-hour and weekly windows. If
    either window, identity, producer time, or freshness is missing, malformed,
    stale, or unrecognized, the observation is unknown/unavailable and cannot
    authorize resumption. No endpoint or exec schema is assumed: file discovery,
    source schema, thread correlation, scope association, and freshness rules
    remain unverified. Persist sanitized coordinates only, never account PII.
    """

    source: RawCodexQuotaStatusSource
    expected_scope: QuotaScope | None
    settings: CodexQuotaSettings
    attempt_call: AttemptCall
    runtime: Runtime
    _latest_by_window: dict[QuotaWindowId, tuple[QuotaWindowObservation, str]] = field(
        init=False, default_factory=dict, repr=False
    )
    _order_lock: asyncio.Lock = field(
        init=False, default_factory=asyncio.Lock, repr=False
    )

    async def observe_settled_attempt(
        self,
        call_id: CallId,
        attempt_number: AttemptNumber,
        evidence: AttemptEvidence,
        expected_scope: QuotaScope,
        /,
    ) -> QuotaTelemetrySnapshot: ...
    async def poll(
        self, request: QuotaProbeRequest, stop_dispatch: DispatchStop, /
    ) -> QuotaProbeResult:
        """Build fixed probe request, call supervisor, then correlate its session."""
        ...

    def _request(self, run_id: RunId, /) -> AttemptRequest:
        """Build the requested Luna/none, minimal, tool-free empty-cwd request.

        Plugins and MCP are disabled and the directory is read-only. The exact
        unattended flag recipe remains unverified and must be checked before an
        implementation claims this effective condition.
        """
        ...

    async def _observation(
        self,
        scope: QuotaScope,
        thread_id: str | None,
        /,
    ) -> QuotaTelemetrySnapshot:
        """Normalize schema and source age, order typed windows, and fail closed.

        Compare producer time first; use a sequence only within the same source
        coordinate. An older observation is inconclusive and never replaces a
        newer cached window or authorizes availability.
        """
        ...
