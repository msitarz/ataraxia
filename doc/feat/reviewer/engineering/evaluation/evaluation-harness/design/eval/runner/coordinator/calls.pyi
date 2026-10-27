# SPDX-License-Identifier: Apache-2.0
"""Call-local attempt settlement, retry eligibility, and cancellable backoff."""

from asyncio import Semaphore

from script.eval.evidence import EvidenceStore
from script.eval.model import HarnessConfig
from script.eval.runner.ports import (
    AttemptCall,
    OutcomeClassifier,
    QuotaStatusReader,
    Runtime,
)

from .control import RunControl
from .state import CallState, Queued

class CallOwner:
    """Own and expose one call's current state through all submitted effects."""

    def __init__(
        self,
        initial: Queued,
        config: HarnessConfig,
        control: RunControl,
        slots: Semaphore,
        attempt: AttemptCall,
        classifier: OutcomeClassifier,
        quota_status: QuotaStatusReader,
        evidence: EvidenceStore,
        runtime: Runtime,
    ) -> None: ...
    @property
    def state(self) -> CallState: ...
    async def run(self) -> CallState:
        """Settle the call or stop it; retain submitted writes during cancellation."""
        ...
