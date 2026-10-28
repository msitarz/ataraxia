# SPDX-License-Identifier: Apache-2.0
"""Shared stop and quota gate behavior through real asyncio waiters."""

import asyncio
from asyncio import CancelledError

import pytest

from script.eval.runner.coordinator.control import RunControl
from script.eval.runner.coordinator.quota_states import PauseOrigin, PauseTrigger
from test.script.unit.eval.test_coordinator_states import call, observation


def _origin(number: int) -> PauseOrigin:
    """Build a pause origin with a real frozen request identity."""
    return PauseOrigin(call(), number)


def test_supervisor_stop_and_cancellation_provenance() -> None:
    # Given
    control = RunControl()
    first = RuntimeError("unsafe cleanup")
    cancellation = CancelledError("leaf")
    failure = RuntimeError("write")

    # When
    control.supervisor_stop(first)
    control.note_cancellation(cancellation, "leaf")
    control.note_cancellation(CancelledError("later"), "owner")
    control.note_recording_failure(failure)
    control.note_recording_failure(RuntimeError("later write"))

    # Then
    assert not control.dispatch_allowed()
    assert control.reason is not None
    assert control.reason.first is first
    assert control.reason.cancellation is cancellation
    assert control.reason.cancellation_origin == "leaf"
    assert control.reason.recording_failure is failure


def test_first_cancellation_latches_stop() -> None:
    # Given
    control = RunControl()
    cancellation = CancelledError("owner")

    # When
    control.note_cancellation(cancellation, "owner")

    # Then
    assert control.reason is not None
    assert control.reason.first is cancellation
    assert control.reason.cancellation is cancellation
    assert control.reason.cancellation_origin == "owner"
    assert not control.dispatch_allowed()


def test_pause_lifecycle_retains_first_origin_and_current_trigger() -> None:
    # Given
    control = RunControl()
    first, later = _origin(1), _origin(2)
    trigger = PauseTrigger(first, observation())

    # When
    control.pause_for_quota(first)
    control.pause_for_quota(later)
    with pytest.raises(ValueError, match="current pause"):
        control.publish_quota_trigger(PauseTrigger(later, trigger.observation))
    control.publish_quota_trigger(trigger)

    # Then
    assert not control.dispatch_allowed()
    assert control.quota_origin is first
    assert control.quota_trigger is trigger

    # When
    control.resume_after_quota()
    control.pause_for_quota(later)

    # Then
    assert control.quota_origin is later
    assert control.quota_trigger is None
    with pytest.raises(ValueError, match="current pause"):
        control.publish_quota_trigger(trigger)


@pytest.mark.parametrize(
    ("paused", "stopped", "dispatch", "pause_ready", "dispatch_ready"),
    [
        (False, False, True, False, True),
        (True, False, False, True, False),
        (False, True, False, True, True),
        (True, True, False, True, True),
    ],
)
def test_gate_predicates(
    paused: bool, stopped: bool, dispatch: bool, pause_ready: bool, dispatch_ready: bool
) -> None:
    # Given
    control = RunControl()

    # When
    if paused:
        control.pause_for_quota(_origin(1))
    if stopped:
        control.latch_stop(RuntimeError("stop"))

    # Then
    assert control.dispatch_allowed() is dispatch
    assert control._pause_or_stop() is pause_ready
    assert control._dispatch_or_stop() is dispatch_ready


async def test_initial_dispatch_is_ready_and_pause_wakes_waiter() -> None:
    # Given
    control = RunControl()
    origin = _origin(1)
    pause = asyncio.create_task(control.wait_for_quota_pause())
    await asyncio.sleep(0)
    assert not pause.done()

    # When
    dispatch = await control.wait_dispatchable()
    control.pause_for_quota(origin)

    # Then
    assert dispatch
    assert not control.dispatch_allowed()
    assert await asyncio.wait_for(pause, 1) is origin


async def test_resume_wakes_all_dispatch_waiters() -> None:
    # Given
    control = RunControl()
    control.pause_for_quota(_origin(1))
    waiters = [asyncio.create_task(control.wait_dispatchable()) for _ in range(3)]
    await asyncio.sleep(0)
    assert all(not waiter.done() for waiter in waiters)

    # When
    control.resume_after_quota()

    # Then
    assert await asyncio.wait_for(asyncio.gather(*waiters), 1) == [True, True, True]


async def test_stop_wakes_dispatch_waiter_and_resume_cannot_reopen() -> None:
    # Given
    control = RunControl()
    control.pause_for_quota(_origin(1))
    dispatch_waiter = asyncio.create_task(control.wait_dispatchable())
    await asyncio.sleep(0)

    # When
    control.latch_stop(RuntimeError("stop"))
    control.resume_after_quota()

    # Then
    assert not await asyncio.wait_for(dispatch_waiter, 1)
    assert not control.dispatch_allowed()


async def test_stop_wakes_pause_waiter_without_pause() -> None:
    # Given
    control = RunControl()
    waiter = asyncio.create_task(control.wait_for_quota_pause())
    await asyncio.sleep(0)
    assert not waiter.done()

    # When
    control.supervisor_stop(RuntimeError("stop"))

    # Then
    assert await asyncio.wait_for(waiter, 1) is None


async def test_cancelled_waiter_does_not_affect_other_waiters() -> None:
    # Given
    control = RunControl()
    control.pause_for_quota(_origin(1))
    cancelled = asyncio.create_task(control.wait_dispatchable())
    survivor = asyncio.create_task(control.wait_dispatchable())
    await asyncio.sleep(0)

    # When
    cancelled.cancel()
    with pytest.raises(CancelledError):
        await cancelled
    control.resume_after_quota()

    # Then
    assert await asyncio.wait_for(survivor, 1)
    assert control.reason is None


async def test_rapid_resume_and_pause_rechecks_before_dispatch() -> None:
    # Given
    control = RunControl()
    control.pause_for_quota(_origin(1))
    waiter = asyncio.create_task(control.wait_dispatchable())
    await asyncio.sleep(0)

    # When
    control.resume_after_quota()
    control.pause_for_quota(_origin(2))
    await asyncio.sleep(0)

    # Then
    assert not waiter.done()
    assert not control.dispatch_allowed()

    # When
    control.resume_after_quota()

    # Then
    assert await asyncio.wait_for(waiter, 1)


async def test_rapid_pause_and_resume_rechecks_pause_waiter() -> None:
    # Given
    control = RunControl()
    waiter = asyncio.create_task(control.wait_for_quota_pause())
    await asyncio.sleep(0)

    # When
    control.pause_for_quota(_origin(1))
    control.resume_after_quota()
    await asyncio.sleep(0)

    # Then
    assert not waiter.done()

    # When
    current = _origin(2)
    control.pause_for_quota(current)

    # Then
    assert await asyncio.wait_for(waiter, 1) is current


async def test_stop_wins_after_resume_before_dispatch_waiter_runs() -> None:
    # Given
    control = RunControl()
    control.pause_for_quota(_origin(1))
    waiter = asyncio.create_task(control.wait_dispatchable())
    await asyncio.sleep(0)

    # When
    control.resume_after_quota()
    control.latch_stop(RuntimeError("stop"))

    # Then
    assert not await asyncio.wait_for(waiter, 1)


async def test_stop_wins_after_pause_before_pause_waiter_runs() -> None:
    # Given
    control = RunControl()
    waiter = asyncio.create_task(control.wait_for_quota_pause())
    await asyncio.sleep(0)

    # When
    control.pause_for_quota(_origin(1))
    control.latch_stop(RuntimeError("stop"))

    # Then
    assert await asyncio.wait_for(waiter, 1) is None
