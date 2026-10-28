# SPDX-License-Identifier: Apache-2.0
"""Call-owner wiring through controlled supervisor and evidence boundaries."""

import asyncio
from asyncio import Semaphore
from pathlib import Path
from typing import override

import pytest

from script.eval.evidence import EvidenceStore
from script.eval.model import (
    AttemptEvidence,
    AttemptNumber,
    AttemptRecord,
    CapacityWaitContext,
    FrozenPlan,
    PreparedEvidence,
    QuotaObservation,
    QuotaProbeEvidence,
    QuotaProbeLifecycleInput,
    QuotaProbeRequest,
    QuotaProbeSettled,
    QuotaScope,
    QuotaTelemetryEvent,
    RetryAssessment,
    RetryClass,
    RunRecord,
    WaitEvent,
)
from script.eval.runner.coordinator.call_states import (
    AttemptWrite,
    CallHistory,
    EvidencePending,
    Finished,
    Queued,
    Stopped,
)
from script.eval.runner.coordinator.calls import CallOwner, _can_prepare_capacity_wait
from script.eval.runner.coordinator.control import RunControl
from script.eval.runner.coordinator.quota_states import PauseOrigin, PauseTrigger
from script.eval.runner.coordinator.state import WaitWrite
from script.eval.runner.ports import OutcomeClassifier, QuotaStatusReader, Runtime
from script.process_supervisor import (
    AttemptCancelled,
    AttemptFailureEvidence,
    AttemptObservation,
    AttemptRequest,
    AttemptResult,
    CapturedOutput,
    CleanupEvidence,
    Completed,
    DispatchStop,
    SignalAttempt,
)
from test.script.unit.eval.test_coordinator_states import (
    assessment,
    attempt_record,
    call,
    config,
    observation,
)


class Store(EvidenceStore):
    """Controlled attempt persistence with optional failure."""

    def __init__(self, failure: BaseException | None = None) -> None:
        self.failure = failure
        self.events: list[WaitEvent] = []
        self.seen: list[AttemptEvidence] = []
        self.slots: Semaphore | None = None
        self.forwarded: tuple[str, str, int, int, RetryAssessment | None] | None = None

    async def record_attempt(
        self,
        run_id: str,
        call_id: str,
        position: int,
        attempt_number: AttemptNumber,
        evidence: AttemptEvidence,
        retry_assessment: RetryAssessment | None,
        /,
    ) -> AttemptRecord:
        """Return a matching durable record or fail the submitted write."""
        assert self.slots is not None and not self.slots.locked()
        self.seen.append(evidence)
        self.forwarded = (run_id, call_id, position, attempt_number, retry_assessment)
        if self.failure is not None:
            raise self.failure
        record = attempt_record(
            attempt_number, "other", exit_status=0, retry_assessment=retry_assessment
        )
        if evidence.control_flow != "returned":
            outcome = (
                "cancelled"
                if evidence.control_flow == "cancelled"
                else "unexpected_exception"
            )
            return record.model_copy(
                update={
                    "control_flow": evidence.control_flow,
                    "outcome_kind": outcome,
                    "exit_status": None,
                }
            )
        return record

    async def create(
        self, output_directory: Path, plan: FrozenPlan, /
    ) -> PreparedEvidence:
        """Reject setup outside this test boundary."""
        raise AssertionError

    async def record_wait_event(self, event: WaitEvent, /) -> None:
        """Retain a wait event after the slot has been released."""
        assert self.slots is not None and not self.slots.locked()
        self.events.append(event)

    async def record_quota_probe_event(
        self, event: QuotaProbeLifecycleInput, /
    ) -> None:
        """Reject unexpected probe writes."""
        raise AssertionError

    async def record_quota_probe_settled(
        self, evidence: QuotaProbeEvidence, /
    ) -> QuotaProbeSettled:
        """Reject unexpected probe settlement."""
        raise AssertionError

    async def record_quota_telemetry(self, event: QuotaTelemetryEvent, /) -> None:
        """Reject unexpected telemetry writes."""
        raise AssertionError

    async def finalize(self, record: RunRecord, /) -> None:
        """Reject unexpected finalization."""
        raise AssertionError


class Classifier(OutcomeClassifier):
    """Return a controlled non-retry assessment."""

    def __init__(self) -> None:
        self.seen: AttemptEvidence | None = None
        self.result = assessment("other")

    def assess(self, evidence: AttemptEvidence, /) -> RetryAssessment:
        """Classify without inspecting output."""
        self.seen = evidence
        return self.result


class Clock(Runtime):
    """Provide a deterministic clock for the returned path."""

    def utc_now(self) -> str:
        """Return a fixed timestamp."""
        return "2026-01-01T00:00:00Z"

    def monotonic(self) -> float:
        """Return deterministic monotonic time."""
        return 1.0

    async def sleep(self, seconds: float, /) -> None:
        """Yield through the deterministic fake clock."""
        await asyncio.sleep(0)

    def uniform(self, lower: float, upper: float, /) -> float:
        """Select zero jitter for a deterministic wait."""
        return 0.0


class NoQuota(QuotaStatusReader):
    """Fail if the opt-out path attempts a passive quota read."""

    @property
    def expected_scope(self) -> QuotaScope | None:
        """No quota scope is used when disabled."""
        return None

    async def poll(
        self, request: QuotaProbeRequest, stop_dispatch: DispatchStop, /
    ) -> QuotaProbeEvidence:
        """Reject unexpected probes."""
        raise AssertionError

    async def observe_settled_attempt(
        self, evidence: AttemptEvidence, /
    ) -> QuotaObservation:
        """Reject quota reads."""
        raise AssertionError("quota opt-out must not read")


class Attempt:
    """Exercise the slot and supervisor hook at invocation."""

    def __init__(self, slots: Semaphore, control: RunControl) -> None:
        self.slots = slots
        self.control = control
        self.calls = 0

    async def __call__(
        self, request: AttemptRequest, stop_dispatch: DispatchStop, /
    ) -> AttemptResult:
        """Return a safely cleaned successful process."""
        assert self.slots.locked()
        assert stop_dispatch == self.control.supervisor_stop
        self.calls += 1
        return Completed(
            AttemptObservation(
                CapturedOutput(b"out", b"err"),
                1.0,
                CleanupEvidence(
                    "owned", (SignalAttempt("SIGKILL", "sent", None),), "reaped", None
                ),
            ),
            0,
        )


def owner(
    store: Store, slots: Semaphore, control: RunControl, attempt: Attempt
) -> CallOwner:
    """Bind typed controlled dependencies to one queued call."""
    store.slots = slots
    return CallOwner(
        Queued(CallHistory(call(), (), ())),
        config(),
        control,
        slots,
        attempt,
        Classifier(),
        NoQuota(),
        store,
        Clock(),
    )


async def test_success_is_recorded_after_supervisor_releases_slot() -> None:
    """A successful returned attempt reaches a durable terminal state."""
    # Given
    slots = Semaphore(1)
    control = RunControl()
    attempt = Attempt(slots, control)
    store = Store()
    classifier = Classifier()
    store.slots = slots
    initial = Queued(CallHistory(call(), (), ()))
    subject = CallOwner(
        initial,
        config(),
        control,
        slots,
        attempt,
        classifier,
        NoQuota(),
        store,
        Clock(),
    )

    # When
    result = await subject.run()

    # Then
    assert isinstance(result, Finished)
    assert result.outcome == "success"
    assert attempt.calls == 1
    assert len(store.seen) == 1
    assert store.forwarded == ("run", "call", 0, 1, assessment("other"))
    assert store.seen[0] is classifier.seen
    assert store.forwarded is not None and store.forwarded[-1] is classifier.result
    assert store.seen[0].request is initial.history.call.request
    assert store.seen[0].usage_telemetry == b"out"
    assert not slots.locked()


async def test_recording_failure_stops_dispatch_and_retains_attempt() -> None:
    """Failed evidence remains inspectable and closes the shared gate."""
    # Given
    slots = Semaphore(1)
    control = RunControl()
    error = OSError("write failed")
    store = Store(error)
    subject = owner(store, slots, control, Attempt(slots, control))

    # When
    result = await subject.run()

    # Then
    assert isinstance(result, EvidencePending)
    assert result.failure.error is error
    assert control.reason is not None
    assert control.reason.recording_failure is error
    assert not slots.locked()


async def test_stop_while_waiting_for_slot_prevents_invocation() -> None:
    """Recheck a shared stop after acquiring a contended slot."""
    # Given
    slots = Semaphore(1)
    await slots.acquire()
    control = RunControl()
    attempt = Attempt(slots, control)
    subject = owner(Store(), slots, control, attempt)
    task = asyncio.create_task(subject.run())
    await asyncio.sleep(0)

    # When
    control.latch_stop(RuntimeError("stop"))
    slots.release()
    result = await task

    # Then
    assert attempt.calls == 0
    assert result == subject.state
    assert not slots.locked()


class BlockingStore(Store):
    """Hold a submitted write until the test releases it."""

    def __init__(self) -> None:
        super().__init__()
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    @override
    async def record_attempt(
        self,
        run_id: str,
        call_id: str,
        position: int,
        attempt_number: AttemptNumber,
        evidence: AttemptEvidence,
        retry_assessment: RetryAssessment | None,
        /,
    ) -> AttemptRecord:
        """Wait for release before returning the durable record."""
        self.started.set()
        await self.release.wait()
        return await super().record_attempt(
            run_id, call_id, position, attempt_number, evidence, retry_assessment
        )


async def test_cancel_during_write_settles_and_preserves_cancellation() -> None:
    """A submitted attempt write completes before owner cancellation escapes."""
    # Given
    slots = Semaphore(1)
    control = RunControl()
    store = BlockingStore()
    subject = owner(store, slots, control, Attempt(slots, control))
    task = asyncio.create_task(subject.run())
    await store.started.wait()

    # When
    task.cancel()
    await asyncio.sleep(0)
    task.cancel()
    await asyncio.sleep(0)
    assert not task.done()
    store.release.set()
    with pytest.raises(asyncio.CancelledError):
        await task

    # Then
    assert len(store.seen) == 1
    assert control.reason is not None
    assert control.reason.cancellation is not None
    assert len(subject.state.history.attempts) == 1


class QuotaAttempt(Attempt):
    """Return a nonzero quota-blocked process outcome."""

    async def __call__(
        self, request: AttemptRequest, stop_dispatch: DispatchStop, /
    ) -> AttemptResult:
        """Preserve the supervisor observation while changing its exit status."""
        result = await super().__call__(request, stop_dispatch)
        assert isinstance(result, Completed)
        return Completed(result.observation, 1)


class QuotaClassifier(Classifier):
    """Recognize a quota exhaustion before evidence is written."""

    @override
    def assess(self, evidence: AttemptEvidence, /) -> RetryAssessment:
        """Return a controlled quota classification."""
        return assessment("quota")


class QuotaReader(NoQuota):
    """Return one scoped exhausted observation."""

    @property
    @override
    def expected_scope(self) -> QuotaScope | None:
        """Return the same verified scope as the observation."""
        return observation().scope

    @override
    async def observe_settled_attempt(
        self, evidence: AttemptEvidence, /
    ) -> QuotaObservation:
        """Return exhausted telemetry."""
        value = observation()
        window = value.windows[0].model_copy(update={"state": "exhausted"})
        return value.model_copy(update={"windows": (window,)})


class QuotaStore(Store):
    """Check pause and trigger ordering around required writes."""

    def __init__(self, control: RunControl, slots: Semaphore) -> None:
        super().__init__()
        self.control = control
        self.slots = slots
        self.telemetry_written = asyncio.Event()
        self.telemetry: QuotaTelemetryEvent | None = None

    @override
    async def record_attempt(
        self,
        run_id: str,
        call_id: str,
        position: int,
        attempt_number: AttemptNumber,
        evidence: AttemptEvidence,
        retry_assessment: RetryAssessment | None,
        /,
    ) -> AttemptRecord:
        """Require the global pause before the attempt write."""
        assert not self.control.dispatch_allowed()
        assert self.control.quota_trigger is None
        record = await super().record_attempt(
            run_id, call_id, position, attempt_number, evidence, retry_assessment
        )
        return record.model_copy(update={"exit_status": 1})

    @override
    async def record_quota_telemetry(self, event: QuotaTelemetryEvent, /) -> None:
        """Require the trigger to remain unpublished until the write returns."""
        assert self.slots is not None and not self.slots.locked()
        assert self.control.quota_trigger is None
        self.telemetry = event
        self.telemetry_written.set()


class ObservedControl(RunControl):
    """Signal only after the real trigger publication completes."""

    def __init__(self) -> None:
        super().__init__()
        self.published = asyncio.Event()

    @override
    def publish_quota_trigger(self, trigger: PauseTrigger, /) -> None:
        """Publish through the real control and then notify the test."""
        super().publish_quota_trigger(trigger)
        self.published.set()


async def test_quota_pause_precedes_writes_and_trigger_follows_telemetry() -> None:
    """Recognized exhaustion closes the gate before fallible persistence."""
    # Given
    slots = Semaphore(1)
    control = ObservedControl()
    store = QuotaStore(control, slots)
    subject = CallOwner(
        Queued(CallHistory(call(), (), ())),
        config(quota_wait_enabled=True),
        control,
        slots,
        QuotaAttempt(slots, control),
        QuotaClassifier(),
        QuotaReader(),
        store,
        Clock(),
    )
    task = asyncio.create_task(subject.run())

    # When
    await control.published.wait()

    # Then
    assert control.quota_trigger is not None
    assert store.telemetry is not None
    assert (
        store.telemetry.run_id,
        store.telemetry.call_id,
        store.telemetry.attempt_number,
    ) == ("run", "call", 1)
    assert control.quota_trigger.observation is store.telemetry.observation
    assert not slots.locked()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


class CapacityClassifier(Classifier):
    """Recognize a capacity failure eligible for a later retry."""

    @override
    def assess(self, evidence: AttemptEvidence, /) -> RetryAssessment:
        """Return a controlled capacity classification."""
        return assessment("capacity")


class CapacityStore(Store):
    """Persist the nonzero process result for the pending wait path."""

    @override
    async def record_attempt(
        self,
        run_id: str,
        call_id: str,
        position: int,
        attempt_number: AttemptNumber,
        evidence: AttemptEvidence,
        retry_assessment: RetryAssessment | None,
        /,
    ) -> AttemptRecord:
        """Return the durable nonzero record."""
        record = await super().record_attempt(
            run_id, call_id, position, attempt_number, evidence, retry_assessment
        )
        return record.model_copy(update={"exit_status": 1})


async def test_capacity_retry_closes_wait_before_retry() -> None:
    """A capacity failure records its wait before the next attempt."""
    # Given
    slots = Semaphore(1)
    control = RunControl()
    store = CapacityStore()
    store.slots = slots
    subject = CallOwner(
        Queued(CallHistory(call(), (), ())),
        config(
            capacity_retry_limit=1,
            capacity_backoff_base_seconds=1.0,
            capacity_backoff_cap_seconds=2.0,
        ),
        control,
        slots,
        QuotaAttempt(slots, control),
        CapacityClassifier(),
        NoQuota(),
        store,
        Clock(),
    )

    # When
    result = await subject.run()

    # Then
    assert isinstance(result, Finished)
    assert len(store.seen) == 2
    assert [event.kind for event in store.events] == ["started", "finished"]
    assert len(result.history.waits) == 1
    assert result.history.waits[0].end == "delay_elapsed"
    assert not slots.locked()


async def test_exceptional_attempt_retains_original_stop() -> None:
    """Exceptional evidence is pending and the original failure propagates."""
    # Given
    slots = Semaphore(1)
    control = RunControl()
    error = OSError("supervisor failure")

    async def attempt(
        request: AttemptRequest, stop_dispatch: DispatchStop, /
    ) -> AttemptResult:
        await asyncio.sleep(0)
        raise error

    store = Store()
    store.slots = slots
    subject = CallOwner(
        Queued(CallHistory(call(), (), ())),
        config(),
        control,
        slots,
        attempt,
        Classifier(),
        NoQuota(),
        store,
        Clock(),
    )

    # When
    with pytest.raises(OSError) as raised:
        await subject.run()

    # Then
    assert raised.value is error
    assert control.reason is not None
    assert control.reason.first is error
    assert len(store.seen) == 1
    assert store.seen[0].control_flow == "raised"
    assert not slots.locked()


class CancelledTelemetryStore(QuotaStore):
    """Raise the supplied leaf cancellation at the telemetry write."""

    def __init__(
        self, control: RunControl, slots: Semaphore, error: asyncio.CancelledError
    ) -> None:
        super().__init__(control, slots)
        self.error = error

    @override
    async def record_quota_telemetry(self, event: QuotaTelemetryEvent, /) -> None:
        """Fail the submitted telemetry write with its original cancellation."""
        assert self.slots is not None and not self.slots.locked()
        raise self.error


async def test_attempt_write_leaf_cancellation_is_preserved() -> None:
    """A cancelled evidence task retains its failed obligation and propagates."""
    # Given
    slots = Semaphore(1)
    control = RunControl()
    error = asyncio.CancelledError("leaf")
    subject = owner(Store(error), slots, control, Attempt(slots, control))

    # When
    with pytest.raises(asyncio.CancelledError) as raised:
        await subject.run()

    # Then
    assert raised.value is error
    assert isinstance(subject.state, EvidencePending)
    assert subject.state.failure.error is error
    assert control.reason is not None
    assert control.reason.cancellation is error
    assert control.reason.cancellation_origin == "leaf"


async def test_telemetry_write_leaf_cancellation_is_preserved() -> None:
    """A cancelled telemetry task retains its event and durable attempt."""
    # Given
    slots = Semaphore(1)
    control = RunControl()
    error = asyncio.CancelledError("leaf")
    store = CancelledTelemetryStore(control, slots, error)
    subject = CallOwner(
        Queued(CallHistory(call(), (), ())),
        config(quota_wait_enabled=True),
        control,
        slots,
        QuotaAttempt(slots, control),
        QuotaClassifier(),
        QuotaReader(),
        store,
        Clock(),
    )

    # When
    with pytest.raises(asyncio.CancelledError) as raised:
        await subject.run()

    # Then
    assert raised.value is error
    assert isinstance(subject.state, EvidencePending)
    assert subject.state.failure.error is error
    assert isinstance(subject.state.failure.obligation, QuotaTelemetryEvent)
    assert len(subject.state.history.attempts) == 1
    assert control.reason is not None
    assert control.reason.cancellation_origin == "leaf"


async def test_owner_cancellation_remains_primary_when_write_is_cancelled() -> None:
    """A concurrent owner cancellation retains the leaf failure as cause."""
    # Given
    slots = Semaphore(1)
    control = RunControl()
    leaf = asyncio.CancelledError("leaf")
    store = BlockingStore()
    store.failure = leaf
    subject = owner(store, slots, control, Attempt(slots, control))
    task = asyncio.create_task(subject.run())
    await store.started.wait()

    # When
    task.cancel("owner")
    await asyncio.sleep(0)
    store.release.set()
    with pytest.raises(asyncio.CancelledError) as raised:
        await task

    # Then
    assert raised.value is not leaf
    assert raised.value.__cause__ is leaf
    assert isinstance(subject.state, EvidencePending)
    assert subject.state.failure.error is leaf
    assert control.reason is not None
    assert control.reason.cancellation_origin == "owner"


class BlockingWaitStore(CapacityStore):
    """Hold one wait write while cancellation is delivered repeatedly."""

    def __init__(self, blocked_kind: str) -> None:
        super().__init__()
        self.blocked_kind = blocked_kind
        self.wait_started = asyncio.Event()
        self.release_wait = asyncio.Event()

    @override
    async def record_wait_event(self, event: WaitEvent, /) -> None:
        """Delay one selected event before its durable append."""
        if event.kind == self.blocked_kind:
            self.wait_started.set()
            await self.release_wait.wait()
        await super().record_wait_event(event)


async def test_repeated_cancellation_during_wait_start_closes_durable_wait() -> None:
    """A start completed under cancellation creates a durable closure."""
    # Given
    slots = Semaphore(1)
    control = RunControl()
    store = BlockingWaitStore("started")
    store.slots = slots
    subject = CallOwner(
        Queued(CallHistory(call(), (), ())),
        config(
            capacity_retry_limit=1,
            capacity_backoff_base_seconds=1.0,
            capacity_backoff_cap_seconds=2.0,
        ),
        control,
        slots,
        QuotaAttempt(slots, control),
        CapacityClassifier(),
        NoQuota(),
        store,
        Clock(),
    )
    task = asyncio.create_task(subject.run())
    await store.wait_started.wait()

    # When
    task.cancel("first")
    await asyncio.sleep(0)
    task.cancel("second")
    await asyncio.sleep(0)
    assert not task.done()
    store.release_wait.set()
    with pytest.raises(asyncio.CancelledError, match="first"):
        await task

    # Then
    assert [event.kind for event in store.events] == ["started", "finished"]
    assert store.events[-1].end == "cancelled"
    assert len(subject.state.history.waits) == 1
    assert subject.state.history.waits[0].end == "cancelled"
    assert len(store.seen) == 1


async def test_repeated_cancellation_during_wait_end_retains_closure() -> None:
    """A submitted end write remains owned through repeated cancellation."""
    # Given
    slots = Semaphore(1)
    control = RunControl()
    store = BlockingWaitStore("finished")
    store.slots = slots
    subject = CallOwner(
        Queued(CallHistory(call(), (), ())),
        config(
            capacity_retry_limit=1,
            capacity_backoff_base_seconds=1.0,
            capacity_backoff_cap_seconds=2.0,
        ),
        control,
        slots,
        QuotaAttempt(slots, control),
        CapacityClassifier(),
        NoQuota(),
        store,
        Clock(),
    )
    task = asyncio.create_task(subject.run())
    await store.wait_started.wait()

    # When
    task.cancel("first")
    await asyncio.sleep(0)
    task.cancel("second")
    await asyncio.sleep(0)
    assert not task.done()
    store.release_wait.set()
    with pytest.raises(asyncio.CancelledError, match="first"):
        await task

    # Then
    assert [event.kind for event in store.events] == ["started", "finished"]
    assert len(subject.state.history.waits) == 1
    assert len(store.seen) == 1


async def test_supervisor_cancellation_survives_latched_stop_and_is_recorded() -> None:
    """The supervisor's original cancellation and cleanup evidence survive."""
    # Given
    slots = Semaphore(1)
    control = RunControl()
    store = Store()
    store.slots = slots
    observed = AttemptObservation(
        CapturedOutput(b"partial", b""),
        1.0,
        CleanupEvidence(
            "owned", (SignalAttempt("SIGKILL", "sent", None),), "reaped", None
        ),
    )
    error = AttemptCancelled(observed)

    async def attempt(
        request: AttemptRequest, stop_dispatch: DispatchStop, /
    ) -> AttemptResult:
        stop_dispatch(error)
        await asyncio.sleep(0)
        raise error

    subject = CallOwner(
        Queued(CallHistory(call(), (), ())),
        config(),
        control,
        slots,
        attempt,
        Classifier(),
        NoQuota(),
        store,
        Clock(),
    )

    # When
    with pytest.raises(AttemptCancelled) as raised:
        await subject.run()

    # Then
    assert raised.value is error
    assert store.seen[0].outcome is error
    assert store.seen[0].usage_telemetry == b"partial"
    assert len(subject.state.history.attempts) == 1
    assert control.reason is not None
    assert control.reason.cancellation is error
    assert control.reason.cancellation_origin == "leaf"


async def test_supervisor_failure_retains_attached_cleanup_evidence() -> None:
    """A raised supervisor error persists its attached cleanup observations."""
    # Given
    slots = Semaphore(1)
    control = RunControl()
    store = Store()
    store.slots = slots
    observation_value = AttemptObservation(
        CapturedOutput(b"partial", b"err"),
        1.0,
        CleanupEvidence(
            "owned", (SignalAttempt("SIGKILL", "sent", None),), "reaped", None
        ),
    )
    attached = AttemptFailureEvidence(observation_value, None)
    error = RuntimeError("failure")
    vars(error)["process_supervisor_evidence"] = attached

    async def attempt(
        request: AttemptRequest, stop_dispatch: DispatchStop, /
    ) -> AttemptResult:
        stop_dispatch(error)
        await asyncio.sleep(0)
        raise error

    subject = CallOwner(
        Queued(CallHistory(call(), (), ())),
        config(),
        control,
        slots,
        attempt,
        Classifier(),
        NoQuota(),
        store,
        Clock(),
    )

    # When
    with pytest.raises(RuntimeError) as raised:
        await subject.run()

    # Then
    assert raised.value is error
    assert store.seen[0].outcome is attached
    assert len(subject.state.history.attempts) == 1
    assert control.reason is not None and control.reason.first is error


class FailedWaitStore(CapacityStore):
    """Fail one selected wait event after optionally blocking it."""

    def __init__(self, kind: str, error: BaseException) -> None:
        super().__init__()
        self.kind = kind
        self.error = error
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    @override
    async def record_wait_event(self, event: WaitEvent, /) -> None:
        """Retain the attempted event and fail its selected write."""
        if event.kind == self.kind:
            self.started.set()
            await self.release.wait()
            raise self.error
        await super().record_wait_event(event)


@pytest.mark.parametrize("kind", ["started", "finished"])
async def test_wait_write_failure_retains_exact_obligation(kind: str) -> None:
    """A failed wait write stops retries and retains its exact input."""
    # Given
    slots = Semaphore(1)
    control = RunControl()
    error = OSError("write")
    store = FailedWaitStore(kind, error)
    store.slots = slots
    subject = CallOwner(
        Queued(CallHistory(call(), (), ())),
        config(
            capacity_retry_limit=1,
            capacity_backoff_base_seconds=1.0,
            capacity_backoff_cap_seconds=2.0,
        ),
        control,
        slots,
        QuotaAttempt(slots, control),
        CapacityClassifier(),
        NoQuota(),
        store,
        Clock(),
    )
    task = asyncio.create_task(subject.run())
    await store.started.wait()

    # When
    store.release.set()
    result = await task

    # Then
    assert isinstance(result, EvidencePending)
    assert isinstance(result.failure.obligation, WaitWrite)
    assert result.failure.obligation.event.kind == kind
    assert result.failure.error is error
    assert control.reason is not None and control.reason.recording_failure is error
    assert len(store.seen) == 1


async def test_cancelled_wait_start_with_failure_preserves_cause() -> None:
    """Owner cancellation remains primary when its retained start write fails."""
    # Given
    slots = Semaphore(1)
    control = RunControl()
    error = OSError("start failed")
    store = FailedWaitStore("started", error)
    store.slots = slots
    subject = CallOwner(
        Queued(CallHistory(call(), (), ())),
        config(
            capacity_retry_limit=1,
            capacity_backoff_base_seconds=1.0,
            capacity_backoff_cap_seconds=2.0,
        ),
        control,
        slots,
        QuotaAttempt(slots, control),
        CapacityClassifier(),
        NoQuota(),
        store,
        Clock(),
    )
    task = asyncio.create_task(subject.run())
    await store.started.wait()

    # When
    task.cancel()
    await asyncio.sleep(0)
    task.cancel()
    await asyncio.sleep(0)
    assert not task.done()
    store.release.set()
    with pytest.raises(asyncio.CancelledError) as raised:
        await task

    # Then
    assert raised.value.__cause__ is error
    assert isinstance(subject.state, EvidencePending)
    assert isinstance(subject.state.failure.obligation, WaitWrite)
    assert subject.state.failure.error is error
    assert store.events == []


class CancellingAttempt:
    """Translate owner cancellation into supervisor cleanup evidence."""

    def __init__(self, started: asyncio.Event, cancelled: AttemptCancelled) -> None:
        self.started = started
        self.cancelled = cancelled
        self.calls = 0

    async def __call__(
        self, request: AttemptRequest, stop_dispatch: DispatchStop, /
    ) -> AttemptResult:
        """Signal entry and return the supervisor cancellation after cleanup."""
        self.calls += 1
        self.started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError as error:
            stop_dispatch(self.cancelled)
            raise self.cancelled from error
        raise AssertionError


async def test_owner_cancellation_during_attempt_is_recorded_as_owner() -> None:
    """An owner cancellation keeps its origin after supervisor cleanup."""
    # Given
    slots = Semaphore(1)
    control = RunControl()
    store = Store()
    store.slots = slots
    started = asyncio.Event()
    observation_value = AttemptObservation(
        CapturedOutput(b"partial", b""),
        1.0,
        CleanupEvidence(
            "owned", (SignalAttempt("SIGKILL", "sent", None),), "reaped", None
        ),
    )
    cancelled = AttemptCancelled(observation_value)
    attempt = CancellingAttempt(started, cancelled)

    subject = CallOwner(
        Queued(CallHistory(call(), (), ())),
        config(),
        control,
        slots,
        attempt,
        Classifier(),
        NoQuota(),
        store,
        Clock(),
    )
    task = asyncio.create_task(subject.run())
    await started.wait()

    # When
    task.cancel()
    with pytest.raises(AttemptCancelled) as raised:
        await task

    # Then
    assert raised.value is cancelled
    assert store.seen[0].outcome is cancelled
    assert control.reason is not None
    assert control.reason.cancellation_origin == "owner"
    assert len(subject.state.history.attempts) == 1


class UnsafeAttempt(QuotaAttempt):
    """Report unsafe cleanup through the supervisor stop hook."""

    async def __call__(
        self, request: AttemptRequest, stop_dispatch: DispatchStop, /
    ) -> AttemptResult:
        """Return unsafe cleanup and latch dispatch before returning."""
        result = await super().__call__(request, stop_dispatch)
        assert isinstance(result, Completed)
        cleanup = CleanupEvidence("acquisition_uncertain", (), "unknown", None)
        unsafe = Completed(
            AttemptObservation(result.observation.output, 1.0, cleanup), 1
        )
        stop_dispatch(unsafe)
        return unsafe


class UnsafeStore(CapacityStore):
    """Return an unsafe cleanup observation in the attempt record."""

    @override
    async def record_attempt(
        self,
        run_id: str,
        call_id: str,
        position: int,
        attempt_number: AttemptNumber,
        evidence: AttemptEvidence,
        retry_assessment: RetryAssessment | None,
        /,
    ) -> AttemptRecord:
        """Persist the unsafe cleanup facts supplied by the supervisor."""
        record = await super().record_attempt(
            run_id, call_id, position, attempt_number, evidence, retry_assessment
        )
        assert record.cleanup is not None
        cleanup = record.cleanup.model_copy(update={"process": "acquisition_uncertain"})
        return record.model_copy(update={"cleanup": cleanup})


async def test_unsafe_cleanup_never_retries_capacity_failure() -> None:
    """Unsafe cleanup refuses a retry despite a capacity allowance."""
    # Given
    slots = Semaphore(1)
    control = RunControl()
    store = UnsafeStore()
    store.slots = slots
    attempt = UnsafeAttempt(slots, control)
    subject = CallOwner(
        Queued(CallHistory(call(), (), ())),
        config(
            capacity_retry_limit=1,
            capacity_backoff_base_seconds=1.0,
            capacity_backoff_cap_seconds=2.0,
        ),
        control,
        slots,
        attempt,
        CapacityClassifier(),
        NoQuota(),
        store,
        Clock(),
    )

    # When
    result = await subject.run()

    # Then
    assert isinstance(result, Stopped)
    assert result.outcome == "failure"
    assert attempt.calls == 1
    assert control.reason is not None
    assert not control.dispatch_allowed()
    assert store.events == []


class MismatchedQuotaReader(QuotaReader):
    """Report an exhaustion associated with an unverified scope."""

    @property
    @override
    def expected_scope(self) -> QuotaScope | None:
        """Deliberately provide no matching verified scope."""
        return None


class RetryClock(Clock):
    """Notify after telemetry processing reaches the retry yield."""

    def __init__(self) -> None:
        self.yielded = asyncio.Event()

    @override
    async def sleep(self, seconds: float, /) -> None:
        """Signal the retry yield and yield to the event loop."""
        self.yielded.set()
        await asyncio.sleep(0)


async def test_mismatched_quota_scope_cannot_publish_trigger() -> None:
    """A persisted exhaustion from a different scope cannot authorize recovery."""
    # Given
    slots = Semaphore(1)
    control = RunControl()
    store = QuotaStore(control, slots)
    clock = RetryClock()
    subject = CallOwner(
        Queued(CallHistory(call(), (), ())),
        config(quota_wait_enabled=True),
        control,
        slots,
        QuotaAttempt(slots, control),
        QuotaClassifier(),
        MismatchedQuotaReader(),
        store,
        clock,
    )
    task = asyncio.create_task(subject.run())

    # When
    await clock.yielded.wait()

    # Then
    assert store.telemetry is not None
    assert control.quota_origin is not None
    assert control.quota_trigger is None
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


class MixedClassifier(Classifier):
    """Select independent infrastructure and capacity classifications."""

    def __init__(self) -> None:
        super().__init__()
        self.categories = iter(("infrastructure", "capacity", "other"))

    @override
    def assess(self, evidence: AttemptEvidence, /) -> RetryAssessment:
        """Return the next declared classification."""
        return RetryAssessment.model_validate({
            "retry_class": next(self.categories),
            "classification_basis": "test",
            "no_result_basis": "confident_absence",
            "diagnostic": None,
        })


async def test_infrastructure_and_capacity_allowances_are_independent() -> None:
    """Each retry category consumes its own finite allowance."""
    # Given
    slots = Semaphore(1)
    control = RunControl()
    store = CapacityStore()
    store.slots = slots
    attempt = QuotaAttempt(slots, control)
    subject = CallOwner(
        Queued(CallHistory(call(), (), ())),
        config(
            retry_limit=1,
            retry_nonzero_exit=True,
            capacity_retry_limit=1,
            capacity_backoff_base_seconds=1.0,
            capacity_backoff_cap_seconds=2.0,
        ),
        control,
        slots,
        attempt,
        MixedClassifier(),
        NoQuota(),
        store,
        Clock(),
    )

    # When
    result = await subject.run()

    # Then
    assert isinstance(result, Finished)
    assert attempt.calls == 3
    assert [event.kind for event in store.events] == ["started", "finished"]
    assert len(result.history.waits) == 1


class BlockingTelemetryStore(QuotaStore):
    """Hold a telemetry write until cancellation has been delivered."""

    def __init__(self, control: RunControl, slots: Semaphore) -> None:
        super().__init__(control, slots)
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    @override
    async def record_quota_telemetry(self, event: QuotaTelemetryEvent, /) -> None:
        """Persist telemetry only after the test releases it."""
        self.started.set()
        await self.release.wait()
        await super().record_quota_telemetry(event)


async def test_repeated_cancellation_during_telemetry_settles_write() -> None:
    """A submitted telemetry write settles before cancellation propagates."""
    # Given
    slots = Semaphore(1)
    control = RunControl()
    store = BlockingTelemetryStore(control, slots)
    subject = CallOwner(
        Queued(CallHistory(call(), (), ())),
        config(quota_wait_enabled=True),
        control,
        slots,
        QuotaAttempt(slots, control),
        QuotaClassifier(),
        QuotaReader(),
        store,
        Clock(),
    )
    task = asyncio.create_task(subject.run())
    await store.started.wait()

    # When
    task.cancel("first")
    await asyncio.sleep(0)
    task.cancel("second")
    await asyncio.sleep(0)
    assert not task.done()
    store.release.set()
    with pytest.raises(asyncio.CancelledError, match="first"):
        await task

    # Then
    assert store.telemetry is not None
    assert control.quota_trigger is None
    assert len(subject.state.history.attempts) == 1
    assert control.reason is not None and control.reason.cancellation_origin == "owner"


class GateClock(Clock):
    """Block the capacity delay and expose the following retry yield."""

    def __init__(self) -> None:
        self.waiting = asyncio.Event()
        self.release = asyncio.Event()
        self.yielded = asyncio.Event()

    @override
    def uniform(self, lower: float, upper: float, /) -> float:
        """Choose the full upper jitter bound."""
        return upper

    @override
    async def sleep(self, seconds: float, /) -> None:
        """Hold the nonzero capacity delay and signal the retry yield."""
        if seconds:
            self.waiting.set()
            await self.release.wait()
        else:
            self.yielded.set()
            await asyncio.sleep(0)


async def test_capacity_retry_rechecks_shared_quota_gate() -> None:
    """A quota pause during a capacity delay blocks its next dispatch."""
    # Given
    slots = Semaphore(1)
    control = RunControl()
    store = CapacityStore()
    store.slots = slots
    attempt = QuotaAttempt(slots, control)
    clock = GateClock()
    initial = Queued(CallHistory(call(), (), ()))
    subject = CallOwner(
        initial,
        config(
            capacity_retry_limit=1,
            capacity_backoff_base_seconds=1.0,
            capacity_backoff_cap_seconds=2.0,
        ),
        control,
        slots,
        attempt,
        CapacityClassifier(),
        NoQuota(),
        store,
        clock,
    )
    task = asyncio.create_task(subject.run())
    await clock.waiting.wait()

    # When
    control.pause_for_quota(PauseOrigin(initial.history.call, 1))
    clock.release.set()
    await clock.yielded.wait()

    # Then
    assert attempt.calls == 1
    assert not slots.locked()
    context = store.events[0].context
    assert isinstance(context, CapacityWaitContext)
    assert context.sampled_seconds == pytest.approx(1.0)
    control.resume_after_quota()
    result = await task
    assert isinstance(result, Finished)
    assert attempt.calls == 2


async def test_supervisor_hook_failure_preserves_attached_returned_outcome() -> None:
    """A stop-hook failure retains the supervisor result attached to the error."""
    # Given
    slots = Semaphore(1)
    control = RunControl()
    store = Store()
    store.slots = slots
    observation_value = AttemptObservation(
        CapturedOutput(b"partial", b"error"),
        1.0,
        CleanupEvidence(
            "owned", (SignalAttempt("SIGKILL", "sent", None),), "reaped", None
        ),
    )
    attached = Completed(observation_value, 1)
    error = RuntimeError("stop hook failed")
    vars(error)["process_supervisor_outcome"] = attached

    async def attempt(
        request: AttemptRequest, stop_dispatch: DispatchStop, /
    ) -> AttemptResult:
        await asyncio.sleep(0)
        raise error

    subject = CallOwner(
        Queued(CallHistory(call(), (), ())),
        config(),
        control,
        slots,
        attempt,
        Classifier(),
        NoQuota(),
        store,
        Clock(),
    )

    # When
    with pytest.raises(RuntimeError) as raised:
        await subject.run()

    # Then
    assert raised.value is error
    assert store.seen[0].outcome is attached
    assert store.seen[0].usage_telemetry == b"partial"
    assert len(subject.state.history.attempts) == 1


class UnknownResultClassifier(Classifier):
    """Classify capacity without proving absence of a semantic result."""

    @override
    def assess(self, evidence: AttemptEvidence, /) -> RetryAssessment:
        """Refuse to infer no result from a nonzero exit."""
        return assessment("capacity", "present_or_unknown")


async def test_capacity_retry_requires_confident_no_result() -> None:
    """A nonzero capacity failure without no-result proof is not repeated."""
    # Given
    slots = Semaphore(1)
    control = RunControl()
    store = CapacityStore()
    store.slots = slots
    attempt = QuotaAttempt(slots, control)
    subject = CallOwner(
        Queued(CallHistory(call(), (), ())),
        config(
            capacity_retry_limit=1,
            capacity_backoff_base_seconds=1.0,
            capacity_backoff_cap_seconds=2.0,
        ),
        control,
        slots,
        attempt,
        UnknownResultClassifier(),
        NoQuota(),
        store,
        Clock(),
    )

    # When
    result = await subject.run()

    # Then
    assert isinstance(result, Finished)
    assert result.outcome == "failure"
    assert attempt.calls == 1
    assert store.events == []


async def test_write_leaf_cancellation_takes_precedence_over_invocation_failure() -> (
    None
):
    """A leaf cancellation propagates with the original invocation error as cause."""
    # Given
    slots = Semaphore(1)
    control = RunControl()
    invocation_error = RuntimeError("invocation")
    write_cancellation = asyncio.CancelledError("write")
    store = Store(write_cancellation)
    store.slots = slots

    async def attempt(
        request: AttemptRequest, stop_dispatch: DispatchStop, /
    ) -> AttemptResult:
        await asyncio.sleep(0)
        raise invocation_error

    subject = CallOwner(
        Queued(CallHistory(call(), (), ())),
        config(),
        control,
        slots,
        attempt,
        Classifier(),
        NoQuota(),
        store,
        Clock(),
    )

    # When
    with pytest.raises(asyncio.CancelledError) as raised:
        await subject.run()

    # Then
    assert raised.value is write_cancellation
    assert raised.value.__cause__ is invocation_error
    assert control.reason is not None
    assert control.reason.first is invocation_error
    assert control.reason.cancellation is write_cancellation
    assert control.reason.cancellation_origin == "leaf"
    assert isinstance(subject.state, EvidencePending)
    assert subject.state.failure.error is write_cancellation
    assert isinstance(subject.state.failure.obligation, AttemptWrite)
    assert subject.state.failure.obligation.evidence is store.seen[0]


class CancelledQuotaReader(QuotaReader):
    """Raise or await cancellation during a passive read."""

    def __init__(self, error: asyncio.CancelledError | None) -> None:
        self.error = error
        self.started = asyncio.Event()

    @override
    async def observe_settled_attempt(
        self, evidence: AttemptEvidence, /
    ) -> QuotaObservation:
        """Signal the read boundary and raise leaf or owner cancellation."""
        self.started.set()
        if self.error is not None:
            raise self.error
        await asyncio.Event().wait()
        raise AssertionError


@pytest.mark.parametrize("origin", ["leaf", "owner"])
async def test_passive_quota_cancellation_preserves_origin(origin: str) -> None:
    """Passive-read cancellation stops with its durable attempt retained."""
    # Given
    slots = Semaphore(1)
    control = RunControl()
    store = QuotaStore(control, slots)
    leaf = asyncio.CancelledError("leaf") if origin == "leaf" else None
    reader = CancelledQuotaReader(leaf)
    attempt = QuotaAttempt(slots, control)
    subject = CallOwner(
        Queued(CallHistory(call(), (), ())),
        config(quota_wait_enabled=True),
        control,
        slots,
        attempt,
        QuotaClassifier(),
        reader,
        store,
        Clock(),
    )
    task = asyncio.create_task(subject.run())
    await reader.started.wait()

    # When
    if origin == "owner":
        task.cancel()
    with pytest.raises(asyncio.CancelledError) as raised:
        await task

    # Then
    if leaf is not None:
        assert raised.value is leaf
    assert control.reason is not None
    assert control.reason.cancellation_origin == origin
    assert isinstance(subject.state, Stopped)
    assert len(subject.state.history.attempts) == 1
    assert store.telemetry is None
    assert attempt.calls == 1


class FailedClassifier(Classifier):
    """Raise the supplied original classification failure."""

    def __init__(self, error: BaseException) -> None:
        super().__init__()
        self.error = error

    @override
    def assess(self, evidence: AttemptEvidence, /) -> RetryAssessment:
        """Fail after the exact supervisor evidence has been captured."""
        self.seen = evidence
        raise self.error


async def test_classification_failure_persists_unclassified_attempt() -> None:
    """Classification failure latches stop and records the original evidence."""
    # Given
    slots = Semaphore(1)
    control = RunControl()
    store = Store()
    store.slots = slots
    error = RuntimeError("classification")
    classifier = FailedClassifier(error)
    attempt = Attempt(slots, control)
    subject = CallOwner(
        Queued(CallHistory(call(), (), ())),
        config(),
        control,
        slots,
        attempt,
        classifier,
        NoQuota(),
        store,
        Clock(),
    )

    # When
    with pytest.raises(RuntimeError) as raised:
        await subject.run()

    # Then
    assert raised.value is error
    assert store.seen[0] is classifier.seen
    assert store.forwarded is not None and store.forwarded[-1] is None
    assert isinstance(subject.state, Stopped)
    assert len(subject.state.history.attempts) == 1
    assert control.reason is not None and control.reason.first is error
    assert attempt.calls == 1


class FailedJitterClock(Clock):
    """Raise the supplied failure when capacity jitter is prepared."""

    def __init__(self, error: BaseException) -> None:
        self.error = error

    @override
    def uniform(self, lower: float, upper: float, /) -> float:
        """Raise before any wait event is submitted."""
        raise self.error


class CapacityTelemetryStore(CapacityStore):
    """Accept passive telemetry after a nonzero capacity attempt."""

    @override
    async def record_quota_telemetry(self, event: QuotaTelemetryEvent, /) -> None:
        """Retain the telemetry event in the in-memory test boundary."""
        assert self.slots is not None and not self.slots.locked()


@pytest.mark.parametrize("quota_enabled", [False, True])
async def test_wait_preparation_failure_preserves_durable_attempt(
    quota_enabled: bool,
) -> None:
    """A failed jitter preparation leaves the already recorded attempt in history."""
    # Given
    slots = Semaphore(1)
    control = RunControl()
    store = CapacityTelemetryStore()
    store.slots = slots
    error = RuntimeError("jitter")
    attempt = QuotaAttempt(slots, control)
    subject = CallOwner(
        Queued(CallHistory(call(), (), ())),
        config(
            quota_wait_enabled=quota_enabled,
            capacity_retry_limit=1,
            capacity_backoff_base_seconds=1.0,
            capacity_backoff_cap_seconds=2.0,
        ),
        control,
        slots,
        attempt,
        CapacityClassifier(),
        QuotaReader(),
        store,
        FailedJitterClock(error),
    )

    # When
    with pytest.raises(RuntimeError) as raised:
        await subject.run()

    # Then
    assert raised.value is error
    assert isinstance(subject.state, Stopped)
    assert len(subject.state.history.attempts) == 1
    assert store.events == []
    assert attempt.calls == 1
    assert control.reason is not None and control.reason.first is error


async def test_classification_cancellation_preserves_invocation_failure() -> None:
    """A classifier's cancellation propagates with the earlier failure as cause."""
    # Given
    slots = Semaphore(1)
    control = RunControl()
    store = Store()
    store.slots = slots
    invocation_error = RuntimeError("supervisor")
    cancellation = asyncio.CancelledError("classification")
    classifier = FailedClassifier(cancellation)

    async def attempt(
        request: AttemptRequest, stop_dispatch: DispatchStop, /
    ) -> AttemptResult:
        await asyncio.sleep(0)
        raise invocation_error

    subject = CallOwner(
        Queued(CallHistory(call(), (), ())),
        config(),
        control,
        slots,
        attempt,
        classifier,
        NoQuota(),
        store,
        Clock(),
    )

    # When
    with pytest.raises(asyncio.CancelledError) as raised:
        await subject.run()

    # Then
    assert raised.value is cancellation
    assert raised.value.__cause__ is invocation_error
    assert store.seen[0] is classifier.seen
    assert store.forwarded is not None and store.forwarded[-1] is None
    assert isinstance(subject.state, Stopped)
    assert len(subject.state.history.attempts) == 1
    assert control.reason is not None
    assert control.reason.first is invocation_error
    assert control.reason.cancellation is cancellation
    assert control.reason.cancellation_origin == "leaf"


class FailedYieldClock(Clock):
    """Raise an error when an infrastructure retry yields."""

    def __init__(self, error: BaseException) -> None:
        self.error = error

    @override
    async def sleep(self, seconds: float, /) -> None:
        """Raise the original retry-yield failure."""
        await asyncio.sleep(0)
        raise self.error


class InfrastructureClassifier(Classifier):
    """Classify an infrastructure failure with no semantic result."""

    @override
    def assess(self, evidence: AttemptEvidence, /) -> RetryAssessment:
        """Return a controlled infrastructure classification."""
        return assessment("infrastructure")


async def test_retry_yield_failure_stops_queued_call_with_history() -> None:
    """A failed retry yield leaves a stopped call with its durable attempt."""
    # Given
    slots = Semaphore(1)
    control = RunControl()
    store = CapacityStore()
    store.slots = slots
    attempt = QuotaAttempt(slots, control)
    error = RuntimeError("yield")
    subject = CallOwner(
        Queued(CallHistory(call(), (), ())),
        config(retry_limit=1, retry_nonzero_exit=True),
        control,
        slots,
        attempt,
        InfrastructureClassifier(),
        NoQuota(),
        store,
        FailedYieldClock(error),
    )

    # When
    with pytest.raises(RuntimeError) as raised:
        await subject.run()

    # Then
    assert raised.value is error
    assert isinstance(subject.state, Stopped)
    assert subject.state.outcome == "failure"
    assert len(subject.state.history.attempts) == 1
    assert attempt.calls == 1
    assert control.reason is not None and control.reason.first is error


def cancellation_setup(
    store: Store,
) -> tuple[
    Semaphore, RunControl, AttemptCancelled, CancellingAttempt, CallOwner, asyncio.Event
]:
    """Bind one cancellable supervisor to a controlled evidence store."""
    slots = Semaphore(1)
    control = RunControl()
    store.slots = slots
    started = asyncio.Event()
    observed = AttemptObservation(
        CapturedOutput(b"partial", b""),
        1.0,
        CleanupEvidence(
            "owned", (SignalAttempt("SIGKILL", "sent", None),), "reaped", None
        ),
    )
    cancellation = AttemptCancelled(observed)
    attempt = CancellingAttempt(started, cancellation)
    subject = CallOwner(
        Queued(CallHistory(call(), (), ())),
        config(),
        control,
        slots,
        attempt,
        Classifier(),
        NoQuota(),
        store,
        Clock(),
    )
    return slots, control, cancellation, attempt, subject, started


async def test_owner_supervisor_cancellation_precedes_write_cancellation() -> None:
    """Owner cancellation survives a later leaf cancellation of its evidence write."""
    # Given
    write_cancellation = asyncio.CancelledError("write leaf")
    store = Store(write_cancellation)
    slots, control, owner_cancellation, attempt, subject, started = cancellation_setup(
        store
    )
    task = asyncio.create_task(subject.run())
    await started.wait()

    # When
    task.cancel()
    with pytest.raises(AttemptCancelled) as raised:
        await task

    # Then
    assert raised.value is owner_cancellation
    assert raised.value.__cause__ is write_cancellation
    assert control.reason is not None
    assert control.reason.cancellation is owner_cancellation
    assert control.reason.cancellation_origin == "owner"
    assert control.reason.recording_failure is write_cancellation
    assert isinstance(subject.state, EvidencePending)
    obligation = subject.state.failure.obligation
    assert isinstance(obligation, AttemptWrite)
    assert obligation.evidence is store.seen[0]
    assert obligation.evidence.outcome is owner_cancellation
    assert subject.state.failure.error is write_cancellation
    assert subject.state.history.attempts == ()
    assert len(store.seen) == 1
    assert attempt.calls == 1
    assert not slots.locked()


async def test_first_owner_cancellation_survives_later_write_cancellation() -> None:
    """A later owner cancellation cannot replace the supervisor cancellation."""
    # Given
    write_cancellation = asyncio.CancelledError("write leaf")
    store = BlockingStore()
    store.failure = write_cancellation
    _, control, first, attempt, subject, started = cancellation_setup(store)
    task = asyncio.create_task(subject.run())
    await started.wait()
    task.cancel("owner")
    await store.started.wait()

    # When
    task.cancel("later")
    await asyncio.sleep(0)
    assert not task.done()
    store.release.set()
    with pytest.raises(AttemptCancelled) as raised:
        await task

    # Then
    assert raised.value is first
    assert raised.value.__cause__ is write_cancellation
    assert control.reason is not None
    assert control.reason.cancellation is first
    assert control.reason.cancellation_origin == "owner"
    assert isinstance(subject.state, EvidencePending)
    assert subject.state.failure.error is write_cancellation
    assert attempt.calls == 1


class ForeignCancellationStore(Store):
    """Latch cancellation belonging to another owner while recording."""

    def __init__(
        self, control: RunControl, cancellation: asyncio.CancelledError
    ) -> None:
        super().__init__()
        self.control = control
        self.cancellation = cancellation

    @override
    async def record_attempt(
        self,
        run_id: str,
        call_id: str,
        position: int,
        attempt_number: AttemptNumber,
        evidence: AttemptEvidence,
        retry_assessment: RetryAssessment | None,
        /,
    ) -> AttemptRecord:
        """Model another owner's cancellation before this attempt is durable."""
        self.control.note_cancellation(self.cancellation, "owner")
        return await super().record_attempt(
            run_id, call_id, position, attempt_number, evidence, retry_assessment
        )


async def test_foreign_owner_cancellation_stops_without_propagating() -> None:
    """A shared stop cannot inject another call's exception into this owner."""
    # Given
    slots = Semaphore(1)
    control = RunControl()
    foreign = asyncio.CancelledError("another call")
    store = ForeignCancellationStore(control, foreign)
    attempt = Attempt(slots, control)
    subject = owner(store, slots, control, attempt)

    # When
    result = await subject.run()

    # Then
    assert isinstance(result, Stopped)
    assert result.outcome == "cancelled"
    assert len(result.history.attempts) == 1
    assert control.reason is not None
    assert control.reason.cancellation is foreign
    assert attempt.calls == 1
    assert not slots.locked()


@pytest.mark.parametrize(
    ("stopped", "category", "limit", "expected"),
    [
        (False, "capacity", 1, True),
        (True, "capacity", 1, False),
        (False, None, 1, False),
        (False, "infrastructure", 1, False),
        (False, "capacity", 0, False),
    ],
    ids=["candidate", "stopped", "unclassified", "other category", "disabled"],
)
def test_capacity_wait_candidate_guard(
    stopped: bool, category: RetryClass | None, limit: int, expected: bool
) -> None:
    """Candidate preparation remains separate from retry eligibility."""
    # Given
    control = RunControl()
    if stopped:
        control.latch_stop(RuntimeError("stop"))
    classification = None if category is None else assessment(category)
    settings = config(
        capacity_retry_limit=limit,
        capacity_backoff_base_seconds=1.0,
        capacity_backoff_cap_seconds=2.0,
    )

    # When
    result = _can_prepare_capacity_wait(control.reason, classification, settings)

    # Then
    assert result is expected


class LeafCancellingAttempt:
    """Raise one supervisor cancellation without cancelling the owner task."""

    def __init__(self, error: AttemptCancelled) -> None:
        self.error = error
        self.calls = 0

    async def __call__(
        self, request: AttemptRequest, stop_dispatch: DispatchStop, /
    ) -> AttemptResult:
        """Latch stop and propagate the exact leaf cancellation."""
        self.calls += 1
        stop_dispatch(self.error)
        await asyncio.sleep(0)
        raise self.error


def leaf_cancellation_setup(
    store: Store,
) -> tuple[RunControl, AttemptCancelled, LeafCancellingAttempt, CallOwner]:
    """Bind a leaf-cancelling supervisor to a controlled evidence store."""
    slots = Semaphore(1)
    control = RunControl()
    store.slots = slots
    observed = AttemptObservation(
        CapturedOutput(b"partial", b""),
        1.0,
        CleanupEvidence(
            "owned", (SignalAttempt("SIGKILL", "sent", None),), "reaped", None
        ),
    )
    cancellation = AttemptCancelled(observed)
    attempt = LeafCancellingAttempt(cancellation)
    subject = CallOwner(
        Queued(CallHistory(call(), (), ())),
        config(),
        control,
        slots,
        attempt,
        Classifier(),
        NoQuota(),
        store,
        Clock(),
    )
    return control, cancellation, attempt, subject


async def test_leaf_supervisor_cancellation_precedes_later_owner_cancellation() -> None:
    """The original leaf cancellation survives owner cancellation during its write."""
    # Given
    store = BlockingStore()
    control, first, attempt, subject = leaf_cancellation_setup(store)
    task = asyncio.create_task(subject.run())
    await store.started.wait()

    # When
    task.cancel("later owner")
    await asyncio.sleep(0)
    assert not task.done()
    store.release.set()
    with pytest.raises(AttemptCancelled) as raised:
        await task

    # Then
    assert raised.value is first
    assert store.seen[0].outcome is first
    assert isinstance(subject.state, Stopped)
    assert len(subject.state.history.attempts) == 1
    assert control.reason is not None
    assert control.reason.cancellation is first
    assert control.reason.cancellation_origin == "leaf"
    assert attempt.calls == 1


async def test_leaf_supervisor_cancellation_precedes_write_leaf_cancellation() -> None:
    """The original leaf cancellation chains a later cancelled evidence write."""
    # Given
    later = asyncio.CancelledError("write leaf")
    store = Store(later)
    control, first, attempt, subject = leaf_cancellation_setup(store)

    # When
    with pytest.raises(AttemptCancelled) as raised:
        await subject.run()

    # Then
    assert raised.value is first
    assert raised.value.__cause__ is later
    assert isinstance(subject.state, EvidencePending)
    obligation = subject.state.failure.obligation
    assert isinstance(obligation, AttemptWrite)
    assert obligation.evidence is store.seen[0]
    assert obligation.evidence.outcome is first
    assert subject.state.failure.error is later
    assert subject.state.history.attempts == ()
    assert control.reason is not None
    assert control.reason.cancellation is first
    assert control.reason.cancellation_origin == "leaf"
    assert control.reason.recording_failure is later
    assert attempt.calls == 1
