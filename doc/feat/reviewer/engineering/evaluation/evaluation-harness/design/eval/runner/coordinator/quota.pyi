# SPDX-License-Identifier: Apache-2.0
"""Exploratory quota recovery and bounded async ownership."""

from script.eval.evidence import EvidenceStore
from script.eval.model import HarnessConfig, QuotaObservation
from script.eval.runner.ports import QuotaStatusReader, Runtime

from .coordinator import RunControl
from .state import Draining, QuotaHistory, QuotaState

class QuotaOwner:
    """Own the current pause and its durable probe history."""

    def __init__(
        self,
        initial: Draining,
        history: QuotaHistory,
        config: HarnessConfig,
        control: RunControl,
        reader: QuotaStatusReader,
        evidence: EvidenceStore,
        runtime: Runtime,
    ) -> None: ...
    @property
    def state(self) -> QuotaState: ...
    @property
    def history(self) -> QuotaHistory: ...
    @property
    def observation(self) -> QuotaObservation | None: ...
    async def recover(self) -> QuotaState:
        """Recover after the run owner drains and persists all active attempts."""
        ...
