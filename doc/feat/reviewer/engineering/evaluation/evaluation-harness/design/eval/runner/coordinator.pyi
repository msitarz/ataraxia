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
    """Dispatch calls and own the optional lifecycle-managed quota monitor."""

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
        """Run frozen calls with global quota, polling, and call-local retry gates.

        Own stop latching, task and signal cancellation, active cleanup waits,
        event persistence, semaphore lifetime, and truthful not-started status.
        When quota waiting is enabled, it explicitly authorizes polling and
        starts one async monitor task that polls during active and
        paused periods at the configured cadence. Polling is single-flight,
        outside evaluation semaphore slots, and uses an earlier reset hint only
        to schedule a check. No probe or session read occurs in default-off or
        dry-run execution.

        A conclusive exhausted observation from either a settled evaluation or
        an active poll closes the same global dispatch gate. Let active calls
        settle and persist before starting another poll; an already-running
        probe may finish under supervision.

        After each settled evaluation attempt, pass its call and attempt identity
        and captured evidence to the same quota port for passive session
        ingestion. Persist that observation separately; keep its producer
        timestamp and source sequence distinct from read time. The source
        adapter orders evidence before returning it so delayed older available
        snapshots cannot supersede newer exhaustion. Unknown/mismatched scope or
        inconclusive freshness fails closed. Once a quota failure pauses global
        dispatch, let active evaluations settle and persist before starting any
        new probe; an already-running supervised probe still settles and records
        before resumption or shutdown.

        Append a probe-start event before calling the port. The port returns an
        ephemeral ``QuotaProbeEvidence`` containing supervisor objects; pass it
        to the evidence store, which writes raw streams as artifacts and returns
        a scalar ``QuotaProbeSettled`` projection with request settings, cleanup,
        source association, timestamps, observation, and available usage. Never
        serialize supervisor exceptions or arbitrary runtime objects. Probe IDs
        are independent of evaluation attempt numbers. The monitor stops launching
        probes at an explicit operational budget limit. With no configured
        count cap, caller-owned operational limits still govern use. A valid
        probe reporting continued quota
        exhaustion remains paused and schedules the next check; unknown,
        infrastructure failure, output overflow, event-write failure, unsafe
        cleanup, or uncertain acquisition latches stop. The monitor is cancelled
        and joined on both normal completion and shutdown after any in-flight
        probe safely settles.

        Use a single monitor sleep per check cycle; reset hints shorten that
        cycle, and no parallel reset timer is started. Persist each cadence
        wait's start and completion through the wait-event port, linked by
        probe/wait ID and retaining the scheduled check and reset hint. Record
        poll start and settlement as separate probe events so wait, check, source
        observation, and shutdown evidence are durable as they occur rather than
        only in final run metadata. A pause ends successfully only with a fresh
        positive observation, recorded as ``quota_available``; hint arrival
        merely schedules a check.

        Before using quota data, require the bound CLI scope, reader's expected
        scope, passive snapshot scope, active probe request scope, and returned
        observation scope to be present and equal. The current run has one
        binding shared by every call, so a verified quota pause remains global.
        It delegates one evaluation attempt to the supplied
        AttemptCall and never creates or cleans up a subprocess itself. The
        quota port alone owns construction and supervision of its separate
        fixed-condition Codex probe; the coordinator does not invoke a CLI.
        """
        ...
