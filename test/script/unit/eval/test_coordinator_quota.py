# SPDX-License-Identifier: Apache-2.0
"""Quota-owner bounded wait wiring through controlled evidence effects."""

import asyncio
from asyncio import CancelledError, Event
from typing import override

import pytest

from script.eval.model import WaitEvent
from script.eval.runner.coordinator.control import RunControl
from script.eval.runner.coordinator.quota import QuotaOwner
from script.eval.runner.coordinator.quota_states import (
    Draining,
    QuotaEvidencePending,
    QuotaHistory,
    QuotaStopped,
)
from script.eval.runner.coordinator.state import WaitWrite
from test.script.unit.eval.test_coordinator_calls import Clock, NoQuota, Store
from test.script.unit.eval.test_coordinator_states import config, waiting


class WaitStore(Store):
    """Capture wait writes and optionally fail or block a selected event."""

    def __init__(self) -> None:
        super().__init__()
        self.entered = Event()
        self.release = Event()
        self.block: str | None = None
        self.fail: str | None = None
        self.error = OSError("wait write failed")

    @override
    async def record_wait_event(self, event: WaitEvent, /) -> None:
        """Record the exact event unless its controlled write fails."""
        if event.kind == self.block:
            self.entered.set()
            await self.release.wait()
        if event.kind == self.fail:
            raise self.error
        self.events.append(event)


def owner(store: WaitStore, control: RunControl | None = None) -> QuotaOwner:
    """Build a probe-disabled owner with real validated values.

    Returns:
        The owner under test.
    """
    return QuotaOwner(
        Draining(waiting().context),
        QuotaHistory((), ()),
        config(quota_wait_enabled=True, quota_probe_budget=0),
        control or RunControl(),
        NoQuota(),
        store,
        Clock(),
        "run",
    )


async def test_zero_probe_budget_closes_a_durable_wait() -> None:
    # Given
    store = WaitStore()
    quota = owner(store)

    # When
    result = await quota.recover()

    # Then
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
    control = RunControl()
    quota = owner(store, control)

    # When
    result = await quota.recover()

    # Then
    assert isinstance(result, QuotaEvidencePending)
    assert isinstance(result.obligation, WaitWrite)
    assert result.obligation.record is not None
    assert result.obligation.event.wait_id == store.events[0].wait_id
    assert result.error is store.error
    assert quota.history.waits == ()
    assert control.reason is not None
    assert control.reason.recording_failure is store.error


async def test_cancellation_during_start_still_closes_the_wait() -> None:
    # Given
    store = WaitStore()
    store.block = "started"
    quota = owner(store)
    task = asyncio.create_task(quota.recover())
    await store.entered.wait()

    # When
    task.cancel("first")
    task.cancel("second")
    store.release.set()
    with pytest.raises(CancelledError, match="first"):
        await task

    # Then
    assert [event.kind for event in store.events] == ["started", "finished"]
    assert store.events[1].end == "cancelled"
    assert quota.history.waits[0].end == "cancelled"
    assert isinstance(quota.state, QuotaStopped)


async def test_probe_capable_path_stops_at_the_pending_seam() -> None:
    # Given
    store = WaitStore()
    quota = QuotaOwner(
        Draining(waiting().context),
        QuotaHistory((), ()),
        config(quota_wait_enabled=True),
        RunControl(),
        NoQuota(),
        store,
        Clock(),
        "run",
    )

    # When
    with pytest.raises(NotImplementedError, match="probe lifecycle"):
        await quota.recover()

    # Then
    assert store.events == []
    assert isinstance(quota.state, Draining)


async def test_failed_start_retains_its_event_without_claiming_a_wait() -> None:
    # Given
    store = WaitStore()
    store.fail = "started"
    quota = owner(store)

    # When
    result = await quota.recover()

    # Then
    assert isinstance(result, QuotaEvidencePending)
    assert isinstance(result.obligation, WaitWrite)
    assert result.obligation.event.kind == "started"
    assert result.obligation.record is None
    assert result.error is store.error
    assert quota.history.waits == ()


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
    control = RunControl()
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
    quota = QuotaOwner(
        Draining(context),
        QuotaHistory((), ()),
        config(quota_wait_enabled=True, quota_wait_limit_seconds=1.0),
        RunControl(),
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
