# SPDX-License-Identifier: Apache-2.0
"""Fail-closed adapter boundary for source-backed Codex quota observations."""

from dataclasses import dataclass
from typing import Protocol

from ...model import QuotaObservation, QuotaScope  # ruff: ignore[relative-imports]
from ..ports import QuotaStatusReader  # ruff: ignore[relative-imports]

class RawCodexQuotaStatusSource(Protocol):
    """Injected raw capture; this is not a claim about a Codex API."""

    async def read_status_bytes(self) -> bytes | None:
        """Return captured bytes or None when no verified source is available."""
        ...

@dataclass(frozen=True)
class CodexQuotaStatusReader(QuotaStatusReader):
    """Map Codex's required windows into provider-neutral quota observations.

    Always represent the five-hour and weekly windows; if either is missing,
    malformed, or unrecognized, its slot is unknown or unavailable. Validate
    any external scope identity against ``expected_scope`` at this adapter
    boundary. Unknown or mismatched identity returns no verified observation
    scope and cannot authorize a wait. No endpoint, app-server schema, or exec
    schema is assumed; source and identity support remain unverified. Persist
    only sanitized source and diagnostic labels, never account PII or secrets.
    """

    source: RawCodexQuotaStatusSource
    expected_scope: QuotaScope | None

    async def read(self) -> QuotaObservation: ...
