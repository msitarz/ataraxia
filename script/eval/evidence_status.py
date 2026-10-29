# SPDX-License-Identifier: Apache-2.0
"""Track whether a standalone run's required evidence was finalized."""

from collections.abc import Callable
from pathlib import Path

from script.eval.evidence import EvidenceStore
from script.eval.model import (
    AttemptEvidence,
    AttemptNumber,
    AttemptRecord,
    CallId,
    FrozenPlan,
    PreparedEvidence,
    QuotaProbeEvidence,
    QuotaProbeLifecycleInput,
    QuotaProbeSettled,
    QuotaTelemetryEvent,
    RetryAssessment,
    RunId,
    RunRecord,
    WaitEvent,
)


class EvidenceStatus:
    """Observe persistence without changing errors or recording behavior."""

    def __init__(self, factory: Callable[[], EvidenceStore]) -> None:
        """Retain the factory without constructing a store for a dry run."""
        self.factory = factory
        self._store: EvidenceStore | None = None
        self.started = False
        self.finalized = False
        self.failed = False

    async def create(
        self, output_directory: Path, plan: FrozenPlan, /
    ) -> PreparedEvidence:
        """Submit exclusive preparation and retain its successful result.

        Returns:
            The store's prepared evidence.
        """
        self.started = True
        if self._store is None:
            self._store = self.factory()
        result = await self._store.create(output_directory, plan)
        return result

    async def record_attempt(
        self,
        run_id: RunId,
        call_id: CallId,
        position: int,
        attempt_number: AttemptNumber,
        evidence: AttemptEvidence,
        retry_assessment: RetryAssessment | None,
        /,
    ) -> AttemptRecord:
        """Forward a durable attempt.

        Returns:
            The store's attempt record.
        """
        try:
            return await self._require_store().record_attempt(
                run_id, call_id, position, attempt_number, evidence, retry_assessment
            )
        except Exception:
            self.failed = True
            raise

    async def record_wait_event(self, event: WaitEvent, /) -> None:
        """Forward a wait event."""
        try:
            await self._require_store().record_wait_event(event)
        except Exception:
            self.failed = True
            raise

    async def record_quota_probe_event(
        self, event: QuotaProbeLifecycleInput, /
    ) -> None:
        """Forward a probe event."""
        try:
            await self._require_store().record_quota_probe_event(event)
        except Exception:
            self.failed = True
            raise

    async def record_quota_probe_settled(
        self, evidence: QuotaProbeEvidence, /
    ) -> QuotaProbeSettled:
        """Forward settled probe evidence.

        Returns:
            The store's settled probe record.
        """
        try:
            return await self._require_store().record_quota_probe_settled(evidence)
        except Exception:
            self.failed = True
            raise

    async def record_quota_telemetry(self, event: QuotaTelemetryEvent, /) -> None:
        """Forward a telemetry event."""
        try:
            await self._require_store().record_quota_telemetry(event)
        except Exception:
            self.failed = True
            raise

    async def finalize(self, record: RunRecord, /) -> None:
        """Retain successful finalization after the store settles."""
        try:
            await self._require_store().finalize(record)
        except Exception:
            self.failed = True
            raise
        self.finalized = True

    def _require_store(self) -> EvidenceStore:
        """Return the submitted store after preparation begins.

        Returns:
            The store selected by the deferred factory.

        Raises:
            RuntimeError: Preparation was never submitted.
        """
        if self._store is None:
            raise RuntimeError("evidence creation was not submitted")
        return self._store
