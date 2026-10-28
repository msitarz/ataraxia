# SPDX-License-Identifier: Apache-2.0
"""Awaited quota recovery through bounded waits and durable probe evidence."""

import asyncio
from asyncio import CancelledError, Task
from dataclasses import replace
from datetime import datetime, timedelta
from typing import Literal
from uuid import uuid4

from script.eval.evidence import EvidenceStore
from script.eval.model import (
    HarnessConfig,
    QuotaObservation,
    QuotaProbeCancelled,
    QuotaProbeDispatched,
    QuotaProbeEvidence,
    QuotaProbeId,
    QuotaProbeLifecycleInput,
    QuotaProbeNotDispatched,
    QuotaProbePrepared,
    QuotaProbeRequest,
    QuotaProbeSchedule,
    QuotaProbeScheduled,
    RunId,
    WaitEnd,
    WaitEvent,
    WaitRecord,
)
from script.eval.runner.policy import (
    quota_poll_delay,
    quota_probe_allowed,
    quota_wait_remaining,
)
from script.eval.runner.ports import QuotaStatusReader, Runtime
from script.eval.runner.quota_evidence import quota_probe_evidence

from .control import RunControl
from .quota_states import (
    Draining,
    Open,
    PreparingProbe,
    ProbeEvidencePending,
    ProbeNotDispatched,
    ProbePrepared,
    Probing,
    QuotaEvidencePending,
    QuotaHistory,
    QuotaState,
    QuotaWriteFailure,
    RecordingProbe,
    Waiting,
)
from .settlement import SettledFailure, Settlement, settle
from .state import WaitWrite

type RaceOutcome = Literal["completed", "stop", "bound", "cancelled"]


class QuotaOwner:
    """Own one drained pause and its durable wait and probe history."""

    def __init__(
        self,
        initial: Draining,
        history: QuotaHistory,
        config: HarnessConfig,
        control: RunControl,
        reader: QuotaStatusReader,
        evidence: EvidenceStore,
        runtime: Runtime,
        run_id: RunId,
    ) -> None:
        """Bind the shared gate and effect boundaries for this pause."""
        self._state: QuotaState = initial
        self._history = history
        self._observation = initial.context.quota_observation
        self._config = config
        self._control = control
        self._reader = reader
        self._evidence = evidence
        self._runtime = runtime
        self._run_id = run_id
        self._local_cancellation: CancelledError | None = None
        self._pending: QuotaEvidencePending | None = None
        self._probe_pending: ProbeEvidencePending | None = None
        self._recording_failure: BaseException | None = None
        self._probe_interrupted = False
        self._probe_active = False

    @property
    def state(self) -> QuotaState:
        """The current authoritative quota state."""
        return self._state

    @property
    def history(self) -> QuotaHistory:
        """Only durably closed waits and probes."""
        return self._history

    @property
    def observation(self) -> QuotaObservation | None:
        """The latest observation retained for this pause."""
        match self._state:
            case Draining(context):
                return context.quota_observation
            case Waiting() as waiting:
                return waiting.observation
            case QuotaEvidencePending(waiting=waiting):
                return waiting.observation
            case _:
                return self._observation

    async def recover(self) -> QuotaState:
        """Recover after the caller closes the quota gate, drains and persists attempts.

        The owner awaits one probe at a time and retains required writes.

        Returns:
            The stopped or evidence-pending state.

        Cancellation propagates only after required writes settle.

        Raises:
            RuntimeError: Recovery was already invoked.
        """
        if not isinstance(self._state, Draining):
            raise RuntimeError("quota recovery already started")
        return await self._start_wait(self._state)

    def _remaining(self, elapsed: float) -> float | None:
        """Apply the cumulative configured bound to elapsed pause time.

        Returns:
            The remaining seconds, or None for an unbounded wait.
        """
        return quota_wait_remaining(self._config, elapsed)

    def _event(
        self,
        waiting: Waiting,
        kind: Literal["started", "finished"],
        end: WaitEnd | None,
    ) -> WaitEvent:
        """Capture an event with the retained wait identity and fresh clocks.

        Returns:
            The event to persist.
        """
        return WaitEvent(
            run_id=self._run_id,
            wait_id=waiting.wait_id,
            context=waiting.context,
            kind=kind,
            observed_at_utc=self._runtime.utc_now(),
            elapsed_seconds=max(
                0.0, self._runtime.monotonic() - waiting.started_monotonic
            ),
            quota_observation=waiting.observation,
            end=end,
            diagnostic=None,
        )

    async def _start_wait(self, initial: Draining) -> QuotaState:
        """Retain a start write and close every successfully started wait.

        Returns:
            The stopped or evidence-pending state.
        """
        waiting = Waiting(
            initial.context,
            str(uuid4()),
            self._runtime.utc_now(),
            self._runtime.monotonic(),
            "submitted",
            None,
            initial.context.quota_observation,
        )
        self._state = waiting
        event = self._event(waiting, "started", None)
        settled = await settle(
            asyncio.create_task(self._evidence.record_wait_event(event))
        )
        cancellation = self._cancellation(settled.cancellation, settled)
        if isinstance(settled, SettledFailure):
            self._control.note_recording_failure(settled.error)
            self._state = QuotaEvidencePending(
                waiting,
                (QuotaWriteFailure(WaitWrite(event, None), settled.error),),
                None,
            )
            if cancellation is settled.error:
                raise cancellation
            if cancellation is not None:
                raise cancellation from settled.error
            return self._state
        reason = self._control.reason
        end = self._end_for_control(cancellation)
        closure = None if end is None else self._closure(waiting, end)
        waiting = initial.started(waiting, cancellation, reason, closure)
        self._state = waiting
        if closure is not None:
            return await self._close_wait(waiting, closure, cancellation)
        return await self._recover_wait(waiting)

    def _closure(self, waiting: Waiting, end: WaitEnd) -> WaitRecord:
        """Build the exact summary owed by a durable start.

        Returns:
            The pending closure.
        """
        return WaitRecord(
            wait_id=waiting.wait_id,
            context=waiting.context,
            started_at_utc=waiting.started_at_utc,
            ended_at_utc=self._runtime.utc_now(),
            elapsed_seconds=max(
                0.0, self._runtime.monotonic() - waiting.started_monotonic
            ),
            end=end,
            diagnostic=None,
        )

    async def _close_wait(
        self, waiting: Waiting, closure: WaitRecord, cancellation: CancelledError | None
    ) -> QuotaState:
        """Settle closure before retaining history or propagating cancellation.

        Returns:
            The stopped or evidence-pending state.
        """
        self._retain_waiting(waiting)
        event = self._event(waiting, "finished", closure.end)
        settled = await settle(
            asyncio.create_task(self._evidence.record_wait_event(event))
        )
        later = self._cancellation(settled.cancellation, settled)
        cancellation = cancellation or later
        if isinstance(settled, SettledFailure):
            self._note_recording_failure(settled.error)
            if self._pending is None:
                self._pending = replace(
                    waiting.journal_failed(WaitWrite(event, closure), settled.error),
                    probe=self._probe_pending,
                )
            else:
                self._pending = replace(self._pending, waiting=waiting).journal_failed(
                    WaitWrite(event, closure), settled.error
                )
            self._state = self._pending
            if cancellation is settled.error:
                raise cancellation
            if cancellation is not None:
                raise cancellation from settled.error
            return self._state
        return self._completed_wait(waiting, closure, cancellation)

    def _retain_waiting(self, waiting: Waiting) -> None:
        """Expose the current wait without losing outstanding failures."""
        if self._pending is not None:
            self._pending = replace(self._pending, waiting=waiting)
            self._state = self._pending
        elif self._probe_pending is not None:
            self._probe_pending = replace(self._probe_pending, waiting=waiting)
            self._state = self._probe_pending
        else:
            self._state = waiting

    def _completed_wait(
        self, waiting: Waiting, closure: WaitRecord, cancellation: CancelledError | None
    ) -> QuotaState:
        """Advance a durable closure and only then permit dispatch.

        Returns:
            The resulting state after the durable closure.
        """
        if closure.end == "quota_available" and (
            self._reader.expected_scope is None
            or waiting.observation.scope != self._reader.expected_scope
        ):
            self._control.latch_stop(RuntimeError("quota scope changed"))
        elapsed = waiting.context.cumulative_waited_before_seconds + max(
            0.0, self._runtime.monotonic() - waiting.started_monotonic
        )
        self._history, self._state = waiting.completed(
            self._history,
            closure,
            self._control.reason,
            self._remaining(elapsed),
            self._runtime.utc_now(),
        )
        if self._pending is not None:
            self._pending = replace(self._pending, waiting=waiting)
            self._state = self._pending
        elif self._probe_pending is not None:
            self._probe_pending = replace(self._probe_pending, waiting=waiting)
            self._state = self._probe_pending
        elif isinstance(self._state, Open):
            self._control.resume_after_quota()
        if cancellation is not None:
            if (
                self._recording_failure is not None
                and self._recording_failure is not cancellation
            ):
                raise cancellation from self._recording_failure
            raise cancellation
        return self._state

    def _cancellation[T](
        self, cancellation: CancelledError | None, settled: Settlement[T]
    ) -> CancelledError | None:
        """Retain this operation's first local cancellation, never another owner's.

        Returns:
            The first local cancellation, if any.
        """
        if cancellation is not None:
            self._control.note_cancellation(cancellation, "owner")
            if self._local_cancellation is None:
                self._local_cancellation = cancellation
        if isinstance(settled, SettledFailure) and isinstance(
            settled.error, CancelledError
        ):
            self._control.note_cancellation(settled.error, "leaf")
            if self._local_cancellation is None:
                self._local_cancellation = settled.error
            return self._local_cancellation
        return self._local_cancellation

    def _end_for_control(self, cancellation: CancelledError | None) -> WaitEnd | None:
        """Select a stop outcome without propagating another owner's cancellation.

        Returns:
            A required closure end, or None when recovery may continue.
        """
        reason = self._control.reason
        if cancellation is not None or (reason is not None and reason.cancellation):
            return "cancelled"
        return "stop" if reason is not None else None

    def _remaining_wait(self, waiting: Waiting) -> float | None:
        """Sample the bound including all elapsed wait and evidence time.

        Returns:
            Remaining seconds, or None without a configured bound.
        """
        return self._remaining(
            waiting.context.cumulative_waited_before_seconds
            + max(0.0, self._runtime.monotonic() - waiting.started_monotonic)
        )

    async def _finish_wait(self, waiting: Waiting, end: WaitEnd) -> QuotaState:
        """Retain and write the final summary before returning or cancelling.

        Returns:
            The resulting quota state.
        """
        closure = self._closure(waiting, end)
        waiting = replace(waiting, end_record=closure)
        return await self._close_wait(waiting, closure, self._local_cancellation)

    async def _journal(
        self,
        state: Waiting
        | PreparingProbe
        | Probing
        | RecordingProbe
        | ProbeEvidencePending,
        event: QuotaProbeLifecycleInput,
    ) -> bool:
        """Retain one exact submitted probe event and latch any write failure.

        Returns:
            Whether the journal write completed successfully.
        """
        settled = await settle(
            asyncio.create_task(self._evidence.record_quota_probe_event(event))
        )
        self._cancellation(settled.cancellation, settled)
        if isinstance(settled, SettledFailure):
            self._note_recording_failure(settled.error)
            if self._pending is None:
                self._pending = state.journal_failed(event, settled.error)
            else:
                self._pending = self._pending.journal_failed(event, settled.error)
            self._state = self._pending
            return False
        return True

    def _note_recording_failure(self, error: BaseException) -> None:
        """Stop on a failed write and retain its first error for cancellation.

        The retained error remains available for cancellation chaining.
        """
        self._control.note_recording_failure(error)
        if self._recording_failure is None:
            self._recording_failure = error

    async def _recover_wait(self, waiting: Waiting) -> QuotaState:
        """Schedule and await probes until a durable closure is selected.

        Returns:
            The resulting terminal or evidence-pending state.
        """
        while True:
            end: WaitEnd | None = self._end_for_control(self._local_cancellation)
            remaining = self._remaining_wait(waiting)
            if end is None and (
                remaining == 0
                or not quota_probe_allowed(self._config, len(self._history.probes))
            ):
                end = "bound"
            if end is None and not waiting.probe_eligible(
                self._reader.expected_scope, self._runtime.utc_now()
            ):
                self._control.latch_stop(RuntimeError("invalid quota trigger"))
                end = "unknown"
            if end is not None:
                return await self._finish_wait(waiting, end)
            waiting = await self._one_probe(waiting)
            if waiting.end_record is not None:
                return await self._close_wait(
                    waiting, waiting.end_record, self._local_cancellation
                )

    async def _one_probe(self, waiting: Waiting) -> Waiting:
        """Persist cadence and preparation, then invoke at most one probe.

        Returns:
            The next wait, possibly with a required closure.
        """
        delay, schedule = self._schedule(waiting)
        if not await self._journal(
            waiting, QuotaProbeScheduled(kind="scheduled", schedule=schedule)
        ):
            return self._ending(waiting, "stop")
        started, interrupted = await self._scheduled_delay(waiting, schedule, delay)
        if interrupted is not None:
            return interrupted
        preparation = ProbePrepared(schedule, waiting.wait_id)
        state = PreparingProbe(waiting, preparation)
        self._state = state
        event = QuotaProbePrepared(
            kind="prepared", schedule=schedule, pause_wait_id=waiting.wait_id
        )
        if not await self._journal(state, event):
            return self._ending(waiting, "stop")
        gate = state.dispatch_gate(
            self._config,
            len(self._history.probes),
            self._remaining_wait(waiting),
            self._control.reason,
            self._local_cancellation,
            self._reader.expected_scope,
            self._runtime.utc_now(),
            max(0.0, self._runtime.monotonic() - started),
        )
        if isinstance(gate, ProbeNotDispatched):
            if gate.cause == "unknown":
                self._control.latch_stop(RuntimeError("invalid quota trigger"))
            await self._journal(
                state,
                QuotaProbeNotDispatched(
                    kind="not_dispatched",
                    schedule=schedule,
                    pause_wait_id=waiting.wait_id,
                    cause=gate.cause,
                    ended_at_utc=gate.ended_at_utc,
                    elapsed_seconds=gate.elapsed_seconds,
                ),
            )
            return self._ending(waiting, gate.cause)
        return await self._poll(state, started)

    async def _scheduled_delay(
        self, waiting: Waiting, schedule: QuotaProbeSchedule, delay: float
    ) -> tuple[float, Waiting | None]:
        """Await scheduled cadence and journal any pre-preparation stop.

        Returns:
            The monotonic start and a closure when the delay was interrupted.
        """
        started = self._runtime.monotonic()
        outcome: RaceOutcome
        outcome, slept = await self._race(
            asyncio.create_task(self._runtime.sleep(delay)),
            self._remaining_wait(waiting),
        )
        if outcome == "completed" and isinstance(slept, SettledFailure):
            if isinstance(slept.error, CancelledError):
                if self._local_cancellation is None:
                    self._local_cancellation = slept.error
                self._control.note_cancellation(slept.error, "leaf")
            else:
                self._control.latch_stop(slept.error)
            outcome = "stop"
        if outcome != "completed":
            cause: Literal["cancelled", "bound", "stop"] = (
                "cancelled"
                if self._local_cancellation is not None
                else ("bound" if outcome == "bound" else "stop")
            )
            event = QuotaProbeCancelled(
                kind="cancelled",
                schedule=schedule,
                cause=cause,
                ended_at_utc=self._runtime.utc_now(),
                elapsed_seconds=max(0.0, self._runtime.monotonic() - started),
                elapsed_basis="monotonic",
            )
            await self._journal(waiting, event)
            return started, self._ending(waiting, cause)
        return started, None

    def _schedule(self, waiting: Waiting) -> tuple[float, QuotaProbeSchedule]:
        """Choose the next periodic or future reset-hint check.

        Returns:
            Its positive delay and durable schedule.
        """
        now = self._runtime.utc_now()
        reset_hint = _reset_hint(waiting.observation)
        delay = quota_poll_delay(
            self._config.quota_poll_interval_seconds,
            now,
            reset_hint,
        )
        due = (
            datetime.fromisoformat(now.replace("Z", "+00:00"))
            + timedelta(seconds=delay)
        ).isoformat()
        scope = waiting.observation.scope
        assert scope is not None
        return delay, QuotaProbeSchedule(
            run_id=self._run_id,
            probe_id=QuotaProbeId(str(uuid4())),
            scope=scope,
            reason="reset_hint"
            if delay < self._config.quota_poll_interval_seconds
            else "periodic",
            created_at_utc=now,
            due_at_utc=due,
            interval_seconds=self._config.quota_poll_interval_seconds,
            reset_hint_at_utc=reset_hint,
        )

    def _ending(self, waiting: Waiting, end: WaitEnd) -> Waiting:
        """Retain a required closure while leaving its write to the caller.

        Returns:
            The waiting state with its pending closure.
        """
        reason = self._control.reason
        if self._local_cancellation is not None or (
            reason is not None and reason.cancellation is not None
        ):
            end = "cancelled"
        return replace(waiting, end_record=self._closure(waiting, end))

    async def _race[T](
        self, task: Task[T], remaining: float | None, *, probe: bool = False
    ) -> tuple[RaceOutcome, Settlement[T]]:
        """Race an owned operation against stop and the cumulative bound.

        Returns:
            The winning reason and the settled operation, including cleanup.
        """
        stop = asyncio.create_task(self._control.wait_stopped())
        timer = (
            None
            if remaining is None
            else asyncio.create_task(self._runtime.sleep(remaining))
        )
        watchers = {task, stop} if timer is None else {task, stop, timer}
        outcome: RaceOutcome = "completed"
        try:
            await asyncio.wait(watchers, return_when=asyncio.FIRST_COMPLETED)
        except CancelledError as error:
            if self._local_cancellation is None:
                self._local_cancellation = error
            self._control.note_cancellation(error, "owner")
            outcome = "cancelled"
        if outcome == "completed":
            outcome = self._race_outcome(timer)
        if _should_cancel_owned(outcome, task.done(), probe, self._probe_active):
            self._probe_interrupted = probe
            task.cancel()
        settled = await settle(task)
        if settled.cancellation is not None:
            if self._local_cancellation is None:
                self._local_cancellation = settled.cancellation
            self._control.note_cancellation(settled.cancellation, "owner")
        await self._dispose_watchers(stop, timer)
        return outcome, settled

    def _race_outcome(self, timer: Task[None] | None) -> RaceOutcome:
        """Select stop or bound before accepting a completed operation.

        Returns:
            The selected reason for leaving the race.
        """
        if self._control.reason is not None:
            return "stop"
        if timer is not None and timer.done():
            try:
                timer.result()
            except CancelledError as error:
                if self._local_cancellation is None:
                    self._local_cancellation = error
                self._control.note_cancellation(error, "leaf")
                return "cancelled"
            except BaseException as error:
                self._control.latch_stop(error)
                return "stop"
            return "bound"
        return "completed"

    async def _dispose_watchers(
        self, stop: Task[None], timer: Task[None] | None
    ) -> None:
        """Cancel and settle the local stop and deadline watchers."""
        stop.cancel()
        if timer is not None:
            timer.cancel()
        settled = await settle(asyncio.create_task(_join_watchers(stop, timer)))
        self._cancellation(settled.cancellation, settled)

    async def _poll(self, state: PreparingProbe, started: float) -> Waiting:
        """Invoke a single poll and persist its exact evidence before deciding.

        Returns:
            Updated wait or a wait with a required closure.
        """
        self._probe_interrupted = False
        outcome: RaceOutcome
        outcome, settled = await self._race(
            asyncio.create_task(self._invoke_probe(state, started)),
            self._remaining_wait(state.waiting),
            probe=True,
        )
        if isinstance(settled, SettledFailure):
            self._control.latch_stop(settled.error)
            return self._ending(state.waiting, "unknown")
        captured = settled.value
        if isinstance(captured, ProbeNotDispatched):
            event = QuotaProbeNotDispatched(
                kind="not_dispatched",
                schedule=captured.prepared.schedule,
                pause_wait_id=captured.prepared.pause_wait_id,
                cause=captured.cause,
                ended_at_utc=captured.ended_at_utc,
                elapsed_seconds=captured.elapsed_seconds,
            )
            await self._journal(state, event)
            if captured.cause == "unknown":
                self._control.latch_stop(RuntimeError("invalid quota trigger"))
            return self._ending(state.waiting, captured.cause)
        probing, evidence, error = captured
        probe = probing.capture(evidence, error)
        if self._pending is not None:
            self._pending = replace(self._pending, probe=probe)
        self._state = self._pending or probe
        if isinstance(probe, ProbeEvidencePending):
            self._probe_pending = probe
            self._control.latch_stop(probe.error)
            return self._ending(state.waiting, "unknown")
        return await self._record_probe(probe, outcome)

    async def _record_probe(
        self, probe: RecordingProbe, outcome: RaceOutcome
    ) -> Waiting:
        """Persist captured process evidence and select the next wait state.

        Returns:
            The updated wait, possibly with a pending closure.
        """
        written = await settle(
            asyncio.create_task(
                self._evidence.record_quota_probe_settled(probe.evidence)
            )
        )
        self._cancellation(written.cancellation, written)
        if isinstance(written, SettledFailure):
            self._note_recording_failure(written.error)
            failed = probe.write_failed(written.error)
            self._probe_pending = failed
            if self._pending is None:
                self._state = failed
            else:
                self._pending = replace(self._pending, probe=failed)
                self._state = self._pending
            return self._ending(probe.waiting, "stop")
        self._history, waiting = probe.persisted(
            self._history,
            written.value.record,
            self._control.reason,
            self._remaining_wait(probe.waiting),
            self._runtime.utc_now(),
            self._runtime.monotonic(),
        )
        self._observation = waiting.observation
        if waiting.end_record is not None and waiting.end_record.end == "unknown":
            self._control.latch_stop(
                RuntimeError("probe did not establish quota state")
            )
        if self._pending is not None:
            self._pending = replace(self._pending, waiting=waiting, probe=None)
            self._state = self._pending
        else:
            self._state = waiting
        if waiting.end_record is None and outcome != "completed":
            end: WaitEnd = "bound" if outcome == "bound" else "stop"
            return self._ending(waiting, end)
        return waiting

    async def _invoke_probe(
        self, state: PreparingProbe, started: float
    ) -> (
        ProbeNotDispatched
        | tuple[Probing, QuotaProbeEvidence | None, BaseException | None]
    ):
        """Recheck immediately before invoking and settle its dispatch journal.

        Returns:
            A non-dispatch closure or exact-request probe outcome.
        """
        request = self._probe_request(state, started)
        if isinstance(request, ProbeNotDispatched):
            return request
        probing = state.dispatched(request)
        self._state = probing
        event = QuotaProbeDispatched(kind="dispatched", request=request)
        journal = asyncio.create_task(self._journal(probing, event))
        evidence: QuotaProbeEvidence | None = None
        error: BaseException | None = None
        self._probe_active = True
        try:
            evidence = await self._reader.poll(request, self._control.supervisor_stop)
        except BaseException as caught:
            error = caught
            evidence = _exception_probe_evidence(caught, request)
            self._note_probe_error(caught)
        self._probe_active = False
        journal_result = await settle(journal)
        if journal_result.cancellation is not None:
            if self._local_cancellation is None:
                self._local_cancellation = journal_result.cancellation
            self._control.note_cancellation(journal_result.cancellation, "owner")
        return probing, evidence, error

    def _note_probe_error(self, error: BaseException) -> None:
        """Distinguish leaf cancellation from stop-induced probe cancellation."""
        if isinstance(error, CancelledError):
            if not self._probe_interrupted:
                if self._local_cancellation is None:
                    self._local_cancellation = error
                self._control.note_cancellation(error, "leaf")
        elif not (self._probe_interrupted and isinstance(error, TimeoutError)):
            self._control.latch_stop(error)

    def _probe_request(
        self, state: PreparingProbe, started: float
    ) -> ProbeNotDispatched | QuotaProbeRequest:
        """Sample the final gate and create a request only when permitted.

        Returns:
            The exact request or a truthful pre-dispatch closure.
        """
        expected_scope = self._reader.expected_scope
        now_utc = self._runtime.utc_now()
        now_monotonic = self._runtime.monotonic()
        elapsed = max(0.0, now_monotonic - started)
        cumulative = state.waiting.context.cumulative_waited_before_seconds + max(
            0.0, now_monotonic - state.waiting.started_monotonic
        )
        gate = state.dispatch_gate(
            self._config,
            len(self._history.probes),
            self._remaining(cumulative),
            self._control.reason,
            self._local_cancellation,
            expected_scope,
            now_utc,
            elapsed,
        )
        if isinstance(gate, ProbeNotDispatched):
            return gate
        return QuotaProbeRequest(
            schedule=state.preparation.schedule,
            pause_wait_id=state.waiting.wait_id,
            poll_started_at_utc=now_utc,
            scheduled_wait_seconds=elapsed,
            scheduled_wait_elapsed_basis="monotonic",
        )


def _should_cancel_owned(
    outcome: RaceOutcome, done: bool, probe: bool, probe_active: bool, /
) -> bool:
    """Cancel interrupted work only while its cancellable operation is active.

    An inactive probe task must settle its dispatch journal or pre-dispatch
    gate; cancelling it there could abandon required lifecycle evidence.

    Returns:
        Whether the race should cancel the owned task.
    """
    return outcome != "completed" and not done and (not probe or probe_active)


def _reset_hint(observation: QuotaObservation) -> str | None:
    """Select the latest reset among the adapter's exhausted windows.

    Returns:
        The latest normalized hint, or None when none is available.
    """
    hints = [
        window.reset_at_utc
        for window in observation.windows
        if window.state == "exhausted" and window.reset_at_utc is not None
    ]
    if not hints:
        return None
    return max(
        hints, key=lambda value: datetime.fromisoformat(value.replace("Z", "+00:00"))
    )


def _exception_probe_evidence(
    error: BaseException, request: QuotaProbeRequest
) -> QuotaProbeEvidence | None:
    """Find evidence for the exact request across an exception cause chain.

    Returns:
        Attached evidence, or None when no exact-request evidence is available.
    """
    seen: set[int] = set()
    pending = [error]
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        evidence = quota_probe_evidence(current, request)
        if evidence is not None:
            return evidence
        if current.__context__ is not None:
            pending.append(current.__context__)
        if current.__cause__ is not None:
            pending.append(current.__cause__)
    return None


async def _join_watchers(stop: Task[None], timer: Task[None] | None) -> None:
    """Join cancelled local watcher tasks without leaving background work."""
    await asyncio.gather(
        stop, *(() if timer is None else (timer,)), return_exceptions=True
    )
