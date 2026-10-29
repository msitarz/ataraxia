# SPDX-License-Identifier: Apache-2.0
"""Historical reviewed signature sketch for Codex quota observation wiring.

Runtime ``script/eval/runner/adapters/codex_quota.py`` is authoritative. It
currently supplies typed source and supervisor wiring around explicit pending
leaves; this sketch does not establish a verified source or quota behavior.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from script.process_supervisor import DispatchStop

from ...model import (  # ruff: ignore[relative-imports]
    AttemptEvidence,
    QuotaObservation,
    QuotaProbeEvidence,
    QuotaProbeRequest,
    QuotaScope,
)
from ..ports import (  # ruff: ignore[relative-imports]
    AttemptCall,
    QuotaStatusReader,
    Runtime,
)

class RawCodexQuotaStatusSource(Protocol):
    """Codex-only local-session lookup; schema and discovery remain unverified."""

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
    probe_instructions_file: Path
    timeout_seconds: float
    cleanup_timeout_seconds: float
    output_limit_bytes: int
    grace_seconds: float

@dataclass
class CodexQuotaStatusReader(QuotaStatusReader):
    """One Codex adapter for passive session ingestion and active supervised polls.

    The proposed connection pins the first validated evaluation session's scope.
    Later evaluations and probes must match it, even when quota windows are absent.
    Unavailable or mismatched identity cannot authorize further dispatch.

    It owns fixed Luna/none probe request construction, invocation through the
    injected existing supervisor call, thread-ID extraction and local-session
    correlation privately, and mapping of both required five-hour and weekly
    windows to generic observations. Thread IDs never leave this adapter. If
    either window, identity, producer time, or freshness is missing, malformed,
    stale, or unrecognized, the observation is unknown/unavailable and cannot
    authorize resumption. It orders producer timestamps and uses source sequence
    only within a single source coordinate; older evidence remains inconclusive.
    Runtime currently requires a supplied scope; proposed pinning is not yet
    implemented. Persist sanitized coordinates only, never account PII.
    """

    source: RawCodexQuotaStatusSource
    expected_scope: QuotaScope | None
    settings: CodexQuotaSettings
    attempt_call: AttemptCall
    runtime: Runtime

    async def observe_settled_attempt(
        self,
        evidence: AttemptEvidence,
        /,
    ) -> QuotaObservation: ...
    async def poll(
        self, request: QuotaProbeRequest, stop_dispatch: DispatchStop, /
    ) -> QuotaProbeEvidence:
        """Return shared process evidence and a separately classified observation."""
        ...
