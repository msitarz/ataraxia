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
)
from script.eval.runner.coordinator.calls import CallOwner
from script.eval.runner.coordinator.control import RunControl
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

    def __init__(self, failure: Exception | None = None) -> None:
        self.failure = failure
        self.seen: list[AttemptEvidence] = []

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
        self.seen.append(evidence)
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

    def assess(self, evidence: AttemptEvidence, /) -> RetryAssessment:
        """Classify without inspecting output."""
        return assessment("other")


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


@pytest.mark.asyncio
async def test_success_is_recorded_after_supervisor_releases_slot() -> None:
    """A successful returned attempt reaches a durable terminal state."""
    slots = Semaphore(1)
    control = RunControl()
    attempt = Attempt(slots, control)
    store = Store()
    subject = owner(store, slots, control, attempt)

    result = await subject.run()

    assert isinstance(result, Finished)
    assert result.outcome == "success"
    assert attempt.calls == 1
    assert len(store.seen) == 1
    assert not slots.locked()


@pytest.mark.asyncio
async def test_recording_failure_stops_dispatch_and_retains_attempt() -> None:
    """Failed evidence remains inspectable and closes the shared gate."""
    slots = Semaphore(1)
    control = RunControl()
    error = OSError("write failed")
    store = Store(error)
    subject = owner(store, slots, control, Attempt(slots, control))

    result = await subject.run()

    assert isinstance(result, EvidencePending)
    assert result.failure.error is error
    assert control.reason is not None
    assert control.reason.recording_failure is error
    assert not slots.locked()


@pytest.mark.asyncio
async def test_stop_while_waiting_for_slot_prevents_invocation() -> None:
    """Recheck a shared stop after acquiring a contended slot."""
    slots = Semaphore(1)
    await slots.acquire()
    control = RunControl()
    attempt = Attempt(slots, control)
    subject = owner(Store(), slots, control, attempt)
    task = asyncio.create_task(subject.run())
    await asyncio.sleep(0)

    control.latch_stop(RuntimeError("stop"))
    slots.release()
    result = await task

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


@pytest.mark.asyncio
async def test_cancel_during_write_settles_and_preserves_cancellation() -> None:
    """A submitted attempt write completes before owner cancellation escapes."""
    slots = Semaphore(1)
    control = RunControl()
    store = BlockingStore()
    subject = owner(store, slots, control, Attempt(slots, control))
    task = asyncio.create_task(subject.run())
    await store.started.wait()

    task.cancel()
    await asyncio.sleep(0)
    assert not task.done()
    store.release.set()
    with pytest.raises(asyncio.CancelledError):
        await task

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

    def __init__(self, control: RunControl) -> None:
        super().__init__()
        self.control = control
        self.telemetry_written = asyncio.Event()

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
        assert self.control.quota_trigger is None
        self.telemetry_written.set()


@pytest.mark.asyncio
async def test_quota_pause_precedes_writes_and_trigger_follows_telemetry() -> None:
    """Recognized exhaustion closes the gate before fallible persistence."""
    slots = Semaphore(1)
    control = RunControl()
    store = QuotaStore(control)
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

    await store.telemetry_written.wait()
    for _ in range(20):
        if control.quota_trigger is not None or task.done():
            break
        await asyncio.sleep(0)

    assert control.quota_trigger is not None
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


@pytest.mark.asyncio
async def test_capacity_retry_stops_at_named_pending_preparation() -> None:
    """A durable capacity failure reaches the explicit unfinished boundary."""
    slots = Semaphore(1)
    control = RunControl()
    store = CapacityStore()
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

    with pytest.raises(NotImplementedError, match="capacity wait preparation"):
        await subject.run()

    assert len(store.seen) == 1
    assert not slots.locked()


@pytest.mark.asyncio
async def test_exceptional_attempt_retains_original_stop() -> None:
    """Exceptional evidence is pending and the original failure propagates."""
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

    with pytest.raises(OSError) as raised:
        await subject.run()

    assert raised.value is error
    assert control.reason is not None
    assert control.reason.first is error
    assert not slots.locked()
