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
    QuotaProbeEvidence,
    QuotaProbeSettled,
    QuotaProbeStarted,
    QuotaTelemetryEvent,
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
        """Project shared process evidence with call and attempt identity."""
        ...

    def record_wait_event(self, event: WaitEvent, /) -> None:
        """Durably append wait start, quota recheck, and end events.

        The quota start carries its scoped provider-neutral window observation
        and selected reset; the coordinator records each event as it happens.
        A final run summary alone is not sufficient evidence of a live wait.
        """
        ...

    def record_quota_probe_started(self, event: QuotaProbeStarted, /) -> None:
        """Append the scalar probe identity and schedule before invocation."""
        ...

    def record_quota_probe_settled(
        self, evidence: QuotaProbeEvidence, /
    ) -> QuotaProbeSettled:
        """Persist a shared process projection plus quota assessment.

        Store raw streams as artifacts; project exceptions to type and
        diagnostic. The returned record combines common process fields with
        probe identity and quota state, without consuming attempt numbers.
        """
        ...

    def record_quota_telemetry(self, event: QuotaTelemetryEvent, /) -> None:
        """Append a provider-neutral observation under call/attempt identity."""
        ...

    def finalize(self, record: RunRecord, /) -> None:
        """Persist truthful final accounting; failure leaves the run incomplete."""
        ...
