# SPDX-License-Identifier: Apache-2.0
"""Historical coordinator type sketch; runtime code is authoritative.

The active API is ``script.eval.runner.coordinator.Coordinator``. This sketch
records reviewed intent only and does not define the current signature.
"""

from dataclasses import dataclass

from ..evidence import EvidenceStore  # ruff: ignore[relative-imports]
from ..model import HarnessConfig, RunRecord  # ruff: ignore[relative-imports]
from .ports import (
    AttemptCall,
    BoundRun,
    OutcomeClassifier,
    ProgressSink,
    QuotaStatusReader,
    Runtime,
)

@dataclass(frozen=True)
class Coordinator:
    """Dispatch calls and own the optional lifecycle-managed quota monitor."""

    attempt: AttemptCall
    classifier: OutcomeClassifier
    quota_status: QuotaStatusReader
    runtime: Runtime
    progress: ProgressSink

    async def run(
        self,
        bound_run: BoundRun,
        evidence: EvidenceStore,
        config: HarnessConfig,
        /,
    ) -> RunRecord:
        """Execute the bound frozen calls and return truthful run accounting.

        The coordinator owns dispatch gates, retry allowances, task lifecycle,
        cleanup waits, and stop latching. ``AttemptCall`` supervises each
        evaluation invocation; ``QuotaStatusReader`` ingests settled-attempt
        observations and runs separate quota probes; ``EvidenceStore`` persists
        events and process projections; ``Runtime`` supplies time and waits.

        Quota monitoring is opt-in and single-flight. Default-off and dry-run
        runs perform no quota probes. The coordinator associates observations
        with the bound scope and uses the current pause ID to gate resumption;
        while paused it waits for active evaluation evidence to settle before a
        new probe. Active-period probes may run alongside evaluation calls.
        Provider freshness/completeness and retry eligibility belong to their
        adapters and policy. Unknown or mismatched scope and inconclusive quota
        evidence fail closed; unsafe cleanup and evidence-write failure latch
        stop.

        Probe lifecycle events are durable before their effects. Prelaunch
        cancellation records no process and spends no probe budget; launched
        probes are projected from ``QuotaProbeEvidence`` by the evidence store.
        Cancellation joins the monitor and waits for supervised cleanup. See
        ``architecture.md#async-dispatch-coordinator`` for scheduling and gate
        sequencing.

        Progress is projected from these same lifecycle states. Durable evidence
        writes precede snapshots that claim persisted facts; ordinary sink I/O
        errors do not change the run. Final progress distinguishes successful,
        failed, cancelled, and incomplete-evidence outcomes.
        """
        ...
