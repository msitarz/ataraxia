# SPDX-License-Identifier: Apache-2.0
"""Run ownership, bounded dispatch, quota recovery and finalization."""

import asyncio
from typing import Never

from script.eval.evidence import EvidenceStore
from script.eval.model import QuotaObservation, QuotaWaitContext, RunRecord
from script.eval.runner.ports import (
    AttemptCall,
    BoundRun,
    OutcomeClassifier,
    ProgressFinalStatus,
    ProgressRunPhase,
    ProgressSink,
    QuotaStatusReader,
    Runtime,
)

from .call_states import CallHistory, CallState, EvidencePending, Finished, Queued
from .calls import CallOwner
from .control import RunControl
from .progress import ProgressView, project
from .quota import QuotaOwner, _reset_hint
from .quota_states import Draining, Open, QuotaHistory
from .records import run_record, settings_digest
from .settlement import SettledFailure, SettledValue, Settlement, settle


class Coordinator:
    """Own one prepared provider-bound run and all tasks until settlement.

    Active dispatch and settlement are bounded by configured concurrency.
    A call sleeping in its own durable capacity wait releases that scheduling
    capacity. Such waits retain one task each until they close; their number is
    bounded by the finite plan rather than the concurrency setting.
    """

    def __init__(
        self,
        bound_run: BoundRun,
        evidence: EvidenceStore,
        attempt: AttemptCall,
        classifier: OutcomeClassifier,
        quota_status: QuotaStatusReader,
        runtime: Runtime,
        progress: ProgressSink,
    ) -> None:
        """Bind already prepared evidence and frozen inputs without effects."""
        self._bound_run = bound_run
        self._evidence = evidence
        self._quota_status = quota_status
        self._runtime = runtime
        self._progress = progress
        self._progress_enabled = True
        self._control = RunControl()
        self._changed = asyncio.Event()
        self._observation: QuotaObservation | None = None
        self._slots = asyncio.Semaphore(bound_run.plan.configuration.concurrency)
        self._calls = tuple(
            CallOwner(
                Queued(CallHistory(call, (), ())),
                bound_run.plan.configuration,
                self._control,
                self._slots,
                attempt,
                classifier,
                quota_status,
                evidence,
                runtime,
                _changed=self._changed.set,
                _observed=self._observe,
            )
            for call in bound_run.calls
        )
        self._tasks: dict[asyncio.Task[BaseException | None], CallOwner] = {}
        self._internal: set[asyncio.Task[BaseException | None]] = set()
        self._next = 0
        self._quota: QuotaOwner | None = None
        self._quota_task: asyncio.Task[object] | None = None
        self._quota_history = QuotaHistory((), ())
        self._error: BaseException | None = None
        self._used = False

    async def run(self) -> RunRecord:
        """Dispatch, settle, and finalize the run before returning or raising.

        Returns:
            The durable final accounting.

        Raises:
            RuntimeError: This coordinator was already used.
        """
        if self._used:
            raise RuntimeError("coordinator already ran")
        self._used = True
        digest = settings_digest(self._bound_run.binding.effective_settings)
        try:
            self._publish("running", None)
            await self._schedule()
        except BaseException as error:
            self._capture_error(error, "owner")
        await self._shutdown()
        states = self._states()
        incomplete = self._control.reason is not None or any(
            not isinstance(state, Finished) for state in states
        )
        record = run_record(
            self._bound_run, states, self._quota_history, incomplete, digest
        )
        result = await settle(asyncio.create_task(self._evidence.finalize(record)))
        self._finalization_facts(result)
        if isinstance(result, SettledValue):
            try:
                self._publish(
                    "final",
                    _final_status(
                        record,
                        states,
                        self._control.reason is not None
                        and self._control.reason.cancellation is not None,
                    ),
                )
            except BaseException as error:
                self._capture_error(error, "owner")
        _raise_outcome(self._primary_error(), result)
        return record

    async def _schedule(self) -> None:
        """Own the control watcher until the plan loop stops."""
        self._watcher = self._watch_control()
        primary: BaseException | None = None
        try:
            await self._schedule_loop()
        except BaseException as error:
            primary = error
            raise
        finally:
            cancellation = await _stop_watcher(self._watcher)
            if cancellation is not None and not isinstance(
                primary, asyncio.CancelledError
            ):
                raise cancellation from primary

    async def _schedule_loop(self) -> None:
        """Run a bounded plan loop and respond to stop or quota pause."""
        while True:
            self._changed.clear()
            self._collect_finished()
            if self._control.reason is not None:
                return
            if self._next == len(self._calls) and not self._tasks:
                return
            if self._control.quota_origin is not None:
                await self._handle_pause()
            else:
                self._start_calls()
                self._publish("running", None)
            if self._next == len(self._calls) and not self._tasks:
                return
            await self._changed.wait()

    async def _handle_pause(self) -> None:
        """Report draining or await a drained quota recovery."""
        if not self._drained():
            self._publish("quota_paused", None)
            return
        await self._recover_quota()
        await self._replace_watcher()

    async def _replace_watcher(self) -> None:
        """Join the prior pause watcher before observing another pause."""
        cancellation = await _stop_watcher(self._watcher)
        if cancellation is not None:
            raise cancellation
        self._watcher = self._watch_control()

    def _watch_control(self) -> asyncio.Task[object]:
        """Return a watcher that wakes the scheduler on pause or stop."""
        task = asyncio.create_task(self._control.wait_for_quota_pause())
        task.add_done_callback(self._wake)
        return task

    def _wake[T](self, task: asyncio.Future[T]) -> None:
        """Wake the run loop after an owned task settles."""
        self._changed.set()

    def _start_calls(self) -> None:
        """Start only enough non-sleeping owners to fill configured capacity."""
        active = sum(not owner.waiting_delay for owner in self._tasks.values())
        limit = self._bound_run.plan.configuration.concurrency
        while active < limit and self._next < len(self._calls):
            owner = self._calls[self._next]
            self._next += 1
            task = asyncio.create_task(_run_call(owner))
            self._tasks[task] = owner
            task.add_done_callback(self._wake)
            active += 1

    def _collect_finished(self) -> None:
        """Retrieve completed task outcomes without forwarding sibling errors."""
        for task in tuple(self._tasks):
            if not task.done():
                continue
            owner = self._tasks.pop(task)
            try:
                error = task.result()
            except BaseException as caught:
                error = caught
            if error is not None and task not in self._internal:
                self._capture_error(error, "leaf")
            elif isinstance(error, asyncio.CancelledError):
                reason = self._control.reason
                if (
                    reason is not None
                    and isinstance(reason.first, BaseException)
                    and (
                        error.__cause__ is reason.first
                        or owner.invocation_error is reason.first
                    )
                    and reason.first is not reason.recording_failure
                ):
                    self._capture_error(reason.first, "leaf")
            self._internal.discard(task)

    def _drained(self) -> bool:
        """Return whether no active attempt or required call write remains."""
        return all(
            task.done() or isinstance(owner.state, Queued) or owner.waiting_delay
            for task, owner in self._tasks.items()
        )

    async def _recover_quota(self) -> None:
        """Await recovery only after active attempt evidence has drained."""
        trigger = self._control.quota_trigger
        if trigger is None:
            self._control.latch_stop(RuntimeError("missing durable quota trigger"))
            return
        scope = self._bound_run.binding.quota_scope
        if (
            scope is None
            or scope != self._quota_status.expected_scope
            or trigger.observation.scope != scope
        ):
            self._control.latch_stop(RuntimeError("quota scope does not match binding"))
            return
        context = QuotaWaitContext(
            kind="quota",
            trigger_call_id=trigger.origin.call.call_id,
            trigger_attempt_number=trigger.origin.attempt_number,
            cumulative_waited_before_seconds=sum(
                wait.elapsed_seconds or 0.0 for wait in self._quota_history.waits
            ),
            wait_limit_seconds=self._bound_run.plan.configuration.quota_wait_limit_seconds,
            quota_observation=trigger.observation,
            selected_reset_at_utc=_reset_hint(trigger.observation),
        )
        owner = QuotaOwner(
            Draining(context),
            self._quota_history,
            self._bound_run.plan.configuration,
            self._control,
            self._quota_status,
            self._evidence,
            self._runtime,
            self._bound_run.plan.run_id,
            _changed=self._changed.set,
            _observed=self._observe,
        )
        self._quota = owner
        task = asyncio.create_task(_run_quota(owner))
        self._quota_task = task
        task.add_done_callback(self._wake)
        while not task.done():
            self._changed.clear()
            self._publish("quota_paused", None)
            if not task.done():
                await self._changed.wait()
        self._quota_history = owner.history
        self._quota_task = None
        error = task.result()
        if error is not None:
            raise error
        if not isinstance(owner.state, Open):
            self._control.latch_stop(
                RuntimeError("quota recovery ended without availability")
            )

    def _capture_error(self, error: BaseException, origin: str) -> None:
        """Latch local error facts without borrowing another task's exception."""
        if isinstance(error, asyncio.CancelledError):
            self._control.note_cancellation(
                error, "owner" if origin == "owner" else "leaf"
            )
        else:
            self._control.latch_stop(error)
        if isinstance(error, (KeyboardInterrupt, SystemExit)) and not isinstance(
            self._error, (KeyboardInterrupt, SystemExit, asyncio.CancelledError)
        ):
            if self._error is not None and error.__cause__ is None:
                error.__cause__ = self._error
            self._error = error
        elif self._error is None:
            self._error = error

    async def _shutdown(self) -> None:
        """Cancel siblings and retain every owned task until its effects settle."""
        if self._control.reason is not None:
            self._report_stopping()
            for task, owner in self._tasks.items():
                if not task.done():
                    owner.cancel_for_stop()
                    self._internal.add(task)
                    task.cancel()
        tasks = tuple(self._tasks)
        if self._quota_task is not None:
            tasks += (self._quota_task,)
        if tasks:
            result = await settle(asyncio.create_task(_join(tasks)))
            if result.cancellation is not None:
                self._capture_error(result.cancellation, "owner")
        if self._quota is not None:
            self._quota_history = self._quota.history
        self._collect_finished()
        for owner in self._calls:
            owner.stop_queued()

    def _report_stopping(self) -> None:
        """Report the stop without allowing presentation to abandon cleanup."""
        try:
            self._publish("stopping", None)
        except BaseException as error:
            self._capture_error(error, "owner")

    def _primary_error(self) -> BaseException | None:
        """Return the local reason with any separately retained failure."""
        reason = self._control.reason
        primary = (
            reason.cancellation
            if reason is not None and reason.cancellation is not None
            else self._error
        )
        if primary is None or primary.__cause__ is not None:
            return primary
        failure = None if reason is None else reason.recording_failure
        if failure is None or failure is primary:
            failure = self._error
        if failure is not None and failure is not primary:
            primary.__cause__ = failure
        return primary

    def _finalization_facts(self, result: Settlement[None]) -> None:
        """Retain cancellation and failed final writes before propagation."""
        if result.cancellation is not None:
            self._control.note_cancellation(result.cancellation, "owner")
        if isinstance(result, SettledFailure):
            if isinstance(result.error, asyncio.CancelledError):
                self._control.note_cancellation(result.error, "leaf")
            self._control.note_recording_failure(result.error)

    def _observe(self, observation: QuotaObservation) -> None:
        """Retain the latest durably recorded passive quota observation."""
        self._observation = observation
        self._changed.set()

    def _states(self) -> tuple[CallState, ...]:
        """Return current call facts for projection."""
        return tuple(owner.state for owner in self._calls)

    def _publish(
        self, phase: ProgressRunPhase, final_status: ProgressFinalStatus | None
    ) -> None:
        """Project current facts and isolate expected presentation failures."""
        if not self._progress_enabled:
            return
        quota = self._quota
        snapshot = project(
            ProgressView(
                self._bound_run.plan.run_id,
                phase,
                final_status,
                self._states(),
                Open() if quota is None else quota.state,
                self._quota_history if quota is None else quota.history,
                quota.observation
                if quota is not None and self._quota_task is not None
                else self._observation,
                self._runtime.monotonic(),
                self._runtime.utc_now(),
            )
        )
        try:
            self._progress.publish(snapshot)
        except OSError:
            self._progress_enabled = False


async def _run_call(owner: CallOwner) -> BaseException | None:
    """Capture even interrupts so the run owner can settle siblings first.

    Returns:
        The original failure, or None after successful owner completion.
    """
    try:
        await owner.run()
    except BaseException as error:
        return error
    return None


async def _run_quota(owner: QuotaOwner) -> BaseException | None:
    """Capture recovery failure until the run owner has retained its history.

    Returns:
        The original failure, or None after recovery returns.
    """
    try:
        await owner.recover()
    except BaseException as error:
        return error
    return None


async def _stop_watcher(watcher: asyncio.Task[object]) -> asyncio.CancelledError | None:
    """Cancel and join a local watcher while retaining owner cancellation.

    Returns:
        The first cancellation received while joining, if any.
    """
    watcher.cancel()
    result = await settle(watcher)
    return result.cancellation


async def _join(tasks: tuple[asyncio.Task[object], ...]) -> None:
    """Observe each task without propagating sibling failures."""
    await asyncio.gather(*tasks, return_exceptions=True)


def _raise_outcome(error: BaseException | None, result: Settlement[None]) -> None:
    """Preserve the local primary control flow after the final write settles."""
    failure = result.error if isinstance(result, SettledFailure) else None
    cancellation = result.cancellation
    if isinstance(error, asyncio.CancelledError):
        _raise_with_cause(error, failure)
    if cancellation is not None:
        _raise_with_cause(
            cancellation,
            failure if failure is not None and failure is not cancellation else error,
        )
    if isinstance(failure, asyncio.CancelledError):
        _raise_with_cause(failure, error)
    if error is not None:
        _raise_with_cause(error, failure)
    if failure is not None:
        raise failure


def _raise_with_cause(error: BaseException, cause: BaseException | None) -> Never:
    """Raise the original object without creating a self-referential cause."""
    if cause is not None and cause is not error:
        raise error from cause
    raise error


def _final_status(
    record: RunRecord, states: tuple[CallState, ...], cancelled: bool
) -> ProgressFinalStatus:
    """Return a status distinguished by accounting and durable call outcomes."""
    if any(isinstance(state, EvidencePending) for state in states):
        return "incomplete_evidence"
    if cancelled or any(
        isinstance(state, Finished) and state.outcome == "cancelled" for state in states
    ):
        return "cancelled"
    if record.state == "incomplete":
        return "incomplete_evidence"
    if any(
        not isinstance(state, Finished) or state.outcome != "success"
        for state in states
    ):
        return "failure"
    return "success"
