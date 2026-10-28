# SPDX-License-Identifier: Apache-2.0
"""Pure projection of lifecycle state and durable history."""

from dataclasses import dataclass
from typing import Literal

from script.eval.model import QuotaObservation, RunId
from script.eval.runner.coordinator.call_states import CallState
from script.eval.runner.coordinator.quota_states import QuotaHistory, QuotaState
from script.eval.runner.ports import ProgressFinalStatus, ProgressSnapshot

@dataclass(frozen=True)
class ProgressView:
    """One coherent owner snapshot and explicit clock inputs for projection."""

    run_id: RunId
    phase: Literal["running", "quota_paused", "stopping", "final"]
    final_status: ProgressFinalStatus | None
    calls: tuple[CallState, ...]
    quota: QuotaState
    probes: QuotaHistory
    observation: QuotaObservation | None
    monotonic_now: float
    utc_now: str

def project(view: ProgressView, /) -> ProgressSnapshot:
    """Derive disjoint call, attempt, and probe counts without effects."""
    ...
