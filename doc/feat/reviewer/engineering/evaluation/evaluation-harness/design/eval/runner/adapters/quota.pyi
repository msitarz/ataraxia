# SPDX-License-Identifier: Apache-2.0
"""Fail-closed adapter boundary for source-backed Codex quota observations."""

from dataclasses import dataclass
from typing import Protocol

from ...model import QuotaObservation  # ruff: ignore[relative-imports]
from ..ports import QuotaStatusReader  # ruff: ignore[relative-imports]

class RawQuotaStatusSource(Protocol):
    """Injected capture source; this is not a claim about a Codex API."""

    async def read_status_bytes(self) -> bytes | None:
        """Return captured bytes or None when no verified source is available."""
        ...

@dataclass(frozen=True)
class CodexQuotaStatusReader(QuotaStatusReader):
    """Map a verified raw source to both windows, otherwise report unknown.

    No endpoint, app-server schema, or exec schema is assumed. Concrete source
    support stays unverified until the Work's evidence establishes its format.
    """

    source: RawQuotaStatusSource

    async def read(self) -> QuotaObservation: ...
