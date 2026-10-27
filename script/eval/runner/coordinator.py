# SPDX-License-Identifier: Apache-2.0
"""Compose coordinator run, attempt, quota, and evidence effects.

Scheduling gates, result conversion, and quota policy remain explicit pending
leaves until their behavior is implemented and reviewed.
"""

import asyncio
from collections.abc import Awaitable, Callable
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
type ExecuteAttempt = Callable[[EffectiveCall, AttemptNumber], Awaitable[AttemptRecord]]
type DispatchStopped = Callable[[], bool]


@dataclass
class _DispatchGate:
    """Latch the first supervisor or coordinator stop reason."""

    reason: AttemptResult | BaseException | None = None

    def __call__(self, reason: AttemptResult | BaseException, /) -> None:
        """Retain the first reason that forbids later attempt dispatch."""
        if self.reason is None:
            self.reason = reason

    def stopped(self) -> bool:
        """Report whether the run has latched a stop reason.

        Returns:
            Whether dispatch should remain stopped.
        """
        return self.reason is not None


type ScheduleCalls = Callable[
    ["Coordinator", ExecuteAttempt, DispatchStop, DispatchStopped],
    Awaitable[RunRecord],
]
type MonitorQuota = Callable[[Coordinator, DispatchStop], Awaitable[None]]


@dataclass(frozen=True)
class Coordinator:
    """Own run-task lifecycle and compose one durable attempt at a time.

    This instance is bound to one run and one evidence store. Configuration is
    always read from the bound frozen plan. The scheduler owns call ordering,
    semaphore gates, stop policy, retry selection, and accounting; it must
    await every callback it starts. The monitor leaf owns cadence and probe
    lifecycle.
    """

    bound_run: BoundRun
    evidence: EvidenceStore
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

    @property
    def config(self) -> HarnessConfig:
        """Configuration frozen into this coordinator's plan."""
        return self.bound_run.plan.configuration

    async def run(self) -> RunRecord:
        """Run the scheduler seam and finalize the record it returns.

        Returns:
            The finalized run record.

        Raises:
            ValueError: Dry-run plans must return through the reporting path.
        """
        if self.config.dry_run:
            raise ValueError("dry-run plans do not enter the coordinator")
        record = await self._dispatch()
        await self.evidence.finalize(record)
        return record

    async def _dispatch(self) -> RunRecord:
        """Run scheduler and monitor tasks through their owned settlement.

        Returns:
            The record assembled by the scheduler after its work settles.
        """
        gate = _DispatchGate()

        async def execute_attempt(
            call: EffectiveCall, attempt_number: AttemptNumber, /
        ) -> AttemptRecord:
            if gate.stopped():
                raise RuntimeError("dispatch was stopped before this attempt")
            return await self._execute_attempt(call, attempt_number, gate)

        scheduler_task = asyncio.create_task(
            _await_schedule(
                self.schedule_calls(self, execute_attempt, gate, gate.stopped)
            ),
            name=f"evaluation-scheduler-{self.bound_run.plan.run_id}",
        )
        monitor_task = (
            asyncio.create_task(
                _await_monitor(self.monitor_quota(self, gate)),
                name=f"quota-monitor-{self.bound_run.plan.run_id}",
            )
            if self.config.quota_wait_enabled
            else None
        )

        try:
            record = await _settle_scheduler_or_monitor(scheduler_task, monitor_task)
        except BaseException as error:
            gate(error)
            cancellation, failures = await _cancel_and_join(
                scheduler_task, monitor_task
            )
            if cancellation is not None and cancellation is not error:
                cancellation.add_note(f"Run stopped while settling after: {error!r}")
                _add_failure_notes(cancellation, failures)
                raise cancellation from error
            _add_failure_notes(error, failures)
            raise

        if monitor_task is not None:
            cancellation, failures = await _cancel_and_join(
                scheduler_task, monitor_task
            )
            if cancellation is not None:
                _add_failure_notes(cancellation, failures)
                raise cancellation
            if failures:
                raise failures[0]
        return record

    async def _execute_attempt(
        self,
        call: EffectiveCall,
        attempt_number: AttemptNumber,
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
        attempt_record = await self.evidence.record_attempt(
            call.run_id,
            call.call_id,
            call.planned_call.position,
            attempt_number,
            attempt_evidence,
            assessment,
        )
        if self.config.quota_wait_enabled:
            observation = await self.quota_status.observe_settled_attempt(
                attempt_evidence
            )
            await self.evidence.record_quota_telemetry(
                QuotaTelemetryEvent(
                    run_id=call.run_id,
                    call_id=call.call_id,
                    attempt_number=attempt_number,
                    observation=observation,
                )
            )
        return attempt_record


async def _settle_scheduler_or_monitor(
    scheduler: asyncio.Task[RunRecord], monitor: asyncio.Task[None] | None, /
) -> RunRecord:
    """Fail closed if the monitor exits before scheduling has settled.

    Returns:
        The scheduler's run record after both tasks have not reported a failure.
    """
    if monitor is None:
        return await scheduler
    done, _ = await asyncio.wait(
        (scheduler, monitor), return_when=asyncio.FIRST_COMPLETED
    )
    if monitor in done:
        failure = monitor.exception()
        if failure is None:
            failure = RuntimeError("quota monitor exited before scheduling settled")
        if scheduler.done():
            await scheduler
        raise failure
    return await scheduler


async def _cancel_and_join(
    scheduler: asyncio.Task[RunRecord], monitor: asyncio.Task[None] | None, /
) -> tuple[asyncio.CancelledError | None, tuple[BaseException, ...]]:
    """Cancel owned tasks and retain them through repeated owner cancellation.

    Returns:
        Any cancellation delivered to this owner and failures from settled tasks.
    """
    tasks = (scheduler,) if monitor is None else (scheduler, monitor)
    failures: list[BaseException] = []
    for task in tasks:
        if not task.done():
            task.cancel()
    owner_cancellation: asyncio.CancelledError | None = None
    for task in tasks:
        cancellation, failure = await _join_task(task)
        if cancellation is not None:
            owner_cancellation = cancellation
        if failure is not None:
            failures.append(failure)
    return owner_cancellation, tuple(failures)


async def _join_task[Result](
    task: asyncio.Task[Result], /
) -> tuple[asyncio.CancelledError | None, BaseException | None]:
    """Join one shielded task and distinguish owner cancellation from its own.

    Returns:
        Owner cancellation, if received, and the settled task's failure.
    """
    owner_cancellation: asyncio.CancelledError | None = None
    while not task.done():
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError as cancellation:
            current = asyncio.current_task()
            if current is not None and current.cancelling():
                owner_cancellation = cancellation
            elif task.cancelled():
                break
        except BaseException:
            break
    failure = None if task.cancelled() else task.exception()
    return owner_cancellation, failure


def _add_failure_notes(
    owner: BaseException, failures: tuple[BaseException, ...], /
) -> None:
    """Retain secondary owned-task failures without replacing the primary."""
    for failure in failures:
        if failure is not owner:
            owner.add_note(f"Owned coordinator task also failed: {failure!r}")


async def _await_monitor(monitor: Awaitable[None], /) -> None:
    """Adapt an injected awaitable monitor to an asyncio task coroutine."""
    await monitor


async def _await_schedule(scheduler: Awaitable[RunRecord], /) -> RunRecord:
    """Adapt an injected awaitable scheduler to an asyncio task coroutine.

    Returns:
        The scheduler's run record.
    """
    return await scheduler


async def _schedule_calls(
    context: Coordinator,
    execute_attempt: ExecuteAttempt,
    stop_dispatch: DispatchStop,
    dispatch_stopped: DispatchStopped,
    /,
) -> RunRecord:
    """Schedule calls under concurrency and lifecycle gates.

    Raises:
        NotImplementedError: Scheduling policy has not been implemented.
    """
    del context, execute_attempt, stop_dispatch, dispatch_stopped
    await asyncio.sleep(0)
    raise NotImplementedError("coordinator scheduling policy is not implemented")


async def _monitor_quota(context: Coordinator, stop_dispatch: DispatchStop, /) -> None:
    """Own one cadence and probe cycle for an opted-in run.

    Raises:
        NotImplementedError: Probe cadence and lifecycle are deferred.
    """
    del context, stop_dispatch
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
