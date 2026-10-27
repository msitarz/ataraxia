# SPDX-License-Identifier: Apache-2.0
"""Compose the coordinator's run, attempt, quota, and evidence effects.

Scheduling gates, result conversion, and policy transitions remain explicit
pending leaves until their behavior is implemented and reviewed.
"""

import asyncio
from collections.abc import Awaitable, Callable
from contextlib import suppress
from dataclasses import dataclass, field

from script.eval.evidence import EvidenceStore
from script.eval.model import (
    AttemptEvidence,
    AttemptNumber,
    AttemptRecord,
    HarnessConfig,
    QuotaTelemetryEvent,
    RunRecord,
)
from script.eval.runner.ports import (
    AttemptCall,
    BoundRun,
    EffectiveCall,
    OutcomeClassifier,
    ProgressSink,
    QuotaStatusReader,
    Runtime,
)
from script.process_supervisor import AttemptResult, DispatchStop

type CaptureReturnedAttempt = Callable[
    [EffectiveCall, AttemptResult, str, str], AttemptEvidence
]
type ScheduleCalls = Callable[
    [
        BoundRun,
        EvidenceStore,
        Callable[
            [EffectiveCall, AttemptNumber, DispatchStop], Awaitable[AttemptRecord]
        ],
        DispatchStop,
        DispatchStopped,
    ],
    Awaitable[RunRecord],
]
type MonitorQuota = Callable[[BoundRun, DispatchStop], Awaitable[None]]
type DispatchStopped = Callable[[], bool]


@dataclass(frozen=True)
class Coordinator:
    """Own monitor-task lifecycle and compose one durable attempt at a time.

    The scheduler owns eventual call ordering, semaphore gates, stop policy,
    retry selection, and accounting. It must await every callback it starts.
    The monitor leaf owns cadence and probe lifecycle. Neither is implemented
    by this wiring increment.
    """

    attempt: AttemptCall
    classifier: OutcomeClassifier
    quota_status: QuotaStatusReader
    runtime: Runtime
    progress: ProgressSink
    schedule_calls: ScheduleCalls = field(default_factory=lambda: _schedule_calls)
    monitor_quota: MonitorQuota = field(default_factory=lambda: _monitor_quota)
    capture_returned_attempt: CaptureReturnedAttempt = field(
        default_factory=lambda: _capture_returned_attempt
    )

    async def run(
        self,
        bound_run: BoundRun,
        evidence: EvidenceStore,
        config: HarnessConfig,
        /,
    ) -> RunRecord:
        """Run the injected scheduling seam and finalize its resulting record.

        A single monitor task is created only for opted-in execution. It is
        cancelled and joined on success, scheduler failure, or cancellation.
        This stage does not establish dispatch, retry, pause/resume, or complete
        accounting semantics.

        Returns:
            The finalized run record.

        Raises:
            ValueError: Dry-run plans must return through the reporting path.
        """
        if config.dry_run:
            raise ValueError("dry-run plans do not enter the coordinator")

        record = await self._dispatch(bound_run, evidence, config)
        await evidence.finalize(record)
        return record

    async def _dispatch(
        self,
        bound_run: BoundRun,
        evidence: EvidenceStore,
        config: HarnessConfig,
        /,
    ) -> RunRecord:
        """Run the scheduler seam and settle the optional monitor task.

        Returns:
            The record assembled by the scheduler after its work settles.
        """
        stop_reason: AttemptResult | BaseException | None = None

        def stop_dispatch(reason: AttemptResult | BaseException, /) -> None:
            nonlocal stop_reason
            if stop_reason is None:
                stop_reason = reason

        def dispatch_stopped() -> bool:
            return stop_reason is not None

        async def execute_attempt(
            call: EffectiveCall,
            attempt_number: AttemptNumber,
            stop: DispatchStop,
            /,
        ) -> AttemptRecord:
            if dispatch_stopped():
                raise RuntimeError("dispatch was stopped before this attempt")
            del stop
            return await self._execute_attempt(
                call, attempt_number, evidence, config, stop_dispatch
            )

        monitor_task = (
            asyncio.create_task(
                _await_monitor(self.monitor_quota(bound_run, stop_dispatch)),
                name=f"quota-monitor-{bound_run.plan.run_id}",
            )
            if config.quota_wait_enabled and not config.dry_run
            else None
        )

        try:
            record = await self.schedule_calls(
                bound_run,
                evidence,
                execute_attempt,
                stop_dispatch,
                dispatch_stopped,
            )
        except BaseException as error:
            stop_dispatch(error)
            if monitor_task is not None:
                try:
                    await _cancel_and_join(monitor_task)
                except BaseException as monitor_error:
                    error.add_note(f"Quota monitor also failed: {monitor_error!r}")
            raise

        if monitor_task is not None:
            await _cancel_and_join(monitor_task)
        return record

    async def _execute_attempt(
        self,
        call: EffectiveCall,
        attempt_number: AttemptNumber,
        evidence: EvidenceStore,
        config: HarnessConfig,
        stop_dispatch: DispatchStop,
        /,
    ) -> AttemptRecord:
        """Order one returned invocation, classification, and evidence writes.

        Returns:
            The durable record for this invocation.
        """
        started_at = self.runtime.utc_now()
        outcome = await self.attempt(call.request, stop_dispatch)
        ended_at = self.runtime.utc_now()
        attempt_evidence = self.capture_returned_attempt(
            call, outcome, started_at, ended_at
        )
        assessment = self.classifier.assess(attempt_evidence)
        attempt_record = await evidence.record_attempt(
            call.run_id,
            call.call_id,
            call.planned_call.position,
            attempt_number,
            attempt_evidence,
            assessment,
        )
        if config.quota_wait_enabled and not config.dry_run:
            observation = await self.quota_status.observe_settled_attempt(
                attempt_evidence
            )
            await evidence.record_quota_telemetry(
                QuotaTelemetryEvent(
                    run_id=call.run_id,
                    call_id=call.call_id,
                    attempt_number=attempt_number,
                    observation=observation,
                )
            )
        return attempt_record


async def _cancel_and_join(task: asyncio.Task[None], /) -> None:
    """Cancel a lifecycle task and wait for its cleanup to settle."""
    if not task.done():
        task.cancel()
    with suppress(asyncio.CancelledError):
        await task


async def _await_monitor(monitor: Awaitable[None], /) -> None:
    """Adapt an injected awaitable monitor to an asyncio task coroutine."""
    await monitor


async def _schedule_calls(
    bound_run: BoundRun,
    evidence: EvidenceStore,
    execute_attempt: Callable[
        [EffectiveCall, AttemptNumber, DispatchStop], Awaitable[AttemptRecord]
    ],
    stop_dispatch: DispatchStop,
    dispatch_stopped: DispatchStopped,
    /,
) -> RunRecord:
    """Schedule calls under concurrency and lifecycle gates.

    Raises:
        NotImplementedError: Scheduling policy has not been implemented.
    """
    del bound_run, evidence, execute_attempt, stop_dispatch, dispatch_stopped
    await asyncio.sleep(0)
    raise NotImplementedError("coordinator scheduling policy is not implemented")


async def _monitor_quota(bound_run: BoundRun, stop_dispatch: DispatchStop, /) -> None:
    """Own one cadence and probe cycle for an opted-in run.

    Raises:
        NotImplementedError: Probe cadence and lifecycle are deferred.
    """
    del bound_run, stop_dispatch
    await asyncio.sleep(0)
    raise NotImplementedError("quota monitor cadence is not implemented")


def _capture_returned_attempt(
    call: EffectiveCall,
    outcome: AttemptResult,
    started_at: str,
    ended_at: str,
    /,
) -> AttemptEvidence:
    """Capture a returned supervisor outcome as typed attempt evidence."""
    del call, outcome, started_at, ended_at
    raise NotImplementedError("supervisor evidence conversion is not implemented")
