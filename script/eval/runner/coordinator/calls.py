# SPDX-License-Identifier: Apache-2.0
"""One call's dispatch, durable settlement, and retry lifecycle."""

import asyncio
from asyncio import CancelledError, Semaphore
from dataclasses import replace
from typing import Literal
from uuid import uuid4

from script.eval.evidence import EvidenceStore
from script.eval.model import (
    AttemptEvidence,
    AttemptRecord,
    CapacityWaitContext,
    HarnessConfig,
    QuotaTelemetryEvent,
    WaitEnd,
    WaitEvent,
    WaitRecord,
)
from script.eval.runner.policy import capacity_jitter_bound
from script.eval.runner.ports import (
    AttemptCall,
    OutcomeClassifier,
    QuotaStatusReader,
    Runtime,
)
from script.process_supervisor import (
    AttemptCancelled,
    AttemptFailureEvidence,
    AttemptRequest,
    AttemptResult,
    Completed,
    InfrastructureFailure,
    OutputLimitExceeded,
    TimedOut,
    failure_evidence,
)

from .call_states import (
    Attempting,
    CallHistory,
    CallState,
    CallWait,
    EvidencePending,
    Finished,
    ObservingQuota,
    Queued,
    Recording,
    RecordingTelemetry,
    RetryWait,
    Stopped,
)
from .control import RunControl
from .quota_states import PauseOrigin, PauseTrigger
from .settlement import SettledFailure, SettledValue, Settlement, settle
from .state import WaitWrite


class CallOwner:
    """Own the state and effects of one planned call."""

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
    ) -> None:
        """Bind the run's shared controls and call-specific dependencies."""
        self._state: CallState = initial
        self._config = config
        self._control = control
        self._slots = slots
        self._attempt = attempt
        self._classifier = classifier
        self._quota_status = quota_status
        self._evidence = evidence
        self._runtime = runtime
        self._invocation_error: BaseException | None = None

    @property
    def state(self) -> CallState:
        """The current authoritative call state."""
        return self._state

    async def run(self) -> CallState:
        """Dispatch and settle this call until terminal or evidence is pending.

        Returns:
            The current terminal or evidence-pending state.

        Raises:
            CancelledError: The owner or an invocation was cancelled.
        """
        try:
            return await self._run()
        except CancelledError as cancellation:
            self._control.note_cancellation(cancellation, "owner")
            if isinstance(self._state, (Queued, ObservingQuota)):
                history = self._state.history
                self._state = Stopped(
                    history, "cancelled" if history.attempts else "not_started"
                )
            raise
        except BaseException as error:
            self._control.latch_stop(error)
            if isinstance(self._state, ObservingQuota):
                self._state = Stopped(self._state.history, "failure")
            raise

    async def _run(self) -> CallState:
        """Advance the typed state until a terminal state or evidence is pending.

        Returns:
            The current terminal or evidence-pending state.

        Raises:
            RuntimeError: The owner is already running an attempt.
        """
        while True:
            match self._state:
                case Queued() as queued:
                    if queued.history.attempts:
                        await self._runtime.sleep(0)
                    await self._dispatch(queued)
                case Recording() as recording:
                    await self._record(recording)
                case ObservingQuota() as observing:
                    await self._observe(observing)
                case RecordingTelemetry() as telemetry:
                    await self._record_telemetry(telemetry)
                case Finished() | EvidencePending() | Stopped():
                    return self._state
                case RetryWait() as wait:
                    await self._wait(wait)
                case Attempting():
                    raise RuntimeError("attempt is already in flight")

    async def _dispatch(self, state: Queued) -> None:
        """Hold a slot through the supervisor call, rechecking the gate."""
        while await self._control.wait_dispatchable():
            async with self._slots:
                if not self._control.dispatch_allowed():
                    continue
                number = len(state.history.attempts) + 1
                self._state = Attempting(state.history, number)
                request = state.history.call.request
                started = self._runtime.utc_now()
                evidence = await self._invoke(request, started)
            assessment = self._classifier.assess(evidence)
            if self._config.quota_wait_enabled and assessment.retry_class == "quota":
                self._control.pause_for_quota(PauseOrigin(state.history.call, number))
            assert isinstance(self._state, Attempting)
            self._state = self._state.capture(evidence, assessment)
            return
        self._state = Stopped(
            state.history, "not_started" if not state.history.attempts else "failure"
        )

    async def _invoke(self, request: AttemptRequest, started: str) -> AttemptEvidence:
        """Capture returned or exceptional supervisor facts for durable writing.

        Returns:
            Evidence associated with the exact submitted request.
        """
        try:
            result = await self._attempt(request, self._control.supervisor_stop)
        except BaseException as error:
            self._invocation_error = error
            if isinstance(error, CancelledError):
                self._note_active_cancellation(error)
            else:
                self._control.latch_stop(error)
            outcome = _exception_outcome(error)
            observation = None if outcome is None else outcome.observation
            return AttemptEvidence(
                "cancelled" if isinstance(error, CancelledError) else "raised",
                outcome,
                type(error).__name__,
                _diagnostic(error),
                request,
                started,
                _end_time(self._runtime),
                None
                if observation is None or observation.output is None
                else observation.output.stdout,
            )
        output = result.observation.output
        return AttemptEvidence(
            "returned",
            result,
            None,
            None,
            request,
            started,
            self._runtime.utc_now(),
            None if output is None else output.stdout,
        )

    def _note_active_cancellation(self, error: CancelledError) -> None:
        """Retain whether this task was cancelled or a leaf raised cancellation."""
        task = asyncio.current_task()
        assert task is not None
        self._control.note_cancellation(error, "owner" if task.cancelling() else "leaf")

    async def _record(self, state: Recording) -> None:
        """Retain the attempt write before selecting its next state."""
        call = state.history.call
        task = asyncio.create_task(
            self._evidence.record_attempt(
                call.run_id,
                call.call_id,
                call.planned_call.position,
                state.attempt.number,
                state.attempt.evidence,
                state.attempt.assessment,
            )
        )
        settled = await settle(task)
        if settled.cancellation is not None:
            self._control.note_cancellation(settled.cancellation, "owner")
        match settled:
            case SettledFailure(error, _):
                if isinstance(error, CancelledError):
                    self._control.note_cancellation(error, "leaf")
                self._control.note_recording_failure(error)
                self._state = state.write_failed(error)
            case SettledValue(record, _):
                wait = (
                    None
                    if self._config.quota_wait_enabled
                    else self._prepare_wait(state.history, record)
                )
                self._state = state.persisted(
                    record, self._config, self._control.reason, wait
                )
        self._finish_attempt_settlement(settled)

    def _finish_attempt_settlement(self, settled: Settlement[AttemptRecord]) -> None:
        """Propagate invocation and write cancellation after state is updated."""
        cancellation = settled.cancellation
        if cancellation is not None:
            if isinstance(settled, SettledFailure):
                raise cancellation from settled.error
            if self._invocation_error is not None:
                raise cancellation from self._invocation_error
            raise cancellation
        if self._invocation_error is not None:
            error = self._invocation_error
            self._invocation_error = None
            if isinstance(settled, SettledFailure):
                raise error from settled.error
            raise error
        if isinstance(settled, SettledFailure) and isinstance(
            settled.error, CancelledError
        ):
            raise settled.error

    async def _observe(self, state: ObservingQuota) -> None:
        """Read passive quota only after the attempt is durable."""
        observation = await self._quota_status.observe_settled_attempt(state.evidence)
        call = state.history.call
        self._state = state.capture(
            QuotaTelemetryEvent(
                run_id=call.run_id,
                call_id=call.call_id,
                attempt_number=state.attempt_number,
                observation=observation,
            )
        )

    async def _record_telemetry(self, state: RecordingTelemetry) -> None:
        """Persist telemetry before publishing a matching exhaustion trigger."""
        settled = await settle(
            asyncio.create_task(self._evidence.record_quota_telemetry(state.event))
        )
        if settled.cancellation is not None:
            self._control.note_cancellation(settled.cancellation, "owner")
        match settled:
            case SettledFailure(error, cancellation):
                if isinstance(error, CancelledError):
                    self._control.note_cancellation(error, "leaf")
                self._control.note_recording_failure(error)
                self._state = state.write_failed(error)
            case SettledValue(_, cancellation):
                origin = self._control.quota_origin
                observation = state.event.observation
                if observation.scope is not None and self._control.reason is None:
                    self._publish_trigger(state, origin)
                wait = self._prepare_wait(
                    state.history, state.history.attempts[-1], includes_record=True
                )
                self._state = state.persisted(self._config, self._control.reason, wait)
        if cancellation is not None:
            if isinstance(settled, SettledFailure):
                raise cancellation from settled.error
            raise cancellation
        if isinstance(settled, SettledFailure) and isinstance(
            settled.error, CancelledError
        ):
            raise settled.error

    def _publish_trigger(
        self, state: RecordingTelemetry, origin: PauseOrigin | None
    ) -> None:
        """Publish only the durable observation associated with the pause."""
        observation = state.event.observation
        if (
            origin is not None
            and origin.call == state.history.call
            and origin.attempt_number == state.event.attempt_number
            and observation.scope == self._quota_status.expected_scope
            and any(window.state == "exhausted" for window in observation.windows)
        ):
            self._control.publish_quota_trigger(PauseTrigger(origin, observation))

    def _prepare_wait(
        self,
        history: CallHistory,
        record: AttemptRecord,
        /,
        *,
        includes_record: bool = False,
    ) -> CallWait | None:
        """Prepare candidate capacity facts; the pure state selects whether to use them.

        Returns:
            Prepared facts for a capacity classification, or no candidate.
        """
        assessment = record.retry_assessment
        if (
            self._control.reason is not None
            or assessment is None
            or assessment.retry_class != "capacity"
            or self._config.capacity_retry_limit == 0
        ):
            return None
        previous = history.attempts[:-1] if includes_record else history.attempts
        index = sum(
            attempt.retry_assessment is not None
            and attempt.retry_assessment.retry_class == "capacity"
            for attempt in previous
        )
        base = self._config.capacity_backoff_base_seconds
        cap = self._config.capacity_backoff_cap_seconds
        assert base is not None and cap is not None
        bound = capacity_jitter_bound(index, base, cap)
        context = CapacityWaitContext(
            kind="capacity",
            call_id=history.call.call_id,
            failed_attempt_number=record.attempt_number,
            retry_index=index,
            base_seconds=base,
            cap_seconds=cap,
            jitter_bound_seconds=bound,
            sampled_seconds=self._runtime.uniform(0.0, bound),
        )
        return CallWait(
            str(uuid4()),
            context,
            self._runtime.utc_now(),
            self._runtime.monotonic(),
            "prepared",
            None,
        )

    def _wait_event(
        self,
        wait: CallWait,
        kind: Literal["started", "finished"],
        end: WaitEnd | None,
    ) -> WaitEvent:
        """Build a wait event with fresh clocks and its exact retained context.

        Returns:
            The event to persist.
        """
        return WaitEvent(
            run_id=self._state.history.call.run_id,
            wait_id=wait.wait_id,
            context=wait.context,
            kind=kind,
            observed_at_utc=self._runtime.utc_now(),
            elapsed_seconds=max(
                0.0, self._runtime.monotonic() - wait.started_monotonic
            ),
            quota_observation=None,
            end=end,
            diagnostic=None,
        )

    async def _wait(self, state: RetryWait) -> None:
        """Start, await, and durably close one selected capacity delay."""
        event = self._wait_event(state.wait, "started", None)
        state = replace(state, wait=replace(state.wait, start_phase="submitted"))
        self._state = state
        settled = await settle(
            asyncio.create_task(self._evidence.record_wait_event(event))
        )
        if settled.cancellation is not None:
            self._control.note_cancellation(settled.cancellation, "owner")
        if isinstance(settled, SettledFailure):
            if isinstance(settled.error, CancelledError):
                self._control.note_cancellation(settled.error, "leaf")
            self._control.note_recording_failure(settled.error)
            self._state = state.write_failed(WaitWrite(event, None), settled.error)
            self._raise_settlement(settled)
            return
        cancellation = settled.cancellation
        cancelled = cancellation is not None or (
            self._control.reason is not None
            and self._control.reason.cancellation is not None
        )
        closure = (
            self._wait_closure(state.wait, "cancelled" if cancelled else "stop")
            if (cancellation is not None or self._control.reason is not None)
            else None
        )
        state = state.started(cancellation, self._control.reason, closure)
        self._state = state
        if closure is not None:
            await self._close_wait(state, closure, cancellation)
            return
        await self._delay(state)

    async def _delay(self, state: RetryWait) -> None:
        """Wait without a slot and always close a durably started delay."""
        cancellation: CancelledError | None = None
        failure: BaseException | None = None
        try:
            await self._runtime.sleep(state.wait.context.sampled_seconds)
        except CancelledError as error:
            cancellation = error
            self._note_active_cancellation(error)
        except BaseException as error:
            failure = error
            self._control.latch_stop(error)
        end: Literal["delay_elapsed", "cancelled", "stop"] = "delay_elapsed"
        if cancellation is not None:
            end = "cancelled"
        elif self._control.reason is not None:
            end = "stop"
        await self._close_wait(state, self._wait_closure(state.wait, end), cancellation)
        if failure is not None:
            reason = self._control.reason
            if reason is not None and reason.recording_failure is not None:
                raise failure from reason.recording_failure
            raise failure

    def _wait_closure(
        self, wait: CallWait, end: Literal["delay_elapsed", "cancelled", "stop"]
    ) -> WaitRecord:
        """Build the final summary from clocks sampled at closure.

        Returns:
            The wait record associated with this exact wait.
        """
        return WaitRecord(
            wait_id=wait.wait_id,
            context=wait.context,
            started_at_utc=wait.started_at_utc,
            ended_at_utc=self._runtime.utc_now(),
            elapsed_seconds=max(
                0.0, self._runtime.monotonic() - wait.started_monotonic
            ),
            end=end,
            diagnostic=None,
        )

    async def _close_wait(
        self, state: RetryWait, record: WaitRecord, cancellation: CancelledError | None
    ) -> None:
        """Retain the end write and preserve cancellation as primary."""
        event = self._wait_event(state.wait, "finished", record.end)
        settled = await settle(
            asyncio.create_task(self._evidence.record_wait_event(event))
        )
        if settled.cancellation is not None:
            self._control.note_cancellation(settled.cancellation, "owner")
            if cancellation is None:
                cancellation = settled.cancellation
        if isinstance(settled, SettledFailure):
            if isinstance(settled.error, CancelledError):
                self._control.note_cancellation(settled.error, "leaf")
            self._control.note_recording_failure(settled.error)
            self._state = state.write_failed(WaitWrite(event, record), settled.error)
            if cancellation is not None:
                raise cancellation from settled.error
            self._raise_settlement(settled)
            return
        self._state = state.completed(record, self._control.reason)
        if cancellation is not None:
            raise cancellation

    def _raise_settlement(self, settled: SettledFailure) -> None:
        """Propagate cancellation while retaining an independent write failure."""
        if settled.cancellation is not None:
            raise settled.cancellation from settled.error
        if isinstance(settled.error, CancelledError):
            raise settled.error


def _diagnostic(error: BaseException, /) -> str:
    """Describe an exception without masking the original if formatting fails.

    Returns:
        Its message or its type name when formatting fails.
    """
    try:
        return str(error)
    except Exception:
        return type(error).__name__


def _end_time(runtime: Runtime, /) -> str | None:
    """Sample an end time without masking an original exceptional outcome.

    Returns:
        The timestamp, or None if the clock itself fails.
    """
    try:
        return runtime.utc_now()
    except Exception:
        return None


def _exception_outcome(
    error: BaseException, /
) -> AttemptResult | AttemptCancelled | AttemptFailureEvidence | None:
    """Recover exact supervisor facts attached to an exceptional outcome.

    Returns:
        The retained supervisor outcome or None when no evidence was attached.
    """
    if isinstance(error, AttemptCancelled):
        return error
    attached = vars(error).get("process_supervisor_outcome")
    if isinstance(
        attached, (Completed, TimedOut, OutputLimitExceeded, InfrastructureFailure)
    ):
        return attached
    return failure_evidence(error)
