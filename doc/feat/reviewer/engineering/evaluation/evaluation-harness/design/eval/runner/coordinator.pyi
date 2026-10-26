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

        After each settled evaluation attempt, pass its captured evidence to the
        same quota port for passive ingestion. The coordinator associates its
        returned observation with call and attempt identity in the telemetry
        event, and compares its scope with the bound run. Keep producer timestamp
        and source sequence distinct from read time. The source adapter orders
        evidence before returning it so delayed older available observations
        cannot supersede newer exhaustion. Unknown/mismatched scope or
        inconclusive freshness fails closed. Once a quota failure pauses global
        dispatch, let active evaluations settle and persist before starting any
        new probe; an already-running supervised probe still settles and records
        before resumption or shutdown. Associate each active pause with its
        stable quota-wait ID. A probe request captures that ID when it starts;
        a probe started before the current pause (including active-period polls)
        may settle and persist but cannot reopen it. Only a fresh, positive
        same-scope result from a probe started for the current pause can confirm
        availability after the active-evaluation settlement barrier.

        Persist each scheduled-check event with creation time, due time,
        interval, and optional reset hint. Do not perform that scheduled
        probe's source read or launch its model before the due time; passive
        observation of settled evaluation evidence may continue during the
        cadence wait. If a pending check is cancelled or
        superseded before dispatch, append a cancellation event with its actual
        monotonic wait duration and end cause; it has no process record and
        consumes no probe budget. A schedule ID ties these transitions together
        without adding cadence waits to the wait ledger.

        After due time, gate on stop and quota budget. While quota is paused,
        also wait for active evaluations to settle and persist, then associate
        the probe with the current pause generation. During active-period
        monitoring, do not wait for unrelated evaluation calls to settle. At
        actual dispatch, create the start event with the then-current pause ID
        (or none) and coordinator dispatch time, and persist it before calling
        the port. The port returns an
        ephemeral ``QuotaProbeEvidence`` containing shared ``ProcessEvidence``
        and a separate quota assessment; pass it to the evidence store, which
        writes one settled lifecycle event and raw streams as artifacts. Only
        actual dispatch consumes the optional probe budget. A cancellation
        after process launch settles as a probe record with the supervisor's
        cancellation outcome; it is not a prelaunch-cancel event. Process
        outcome (including timeout, overflow, cancellation, error, or no launch)
        never implies quota availability. Never serialize supervisor exceptions
        or arbitrary runtime objects. Probe IDs
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
        cycle, and no parallel reset timer is started. A scheduled lifecycle
        event records the cadence decision; start, settlement, and prelaunch
        cancellation record actual progress. The separate quota-pause and
        capacity-backoff waits remain in the wait ledger. A pause ends
        successfully only with a fresh
        positive observation, recorded as ``quota_available``; hint arrival
        merely schedules a check. Compare the probe's captured pause ID with the
        current pause ID before accepting availability, not completion or read
        time alone.

        Before using quota data, require the bound CLI scope, reader's expected
        scope, passive observation scope, active probe request scope, and returned
        observation scope to be present and equal. The current run has one
        binding shared by every call, so a verified quota pause remains global.
        It delegates one evaluation attempt to the supplied
        AttemptCall and never creates or cleans up a subprocess itself. The
        quota port alone owns construction and supervision of its separate
        fixed-condition Codex probe; the coordinator does not invoke a CLI.
        """
        ...
