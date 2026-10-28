# SPDX-License-Identifier: Apache-2.0
"""Quota-owner bounded wait wiring through controlled evidence effects."""

import asyncio
from asyncio import CancelledError, Event
from typing import override

import pytest

from script.eval.model import (
    QuotaProbeEvidence,
    QuotaProbeLifecycleInput,
    QuotaProbeRecord,
    QuotaProbeRequest,
    QuotaProbeSettled,
    QuotaScope,
    QuotaWaitContext,
    WaitEvent,
)
from script.eval.runner.coordinator.call_states import CallHistory
from script.eval.runner.coordinator.control import RunControl
from script.eval.runner.coordinator.quota import QuotaOwner, _reset_hint
from script.eval.runner.coordinator.quota_states import (
    Draining,
    Open,
    PauseOrigin,
    ProbeEvidencePending,
    QuotaEvidencePending,
    QuotaHistory,
    QuotaStopped,
)
from script.eval.runner.coordinator.state import WaitWrite
from script.eval.runner.quota_evidence import attach_quota_probe_evidence
from script.process_supervisor import DispatchStop
from test.script.unit.eval.test_coordinator_calls import Clock, NoQuota, Store
from test.script.unit.eval.test_coordinator_states import (
    call,
    config,
    observation,
    process_fields,
    recording,
    waiting,
)


class WaitStore(Store):
    """Capture wait writes and optionally fail or block a selected event."""

    def __init__(self) -> None:
        super().__init__()
        self.entered = Event()
        self.release = Event()
        self.block: str | None = None
        self.fail: str | None = None
        self.error: BaseException = OSError("wait write failed")
        self.attempted: list[WaitEvent] = []

    @override
    async def record_wait_event(self, event: WaitEvent, /) -> None:
        """Record the exact event unless its controlled write fails."""
        self.attempted.append(event)
        if event.kind == self.block:
            self.entered.set()
            await self.release.wait()
        if event.kind == self.fail:
            raise self.error
        self.events.append(event)


def paused_control() -> RunControl:
    """Latch the same call and attempt represented by the wait context.

    Returns:
        The paused shared control.
    """
    control = RunControl()
    control.pause_for_quota(PauseOrigin(call(), 1))
    return control


def owner(store: WaitStore, control: RunControl | None = None) -> QuotaOwner:
    """Build a probe-disabled owner with real validated values.

    Returns:
        The owner under test.
    """
    return QuotaOwner(
        Draining(waiting().context),
        QuotaHistory((), ()),
        config(quota_wait_enabled=True, quota_probe_budget=0),
        control or paused_control(),
        NoQuota(),
        store,
        Clock(),
        "run",
    )


async def test_zero_probe_budget_closes_a_durable_wait() -> None:
    # Given
    store = WaitStore()
    control = paused_control()
    quota = owner(store, control)

    # When
    result = await quota.recover()

    # Then
    assert not control.dispatch_allowed()
    assert isinstance(result, QuotaStopped)
    assert [event.kind for event in store.events] == ["started", "finished"]
    assert store.events[1].end == "bound"
    assert quota.history.waits[0].wait_id == store.events[0].wait_id
    assert quota.history.waits[0].end == "bound"
    assert quota.history.probes == ()


async def test_failed_closure_retains_the_exact_obligation() -> None:
    # Given
    store = WaitStore()
    store.fail = "finished"
    control = paused_control()
    quota = owner(store, control)

    # When
    result = await quota.recover()

    # Then
    assert isinstance(result, QuotaEvidencePending)
    assert isinstance(result.failures[0].obligation, WaitWrite)
    assert result.failures[0].obligation.record is not None
    assert result.failures[0].obligation.event.wait_id == store.events[0].wait_id
    assert result.failures[0].error is store.error
    assert quota.history.waits == ()
    assert control.reason is not None
    assert control.reason.recording_failure is store.error
    assert not control.dispatch_allowed()


async def test_cancellation_during_start_still_closes_the_wait() -> None:
    # Given
    store = WaitStore()
    store.block = "started"
    quota = owner(store)
    task = asyncio.create_task(quota.recover())
    await store.entered.wait()

    # When
    task.cancel("first")
    await asyncio.sleep(0)
    assert not task.done()
    task.cancel("second")
    await asyncio.sleep(0)
    assert not task.done()
    store.release.set()
    with pytest.raises(CancelledError, match="first"):
        await task

    # Then
    assert [event.kind for event in store.events] == ["started", "finished"]
    assert store.events[1].end == "cancelled"
    assert quota.history.waits[0].end == "cancelled"
    assert isinstance(quota.state, QuotaStopped)


async def test_invalid_trigger_stops_without_a_probe() -> None:
    # Given
    store = WaitStore()
    quota = QuotaOwner(
        Draining(waiting().context),
        QuotaHistory((), ()),
        config(quota_wait_enabled=True),
        paused_control(),
        NoQuota(),
        store,
        Clock(),
        "run",
    )

    # When
    result = await quota.recover()

    # Then
    assert isinstance(result, QuotaStopped)
    assert store.events[-1].end == "unknown"


async def test_failed_start_retains_its_event_without_claiming_a_wait() -> None:
    # Given
    store = WaitStore()
    store.fail = "started"
    control = paused_control()
    quota = owner(store, control)

    # When
    result = await quota.recover()

    # Then
    assert isinstance(result, QuotaEvidencePending)
    assert isinstance(result.failures[0].obligation, WaitWrite)
    assert result.failures[0].obligation.event.kind == "started"
    assert result.failures[0].obligation.record is None
    assert result.failures[0].error is store.error
    assert quota.history.waits == ()
    assert not control.dispatch_allowed()


async def test_cancellation_stays_primary_when_closure_fails() -> None:
    # Given
    store = WaitStore()
    store.block = "started"
    store.fail = "finished"
    quota = owner(store)
    task = asyncio.create_task(quota.recover())
    await store.entered.wait()

    # When
    task.cancel("original")
    store.release.set()
    with pytest.raises(CancelledError, match="original") as caught:
        await task

    # Then
    assert caught.value.__cause__ is store.error
    assert isinstance(quota.state, QuotaEvidencePending)
    assert quota.history.waits == ()


async def test_another_owners_cancellation_stops_without_being_raised() -> None:
    # Given
    store = WaitStore()
    control = paused_control()
    cancellation = CancelledError("other owner")
    control.note_cancellation(cancellation, "leaf")
    quota = owner(store, control)

    # When
    result = await quota.recover()

    # Then
    assert isinstance(result, QuotaStopped)
    assert store.events[-1].end == "cancelled"
    assert control.reason is not None
    assert control.reason.cancellation is cancellation
    assert not control.dispatch_allowed()


async def test_cumulative_bound_forbids_probe_even_with_budget_available() -> None:
    # Given
    store = WaitStore()
    context = waiting().context.model_copy(
        update={"cumulative_waited_before_seconds": 1.0, "wait_limit_seconds": 1.0}
    )
    control = paused_control()
    quota = QuotaOwner(
        Draining(context),
        QuotaHistory((), ()),
        config(quota_wait_enabled=True, quota_wait_limit_seconds=1.0),
        control,
        NoQuota(),
        store,
        Clock(),
        "run",
    )

    # When
    result = await quota.recover()

    # Then
    assert isinstance(result, QuotaStopped)
    assert store.events[-1].end == "bound"
    assert quota.history.probes == ()
    assert not control.dispatch_allowed()


@pytest.mark.parametrize(
    ("kind", "has_record"),
    [("started", False), ("finished", True)],
    ids=("start", "closure"),
)
async def test_leaf_cancellation_retains_exact_failed_write(
    kind: str, has_record: bool
) -> None:
    # Given
    store = WaitStore()
    store.fail = kind
    error = CancelledError("leaf write")
    store.error = error
    control = paused_control()
    quota = owner(store, control)

    # When
    with pytest.raises(CancelledError) as caught:
        await quota.recover()

    # Then
    assert caught.value is error
    assert error.__cause__ is None
    assert isinstance(quota.state, QuotaEvidencePending)
    assert quota.state.failures[0].error is error
    assert isinstance(quota.state.failures[0].obligation, WaitWrite)
    assert quota.state.failures[0].obligation.event is store.attempted[-1]
    assert (quota.state.failures[0].obligation.record is not None) is has_record
    assert quota.history.waits == ()
    assert control.reason is not None
    assert control.reason.cancellation is error
    assert control.reason.cancellation_origin == "leaf"
    assert control.reason.recording_failure is error
    assert not control.dispatch_allowed()


async def test_repeated_cancellation_during_closure_retains_write() -> None:
    # Given
    store = WaitStore()
    store.block = "finished"
    control = paused_control()
    quota = owner(store, control)
    task = asyncio.create_task(quota.recover())
    await store.entered.wait()

    # When
    task.cancel("first")
    await asyncio.sleep(0)
    assert not task.done()
    task.cancel("second")
    await asyncio.sleep(0)
    assert not task.done()
    store.release.set()
    with pytest.raises(CancelledError, match="first"):
        await task

    # Then
    assert [event.kind for event in store.events] == ["started", "finished"]
    assert quota.history.waits[0].end == "bound"
    assert isinstance(quota.state, QuotaStopped)
    assert not control.dispatch_allowed()


class ProbeStore(WaitStore):
    """Capture actual probe journal events and project returned probe evidence."""

    def __init__(self) -> None:
        super().__init__()
        self.probe_events: list[QuotaProbeLifecycleInput] = []

    @override
    async def record_quota_probe_event(
        self, event: QuotaProbeLifecycleInput, /
    ) -> None:
        """Capture each submitted probe event."""
        self.probe_events.append(event)

    @override
    async def record_quota_probe_settled(
        self, evidence: QuotaProbeEvidence, /
    ) -> QuotaProbeSettled:
        """Produce a safely cleaned process record with the same request."""
        fields = process_fields()
        fields.update(
            request=evidence.request,
            quota_state=evidence.quota_state,
            observation=evidence.observation,
            classification_basis=evidence.classification_basis,
            exit_status=0,
        )
        return QuotaProbeSettled(
            kind="settled", record=QuotaProbeRecord.model_validate(fields)
        )


class AvailableReader(NoQuota):
    """Return one fresh availability observation for the exact request."""

    @property
    @override
    def expected_scope(self) -> QuotaScope | None:
        """The reader binding used by the controlled pause."""
        return observation().scope

    @override
    async def poll(
        self, request: QuotaProbeRequest, stop_dispatch: DispatchStop, /
    ) -> QuotaProbeEvidence:
        """Return controlled availability without launching a process."""
        process = recording(CallHistory(call(), (), ()), 1, "quota").attempt.evidence
        return QuotaProbeEvidence(
            request, process, "available", observation(), "confirmed"
        )


def exhausted_context() -> QuotaWaitContext:
    """Construct a fresh normalized exhausted trigger.

    Returns:
        The trigger context for a drained pause.
    """
    context = waiting().context
    obs = context.quota_observation
    exhausted = obs.model_copy(
        update={"windows": (obs.windows[0].model_copy(update={"state": "exhausted"}),)}
    )
    return context.model_copy(update={"quota_observation": exhausted})


async def test_fresh_probe_resumes_only_after_durable_wait_closure() -> None:
    # Given
    store = ProbeStore()
    control = paused_control()
    quota = QuotaOwner(
        Draining(exhausted_context()),
        QuotaHistory((), ()),
        config(quota_wait_enabled=True),
        control,
        AvailableReader(),
        store,
        Clock(),
        "run",
    )

    # When
    result = await quota.recover()

    # Then
    assert isinstance(result, Open)
    assert control.dispatch_allowed()
    assert [event.kind for event in store.probe_events] == [
        "scheduled",
        "prepared",
        "dispatched",
    ]
    assert len(quota.history.probes) == 1
    assert quota.history.waits[0].end == "quota_available"
    assert store.events[-1].end == "quota_available"


class BlockingReader(AvailableReader):
    """Keep a dispatched probe active until cancellation and controlled cleanup."""

    def __init__(self) -> None:
        self.entered = Event()
        self.cleaning = Event()
        self.release = Event()
        self.request: QuotaProbeRequest | None = None

    @override
    async def poll(
        self, request: QuotaProbeRequest, stop_dispatch: DispatchStop, /
    ) -> QuotaProbeEvidence:
        """Attach exact request evidence after cleanup before cancellation escapes."""
        self.request = request
        self.entered.set()
        try:
            await Event().wait()
        except CancelledError as error:
            self.cleaning.set()
            await self.release.wait()
            process = recording(
                CallHistory(call(), (), ()), 1, "quota"
            ).attempt.evidence
            attach_quota_probe_evidence(
                error, QuotaProbeEvidence(request, process, "unknown", None, None)
            )
            raise
        raise AssertionError("probe unexpectedly completed")


class FailingProbeStore(ProbeStore):
    """Fail dispatch and wait closure while preserving exact submitted events."""

    def __init__(self) -> None:
        super().__init__()
        self.dispatch_error = OSError("dispatch journal")
        self.fail = "finished"

    @override
    async def record_quota_probe_event(
        self, event: QuotaProbeLifecycleInput, /
    ) -> None:
        """Fail only the submitted dispatch event."""
        self.probe_events.append(event)
        if event.kind == "dispatched":
            raise self.dispatch_error


async def test_dispatch_and_closure_failures_survive_cleanup() -> None:
    # Given
    store = FailingProbeStore()
    reader = BlockingReader()
    control = paused_control()
    quota = QuotaOwner(
        Draining(exhausted_context()),
        QuotaHistory((), ()),
        config(quota_wait_enabled=True),
        control,
        reader,
        store,
        Clock(),
        "run",
    )
    task = asyncio.create_task(quota.recover())
    await reader.cleaning.wait()

    # When
    assert not task.done()
    reader.release.set()
    result = await task

    # Then
    assert isinstance(result, QuotaEvidencePending)
    assert result.failures[0].obligation is store.probe_events[-1]
    assert result.failures[0].error is store.dispatch_error
    assert isinstance(result.failures[1].obligation, WaitWrite)
    assert result.failures[1].obligation.event is store.attempted[-1]
    assert result.failures[1].error is store.error
    assert quota.history.probes[0].request is reader.request
    assert not control.dispatch_allowed()


async def test_repeated_owner_cancellation_waits_for_probe_cleanup_and_evidence() -> (
    None
):
    # Given
    store = ProbeStore()
    reader = BlockingReader()
    quota = QuotaOwner(
        Draining(exhausted_context()),
        QuotaHistory((), ()),
        config(quota_wait_enabled=True),
        paused_control(),
        reader,
        store,
        Clock(),
        "run",
    )
    task = asyncio.create_task(quota.recover())
    await reader.entered.wait()

    # When
    task.cancel("first")
    await reader.cleaning.wait()
    task.cancel("second")
    await asyncio.sleep(0)
    assert not task.done()
    reader.release.set()
    with pytest.raises(CancelledError, match="first"):
        await task

    # Then
    assert quota.history.probes[0].request is reader.request
    assert quota.history.waits[0].end == "cancelled"


class ExhaustedReader(AvailableReader):
    """Keep reporting exhaustion for the exact dispatched request."""

    @override
    async def poll(
        self, request: QuotaProbeRequest, stop_dispatch: DispatchStop, /
    ) -> QuotaProbeEvidence:
        """Return a safely settled exhausted observation."""
        process = recording(CallHistory(call(), (), ()), 1, "quota").attempt.evidence
        return QuotaProbeEvidence(
            request,
            process,
            "exhausted",
            exhausted_context().quota_observation,
            "exhausted",
        )


async def test_exhaustion_respects_probe_budget_and_keeps_gate_closed() -> None:
    # Given
    store = ProbeStore()
    control = paused_control()
    quota = QuotaOwner(
        Draining(exhausted_context()),
        QuotaHistory((), ()),
        config(quota_wait_enabled=True, quota_probe_budget=1),
        control,
        ExhaustedReader(),
        store,
        Clock(),
        "run",
    )

    # When
    result = await quota.recover()

    # Then
    assert isinstance(result, QuotaStopped)
    assert len(quota.history.probes) == 1
    assert quota.history.waits[0].end == "bound"
    assert not control.dispatch_allowed()


class BoundClock(Clock):
    """Advance the bound during a retained preparation write."""

    def __init__(self) -> None:
        self.now = 0.0

    @override
    def monotonic(self) -> float:
        """Return controlled elapsed time."""
        return self.now

    @override
    async def sleep(self, seconds: float, /) -> None:
        """Complete the cadence but leave the deadline pending."""
        if seconds > 10.0:
            return
        await Event().wait()


class AdvancingStore(ProbeStore):
    """Spend the entire wait bound before preparation settles."""

    def __init__(self, clock: BoundClock) -> None:
        super().__init__()
        self.clock = clock

    @override
    async def record_quota_probe_event(
        self, event: QuotaProbeLifecycleInput, /
    ) -> None:
        """Advance time when the prepared event becomes durable."""
        self.probe_events.append(event)
        if event.kind == "prepared":
            self.clock.now = 2.0


async def test_bound_crossed_during_preparation_never_invokes_probe() -> None:
    # Given
    clock = BoundClock()
    store = AdvancingStore(clock)
    control = paused_control()
    quota = QuotaOwner(
        Draining(exhausted_context()),
        QuotaHistory((), ()),
        config(quota_wait_enabled=True, quota_wait_limit_seconds=2.0),
        control,
        AvailableReader(),
        store,
        clock,
        "run",
    )

    # When
    result = await quota.recover()

    # Then
    assert isinstance(result, QuotaStopped)
    assert [event.kind for event in store.probe_events] == [
        "scheduled",
        "prepared",
        "not_dispatched",
    ]
    assert quota.history.probes == ()
    assert quota.history.waits[0].end == "bound"
    assert not control.dispatch_allowed()


class MissingEvidenceReader(AvailableReader):
    """Fail without attaching exact-request probe evidence."""

    @override
    async def poll(
        self, request: QuotaProbeRequest, stop_dispatch: DispatchStop, /
    ) -> QuotaProbeEvidence:
        """Expose an unavailable supervisor outcome."""
        raise TimeoutError("probe timeout")


async def test_missing_probe_evidence_stays_pending_after_durable_closure() -> None:
    # Given
    store = ProbeStore()
    control = paused_control()
    quota = QuotaOwner(
        Draining(exhausted_context()),
        QuotaHistory((), ()),
        config(quota_wait_enabled=True),
        control,
        MissingEvidenceReader(),
        store,
        Clock(),
        "run",
    )

    # When
    result = await quota.recover()

    # Then
    assert isinstance(result, ProbeEvidencePending)
    assert result.evidence is None
    assert isinstance(result.error, TimeoutError)
    assert quota.history.waits[0].end == "unknown"
    assert not control.dispatch_allowed()


class TimeoutChainReader(AvailableReader):
    """Expose evidence attached to the cancellation translated into timeout."""

    @override
    async def poll(
        self, request: QuotaProbeRequest, stop_dispatch: DispatchStop, /
    ) -> QuotaProbeEvidence:
        """Raise a timeout whose cause carries the exact probe evidence."""
        cancellation = CancelledError("deadline")
        process = recording(CallHistory(call(), (), ()), 1, "quota").attempt.evidence
        attach_quota_probe_evidence(
            cancellation, QuotaProbeEvidence(request, process, "unknown", None, None)
        )
        raise TimeoutError("quota deadline") from cancellation


async def test_timeout_chain_evidence_is_durable_without_owner_cancellation() -> None:
    # Given
    store = ProbeStore()
    control = paused_control()
    quota = QuotaOwner(
        Draining(exhausted_context()),
        QuotaHistory((), ()),
        config(quota_wait_enabled=True),
        control,
        TimeoutChainReader(),
        store,
        Clock(),
        "run",
    )

    # When
    result = await quota.recover()

    # Then
    assert isinstance(result, QuotaStopped)
    assert len(quota.history.probes) == 1
    assert quota.history.probes[0].quota_state == "unknown"
    assert quota.history.waits[0].end == "stop"
    assert control.reason is not None
    assert control.reason.cancellation is None
    assert not control.dispatch_allowed()


class MismatchedReader(AvailableReader):
    """Return evidence associated with a different request object."""

    @override
    async def poll(
        self, request: QuotaProbeRequest, stop_dispatch: DispatchStop, /
    ) -> QuotaProbeEvidence:
        """Return a value-equal but not identical request."""
        process = recording(CallHistory(call(), (), ()), 1, "quota").attempt.evidence
        return QuotaProbeEvidence(
            request.model_copy(), process, "available", observation(), "wrong"
        )


async def test_mismatched_probe_evidence_cannot_authorize_resumption() -> None:
    # Given
    store = ProbeStore()
    control = paused_control()
    quota = QuotaOwner(
        Draining(exhausted_context()),
        QuotaHistory((), ()),
        config(quota_wait_enabled=True),
        control,
        MismatchedReader(),
        store,
        Clock(),
        "run",
    )

    # When
    result = await quota.recover()

    # Then
    assert isinstance(result, ProbeEvidencePending)
    assert result.evidence is None
    assert quota.history.probes == ()
    assert quota.history.waits[0].end == "unknown"
    assert not control.dispatch_allowed()


async def test_available_probe_does_not_resume_when_wait_closure_fails() -> None:
    # Given
    store = ProbeStore()
    store.fail = "finished"
    control = paused_control()
    quota = QuotaOwner(
        Draining(exhausted_context()),
        QuotaHistory((), ()),
        config(quota_wait_enabled=True),
        control,
        AvailableReader(),
        store,
        Clock(),
        "run",
    )

    # When
    result = await quota.recover()

    # Then
    assert isinstance(result, QuotaEvidencePending)
    assert len(quota.history.probes) == 1
    assert quota.history.waits == ()
    assert result.failures[0].error is store.error
    assert not control.dispatch_allowed()


class BlockingPreparationStore(ProbeStore):
    """Hold preparation and fail it after controlled release."""

    def __init__(self) -> None:
        super().__init__()
        self.preparing = Event()
        self.preparation_release = Event()
        self.preparation_error = OSError("preparation write")

    @override
    async def record_quota_probe_event(
        self, event: QuotaProbeLifecycleInput, /
    ) -> None:
        """Fail the exact submitted preparation after its retained write settles."""
        self.probe_events.append(event)
        if event.kind == "prepared":
            self.preparing.set()
            await self.preparation_release.wait()
            raise self.preparation_error


async def test_cancelled_preparation_failure_remains_cause_after_wait_closure() -> None:
    # Given
    store = BlockingPreparationStore()
    control = paused_control()
    quota = QuotaOwner(
        Draining(exhausted_context()),
        QuotaHistory((), ()),
        config(quota_wait_enabled=True),
        control,
        AvailableReader(),
        store,
        Clock(),
        "run",
    )
    task = asyncio.create_task(quota.recover())
    await store.preparing.wait()

    # When
    task.cancel("first")
    await asyncio.sleep(0)
    task.cancel("second")
    await asyncio.sleep(0)
    assert not task.done()
    store.preparation_release.set()
    with pytest.raises(CancelledError, match="first") as raised:
        await task

    # Then
    assert raised.value.__cause__ is store.preparation_error
    assert isinstance(quota.state, QuotaEvidencePending)
    assert quota.state.failures[0].obligation is store.probe_events[-1]
    assert quota.history.waits[0].end == "cancelled"
    assert not control.dispatch_allowed()


class RecoveringReader(AvailableReader):
    """Return exhaustion once and fresh availability on the next probe."""

    def __init__(self) -> None:
        self.requests: list[QuotaProbeRequest] = []

    @override
    async def poll(
        self, request: QuotaProbeRequest, stop_dispatch: DispatchStop, /
    ) -> QuotaProbeEvidence:
        """Keep each dispatched request distinct and return controlled outcomes."""
        self.requests.append(request)
        process = recording(CallHistory(call(), (), ()), 1, "quota").attempt.evidence
        if len(self.requests) == 1:
            return QuotaProbeEvidence(
                request,
                process,
                "exhausted",
                exhausted_context().quota_observation,
                "exhausted",
            )
        return QuotaProbeEvidence(
            request, process, "available", observation(), "available"
        )


async def test_continued_exhaustion_waits_for_another_separate_probe() -> None:
    # Given
    reader = RecoveringReader()
    store = ProbeStore()
    control = paused_control()
    quota = QuotaOwner(
        Draining(exhausted_context()),
        QuotaHistory((), ()),
        config(quota_wait_enabled=True),
        control,
        reader,
        store,
        Clock(),
        "run",
    )

    # When
    result = await quota.recover()

    # Then
    assert isinstance(result, Open)
    assert len(reader.requests) == 2
    assert reader.requests[0] is not reader.requests[1]
    assert [record.request for record in quota.history.probes] == reader.requests
    assert quota.history.waits[0].end == "quota_available"
    assert control.dispatch_allowed()


def test_reset_hint_selects_latest_exhausted_window() -> None:
    # Given
    obs = exhausted_context().quota_observation
    first = obs.windows[0].model_copy(update={"reset_at_utc": "2026-01-01T00:00:02Z"})
    second = first.model_copy(update={"reset_at_utc": "2026-01-01T00:00:05Z"})
    available = first.model_copy(
        update={"state": "available", "reset_at_utc": "2026-01-01T00:00:08Z"}
    )
    combined = obs.model_copy(update={"windows": (first, second, available)})

    # When
    hint = _reset_hint(combined)

    # Then
    assert hint == "2026-01-01T00:00:05Z"


async def test_gate_stays_closed_until_available_wait_closure_is_durable() -> None:
    # Given
    store = ProbeStore()
    store.block = "finished"
    control = paused_control()
    quota = QuotaOwner(
        Draining(exhausted_context()),
        QuotaHistory((), ()),
        config(quota_wait_enabled=True),
        control,
        AvailableReader(),
        store,
        Clock(),
        "run",
    )
    task = asyncio.create_task(quota.recover())
    await store.entered.wait()

    # When
    closed_before_write = not control.dispatch_allowed()
    store.release.set()
    result = await task

    # Then
    assert closed_before_write
    assert isinstance(result, Open)
    assert control.dispatch_allowed()
    assert quota.history.waits[0].end == "quota_available"


class DeadlineClock(BoundClock):
    """Let the test release the quota deadline during a probe."""

    def __init__(self) -> None:
        super().__init__()
        self.deadline = Event()

    @override
    async def sleep(self, seconds: float, /) -> None:
        """Complete cadence immediately and await an explicit deadline."""
        if seconds > 10.0:
            return
        await self.deadline.wait()


async def test_bound_during_probe_waits_for_cleanup_and_records_exact_evidence() -> (
    None
):
    # Given
    clock = DeadlineClock()
    store = ProbeStore()
    reader = BlockingReader()
    control = paused_control()
    quota = QuotaOwner(
        Draining(exhausted_context()),
        QuotaHistory((), ()),
        config(quota_wait_enabled=True, quota_wait_limit_seconds=2.0),
        control,
        reader,
        store,
        clock,
        "run",
    )
    task = asyncio.create_task(quota.recover())
    await reader.entered.wait()

    # When
    clock.now = 2.0
    clock.deadline.set()
    await reader.cleaning.wait()
    assert not task.done()
    reader.release.set()
    result = await task

    # Then
    assert isinstance(result, QuotaStopped)
    assert quota.history.probes[0].request is reader.request
    assert quota.history.waits[0].end == "bound"
    assert not control.dispatch_allowed()


class BlockingProbeEvidenceStore(ProbeStore):
    """Block and fail the submitted probe evidence write."""

    def __init__(self) -> None:
        super().__init__()
        self.writing_probe = Event()
        self.release_probe = Event()
        self.probe_error = OSError("probe evidence write")
        self.captured: QuotaProbeEvidence | None = None

    @override
    async def record_quota_probe_settled(
        self, evidence: QuotaProbeEvidence, /
    ) -> QuotaProbeSettled:
        """Retain the exact evidence until the controlled failure."""
        self.captured = evidence
        self.writing_probe.set()
        await self.release_probe.wait()
        raise self.probe_error


async def test_cancelled_probe_evidence_failure_is_chained_after_wait_closure() -> None:
    # Given
    store = BlockingProbeEvidenceStore()
    control = paused_control()
    quota = QuotaOwner(
        Draining(exhausted_context()),
        QuotaHistory((), ()),
        config(quota_wait_enabled=True),
        control,
        AvailableReader(),
        store,
        Clock(),
        "run",
    )
    task = asyncio.create_task(quota.recover())
    await store.writing_probe.wait()

    # When
    task.cancel("first")
    await asyncio.sleep(0)
    task.cancel("second")
    await asyncio.sleep(0)
    assert not task.done()
    store.release_probe.set()
    with pytest.raises(CancelledError, match="first") as raised:
        await task

    # Then
    assert raised.value.__cause__ is store.probe_error
    assert isinstance(quota.state, ProbeEvidencePending)
    assert quota.state.evidence is store.captured
    assert quota.history.waits[0].end == "cancelled"
    assert not control.dispatch_allowed()


class TranslatedDeadlineReader(BlockingReader):
    """Translate controlled probe cancellation into a timeout with evidence."""

    @override
    async def poll(
        self, request: QuotaProbeRequest, stop_dispatch: DispatchStop, /
    ) -> QuotaProbeEvidence:
        """Preserve the cancelled probe evidence in the timeout cause."""
        self.request = request
        self.entered.set()
        try:
            await Event().wait()
        except CancelledError as error:
            process = recording(
                CallHistory(call(), (), ()), 1, "quota"
            ).attempt.evidence
            attach_quota_probe_evidence(
                error, QuotaProbeEvidence(request, process, "unknown", None, None)
            )
            raise TimeoutError("translated deadline") from error
        raise AssertionError("probe unexpectedly completed")


async def test_quota_deadline_timeout_preserves_cause_evidence_and_bound_end() -> None:
    # Given
    clock = DeadlineClock()
    store = ProbeStore()
    reader = TranslatedDeadlineReader()
    control = paused_control()
    quota = QuotaOwner(
        Draining(exhausted_context()),
        QuotaHistory((), ()),
        config(quota_wait_enabled=True, quota_wait_limit_seconds=2.0),
        control,
        reader,
        store,
        clock,
        "run",
    )
    task = asyncio.create_task(quota.recover())
    await reader.entered.wait()

    # When
    clock.now = 2.0
    clock.deadline.set()
    result = await task

    # Then
    assert isinstance(result, QuotaStopped)
    assert quota.history.probes[0].request is reader.request
    assert quota.history.waits[0].end == "bound"
    assert control.reason is None
    assert not control.dispatch_allowed()


async def test_shared_stop_cancels_active_probe_and_awaits_its_cleanup() -> None:
    # Given
    store = ProbeStore()
    reader = BlockingReader()
    control = paused_control()
    quota = QuotaOwner(
        Draining(exhausted_context()),
        QuotaHistory((), ()),
        config(quota_wait_enabled=True),
        control,
        reader,
        store,
        Clock(),
        "run",
    )
    task = asyncio.create_task(quota.recover())
    await reader.entered.wait()

    # When
    control.latch_stop(RuntimeError("external stop"))
    await reader.cleaning.wait()
    assert not task.done()
    reader.release.set()
    result = await task

    # Then
    assert isinstance(result, QuotaStopped)
    assert quota.history.probes[0].request is reader.request
    assert quota.history.waits[0].end == "stop"
    assert not control.dispatch_allowed()


class MutableScopeReader(AvailableReader):
    """Allow the binding to become unavailable during a closure write."""

    def __init__(self) -> None:
        self.scope = observation().scope

    @property
    @override
    def expected_scope(self) -> QuotaScope | None:
        """Return the current controlled binding."""
        return self.scope


async def test_scope_loss_during_closure_prevents_resumption() -> None:
    # Given
    store = ProbeStore()
    store.block = "finished"
    reader = MutableScopeReader()
    control = paused_control()
    quota = QuotaOwner(
        Draining(exhausted_context()),
        QuotaHistory((), ()),
        config(quota_wait_enabled=True),
        control,
        reader,
        store,
        Clock(),
        "run",
    )
    task = asyncio.create_task(quota.recover())
    await store.entered.wait()

    # When
    reader.scope = None
    store.release.set()
    result = await task

    # Then
    assert isinstance(result, QuotaStopped)
    assert quota.history.waits[0].end == "quota_available"
    assert not control.dispatch_allowed()


class FinalGateClock(BoundClock):
    """Cross the bound only at the final invocation-time clock sample."""

    def __init__(self) -> None:
        super().__init__()
        self.armed = False
        self.samples = 0

    @override
    def monotonic(self) -> float:
        """Advance after the earlier prepared gate has passed."""
        if self.armed:
            self.samples += 1
            if self.samples >= 4:
                self.now = 2.0
        return self.now


class ArmFinalGateStore(ProbeStore):
    """Start counting time samples once preparation is durable."""

    def __init__(self, clock: FinalGateClock) -> None:
        super().__init__()
        self.clock = clock

    @override
    async def record_quota_probe_event(
        self, event: QuotaProbeLifecycleInput, /
    ) -> None:
        """Arm the final gate clock after the preparation event."""
        self.probe_events.append(event)
        if event.kind == "prepared":
            self.clock.armed = True


async def test_final_invocation_gate_rechecks_bound_after_prepared_gate() -> None:
    # Given
    clock = FinalGateClock()
    store = ArmFinalGateStore(clock)
    control = paused_control()
    quota = QuotaOwner(
        Draining(exhausted_context()),
        QuotaHistory((), ()),
        config(quota_wait_enabled=True, quota_wait_limit_seconds=2.0),
        control,
        AvailableReader(),
        store,
        clock,
        "run",
    )

    # When
    result = await quota.recover()

    # Then
    assert isinstance(result, QuotaStopped)
    assert [event.kind for event in store.probe_events] == [
        "scheduled",
        "prepared",
        "not_dispatched",
    ]
    assert quota.history.probes == ()
    assert quota.history.waits[0].end == "bound"
    assert not control.dispatch_allowed()


class ThreeFailureStore(FailingProbeStore):
    """Also fail the independently required settled-probe write."""

    def __init__(self) -> None:
        super().__init__()
        self.probe_error = OSError("probe evidence")
        self.captured: QuotaProbeEvidence | None = None

    @override
    async def record_quota_probe_settled(
        self, evidence: QuotaProbeEvidence, /
    ) -> QuotaProbeSettled:
        """Keep exact captured evidence while refusing its durable write."""
        self.captured = evidence
        raise self.probe_error


async def test_dispatch_probe_and_closure_failures_preserve_each_obligation() -> None:
    # Given
    store = ThreeFailureStore()
    reader = BlockingReader()
    quota = QuotaOwner(
        Draining(exhausted_context()),
        QuotaHistory((), ()),
        config(quota_wait_enabled=True),
        paused_control(),
        reader,
        store,
        Clock(),
        "run",
    )
    task = asyncio.create_task(quota.recover())
    await reader.cleaning.wait()

    # When
    reader.release.set()
    result = await task

    # Then
    assert isinstance(result, QuotaEvidencePending)
    assert result.failures[0].error is store.dispatch_error
    assert result.failures[1].error is store.error
    assert isinstance(result.probe, ProbeEvidencePending)
    assert result.probe.evidence is store.captured
    assert result.probe.error is store.probe_error
    assert result.probe.request is reader.request
    assert quota.history.probes == ()
    assert quota.history.waits == ()


async def test_durable_probe_is_not_counted_active_during_wait_closure() -> None:
    # Given
    from dataclasses import replace

    from script.eval.runner.coordinator.progress import project
    from test.script.unit.eval.test_coordinator_progress import view

    store = ProbeStore()
    store.block = "finished"
    quota = QuotaOwner(
        Draining(exhausted_context()),
        QuotaHistory((), ()),
        config(quota_wait_enabled=True),
        paused_control(),
        AvailableReader(),
        store,
        Clock(),
        "run",
    )
    task = asyncio.create_task(quota.recover())
    await store.entered.wait()

    # When
    counts = project(replace(view(), quota=quota.state, probes=quota.history)).counts
    store.release.set()
    await task

    # Then
    assert counts.probes_started == 1
    assert counts.probes_active == 0


class LeafCancelledReader(AvailableReader):
    """Raise a leaf cancellation with evidence for the exact request."""

    def __init__(self) -> None:
        self.error = CancelledError("probe leaf")

    @override
    async def poll(
        self, request: QuotaProbeRequest, stop_dispatch: DispatchStop, /
    ) -> QuotaProbeEvidence:
        """Attach evidence before propagating the original leaf cancellation."""
        process = recording(CallHistory(call(), (), ()), 1, "quota").attempt.evidence
        attach_quota_probe_evidence(
            self.error, QuotaProbeEvidence(request, process, "unknown", None, None)
        )
        raise self.error


async def test_probe_leaf_cancellation_remains_primary_after_durable_evidence() -> None:
    # Given
    store = ProbeStore()
    reader = LeafCancelledReader()
    control = paused_control()
    quota = QuotaOwner(
        Draining(exhausted_context()),
        QuotaHistory((), ()),
        config(quota_wait_enabled=True),
        control,
        reader,
        store,
        Clock(),
        "run",
    )

    # When
    with pytest.raises(CancelledError) as raised:
        await quota.recover()

    # Then
    assert raised.value is reader.error
    assert reader.error.__cause__ is None
    assert quota.history.waits[0].end == "cancelled"
    assert len(quota.history.probes) == 1
    assert control.reason is not None
    assert control.reason.cancellation_origin == "leaf"


async def test_another_owners_cancellation_during_probe_is_not_propagated() -> None:
    # Given
    store = ProbeStore()
    reader = BlockingReader()
    control = paused_control()
    quota = QuotaOwner(
        Draining(exhausted_context()),
        QuotaHistory((), ()),
        config(quota_wait_enabled=True),
        control,
        reader,
        store,
        Clock(),
        "run",
    )
    task = asyncio.create_task(quota.recover())
    await reader.entered.wait()

    # When
    other = CancelledError("another owner")
    control.note_cancellation(other, "leaf")
    await reader.cleaning.wait()
    reader.release.set()
    result = await task

    # Then
    assert isinstance(result, QuotaStopped)
    assert quota.history.waits[0].end == "cancelled"
    assert control.reason is not None
    assert control.reason.cancellation is other
