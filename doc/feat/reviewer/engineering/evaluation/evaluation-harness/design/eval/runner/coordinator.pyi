# SPDX-License-Identifier: Apache-2.0
"""Own async scheduling, attempt lifecycle gates, cancellation, and accounting."""

from dataclasses import dataclass

from ..evidence import EvidenceStore  # ruff: ignore[relative-imports]
from ..model import HarnessConfig, RunRecord  # ruff: ignore[relative-imports]
from .ports import (
    AttemptCall,
    BoundRun,
    OutcomeClassifier,
    QuotaStatusReader,
    Runtime,
)

@dataclass(frozen=True)
class Coordinator:
    """Dispatch calls and retries through the existing supervisor boundary."""

    attempt: AttemptCall
    classifier: OutcomeClassifier
    quota_status: QuotaStatusReader
    runtime: Runtime

    async def run(
        self,
        bound_run: BoundRun,
        evidence: EvidenceStore,
        config: HarnessConfig,
        /,
    ) -> RunRecord:
        """Run the frozen calls with global quota and call-local retry gates.

        Own stop latching, task and signal cancellation, active cleanup waits,
        event persistence, semaphore lifetime, and truthful not-started status.
        It delegates one attempt to the supplied AttemptCall and never creates
        or cleans up a subprocess itself.
        """
        ...
