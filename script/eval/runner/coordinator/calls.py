# SPDX-License-Identifier: Apache-2.0
"""One call's typed dispatch and durable settlement wiring.

Returned attempts and passive telemetry are wired. Exceptional supervisor
completion, retry waits and cancellation closure remain pending implementation.
"""

import asyncio
from asyncio import CancelledError, Semaphore
from typing import Never

from script.eval.evidence import EvidenceStore
from script.eval.model import (
    AttemptEvidence,
    HarnessConfig,
    QuotaTelemetryEvent,
)
from script.eval.runner.ports import (
    AttemptCall,
    OutcomeClassifier,
    QuotaStatusReader,
    Runtime,
)
from script.process_supervisor import AttemptRequest, AttemptResult

from .call_states import (
    Attempting,
    CallState,
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
from .settlement import SettledFailure, SettledValue, settle


class CallOwner:
    """Own the state and effects of one planned call.

    This increment wires returned attempts; exceptional supervisor completion
    and retry waits are explicit pending leaves, not completed lifecycle paths.
    """

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

    @property
    def state(self) -> CallState:
        """The current authoritative call state."""
        return self._state

    async def run(self) -> CallState:
        """Dispatch and settle this call until terminal or a pending leaf.

        Returns:
            The current terminal or evidence-pending state.

        Raises:
            CancelledError: The owner or an invocation was cancelled.
        """
        try:
            return await self._run()
        except CancelledError as cancellation:
            self._control.note_cancellation(cancellation, "owner")
            raise

    async def _run(self) -> CallState:
        """Advance the typed state until a terminal state or pending leaf.

        Returns:
            The current terminal or evidence-pending state.

        Raises:
            RuntimeError: The owner is already running an attempt.
        """
        while True:
            match self._state:
                case Queued() as queued:
                    await self._dispatch(queued)
                case Recording() as recording:
                    await self._record(recording)
                case ObservingQuota() as observing:
                    await self._observe(observing)
                case RecordingTelemetry() as telemetry:
                    await self._record_telemetry(telemetry)
                case Finished() | EvidencePending() | Stopped():
                    return self._state
                case RetryWait():
                    await _pending_retry_wait()
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
                result = await self._invoke(request)
                ended = self._runtime.utc_now()
            output = result.observation.output
            evidence = AttemptEvidence(
                "returned",
                result,
                None,
                None,
                request,
                started,
                ended,
                None if output is None else output.stdout,
            )
            assessment = self._classifier.assess(evidence)
            if self._config.quota_wait_enabled and assessment.retry_class == "quota":
                self._control.pause_for_quota(PauseOrigin(state.history.call, number))
            assert isinstance(self._state, Attempting)
            self._state = self._state.capture(evidence, assessment)
            return
        self._state = Stopped(
            state.history, "not_started" if not state.history.attempts else "failure"
        )

    async def _invoke(self, request: AttemptRequest) -> AttemptResult:
        """Invoke the supervisor and retain the reason for exceptional control flow.

        Returns:
            The returned supervisor result.

        """
        try:
            return await self._attempt(request, self._control.supervisor_stop)
        except CancelledError as cancellation:
            self._control.note_cancellation(cancellation, "leaf")
            _pending_exception_evidence(cancellation)
        except BaseException as error:
            self._control.latch_stop(error)
            _pending_exception_evidence(error)

    async def _record(self, state: Recording) -> None:
        """Retain the attempt write before selecting its next state."""
        _pending_capacity_preparation(state, self._config)
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
            case SettledFailure(error, cancellation):
                if isinstance(error, CancelledError):
                    self._control.note_cancellation(error, "leaf")
                self._control.note_recording_failure(error)
                self._state = state.write_failed(error)
            case SettledValue(record, cancellation):
                self._state = state.persisted(
                    record, self._config, self._control.reason, None
                )
        if cancellation is not None:
            if isinstance(settled, SettledFailure):
                raise cancellation from settled.error
            raise cancellation
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
                if observation.scope is not None:
                    self._publish_trigger(state, origin)
                self._state = state.persisted(self._config, self._control.reason, None)
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


async def _pending_retry_wait() -> None:
    """Mark the unimplemented durable retry-wait lifecycle explicitly."""
    raise NotImplementedError("retry-wait lifecycle is pending")


def _pending_capacity_preparation(state: Recording, config: HarnessConfig, /) -> None:
    """Stop before submission when a capacity wait may need preparation.

    This conservative seam leaves retry eligibility to the pure transition once
    wait preparation is implemented, without claiming an attempt write occurred.

    Raises:
        NotImplementedError: Capacity wait preparation is pending.
    """
    assessment = state.attempt.assessment
    if (
        assessment is not None
        and assessment.retry_class == "capacity"
        and config.capacity_retry_limit > 0
    ):
        raise NotImplementedError("capacity wait preparation is pending")


def _pending_exception_evidence(error: BaseException, /) -> Never:
    """Leave exceptional supervisor evidence to the next implementation phase.

    The original exception remains the propagated control flow; submitted
    attempt evidence is not yet constructed or persisted on this path.

    """
    raise error
