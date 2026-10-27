# SPDX-License-Identifier: Apache-2.0
"""Run ownership, bounded workers, shutdown, and finalization."""

from script.eval.evidence import EvidenceStore
from script.eval.model import RunRecord
from script.eval.runner.ports import (
    AttemptCall,
    BoundRun,
    OutcomeClassifier,
    ProgressSink,
    QuotaStatusReader,
    Runtime,
)

class Coordinator:
    """Own one provider-bound run and its retained tasks through settlement."""

    def __init__(
        self,
        bound_run: BoundRun,
        evidence: EvidenceStore,
        attempt: AttemptCall,
        classifier: OutcomeClassifier,
        quota_status: QuotaStatusReader,
        runtime: Runtime,
        progress: ProgressSink,
    ) -> None: ...
    async def run(self) -> RunRecord:
        """Finalize truthful accounting and propagate primary cancellation."""
        ...
