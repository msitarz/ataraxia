# SPDX-License-Identifier: Apache-2.0
"""Exclusive run-artifact creation and append-only evidence persistence port."""

from pathlib import Path
from typing import Protocol

from .model import (
    AttemptEvidence,
    AttemptNumber,
    AttemptRecord,
    CallId,
    FrozenPlan,
    PreparedEvidence,
    RunId,
    RunRecord,
    WaitEvent,
)

class EvidenceStore(Protocol):
    """Exclusive, append-only run evidence boundary."""

    def create(self, output_directory: Path, plan: FrozenPlan, /) -> PreparedEvidence:
        """Exclusively create storage and persist plan/instructions pre-dispatch.

        Returns paths to the durable plan and staged model instruction file.
        No supervisor process may launch before this call succeeds.
        """
        ...

    def record_attempt(
        self,
        run_id: RunId,
        call_id: CallId,
        position: int,
        attempt_number: AttemptNumber,
        evidence: AttemptEvidence,
        /,
    ) -> AttemptRecord:
        """Persist an explicitly associated attempt without replacing evidence."""
        ...

    def record_wait_event(self, event: WaitEvent, /) -> None:
        """Durably append wait start, selected reset, recheck, and end events.

        The coordinator records each event as it happens; a final run summary
        alone is not sufficient evidence of a live wait.
        """
        ...

    def finalize(self, record: RunRecord, /) -> None:
        """Persist truthful final accounting; failure leaves the run incomplete."""
        ...
