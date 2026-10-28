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
    RunRecord,
    WaitEvent,
)
from script.eval.runner.coordinator.call_states import (
    CallHistory,
    EvidencePending,
    Finished,
    Queued,
    Recording,
)
from script.eval.runner.coordinator.calls import CallOwner
from script.eval.runner.coordinator.control import RunControl
from script.eval.runner.coordinator.quota_states import PauseTrigger
from script.eval.runner.ports import OutcomeClassifier, QuotaStatusReader, Runtime
from script.process_supervisor import (
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
        return attempt_record(
            attempt_number, "other", exit_status=0, retry_assessment=retry_assessment
        )

    async def create(
        self, output_directory: Path, plan: FrozenPlan, /
    ) -> PreparedEvidence:
        """Reject setup outside this test boundary."""
        raise AssertionError

    async def record_wait_event(self, event: WaitEvent, /) -> None:
        """Reject unexpected wait writes."""
        raise AssertionError

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
        """Reject unexpected clock use."""
        raise AssertionError

    async def sleep(self, seconds: float, /) -> None:
        """Reject unexpected waits."""
        raise AssertionError

    def uniform(self, lower: float, upper: float, /) -> float:
        """Reject unexpected jitter."""
        raise AssertionError


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


async def test_capacity_retry_stops_at_named_pending_preparation() -> None:
    """A capacity failure stops before submitting its attempt write."""
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
    with pytest.raises(NotImplementedError, match="capacity wait preparation"):
        await subject.run()

    # Then
    assert store.seen == []
    assert isinstance(subject.state, Recording)
    assert subject.state.history.attempts == ()
    assert subject.state.attempt.assessment == assessment("capacity")
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

    subject = CallOwner(
        Queued(CallHistory(call(), (), ())),
        config(),
        control,
        slots,
        attempt,
        Classifier(),
        NoQuota(),
        Store(),
        Clock(),
    )

    # When
    with pytest.raises(OSError) as raised:
        await subject.run()

    # Then
    assert raised.value is error
    assert control.reason is not None
    assert control.reason.first is error
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
