# SPDX-License-Identifier: Apache-2.0
"""Control wiring with injected leaves; actual notifications and waits are pending."""

import asyncio
from asyncio import CancelledError
from collections.abc import Callable

import pytest

from script.eval.runner.coordinator.control import RunControl
from script.eval.runner.coordinator.quota_states import PauseOrigin, PauseTrigger
from test.script.unit.eval.test_coordinator_states import call, observation


def _origin(number: int) -> PauseOrigin:
    """Build a pause origin with a real frozen request identity."""
    return PauseOrigin(call(), number)


def test_supervisor_stop_precedes_notification_and_retains_cancellation() -> None:
    # Given
    observed: list[bool] = []
    control = RunControl(_notify=lambda: observed.append(control.dispatch_allowed()))
    first = RuntimeError("unsafe cleanup")
    cancellation = CancelledError("leaf")
    failure = RuntimeError("write")

    # When
    control.supervisor_stop(first)
    control.note_cancellation(cancellation, "leaf")
    control.note_cancellation(CancelledError("later"), "owner")
    control.note_recording_failure(failure)

    # Then
    assert observed == [False]
    assert control.reason is not None
    assert control.reason.first is first
    assert control.reason.cancellation is cancellation
    assert control.reason.cancellation_origin == "leaf"
    assert control.reason.recording_failure is failure


def test_pause_first_origin_and_durable_trigger_ownership() -> None:
    # Given
    observed: list[bool] = []
    control = RunControl(_notify=lambda: observed.append(control.dispatch_allowed()))
    first, later = _origin(1), _origin(2)
    trigger = PauseTrigger(first, observation())

    # When
    control.pause_for_quota(first)
    control.pause_for_quota(later)
    with pytest.raises(ValueError, match="current pause"):
        control.publish_quota_trigger(PauseTrigger(later, trigger.observation))
    control.publish_quota_trigger(trigger)

    # Then
    assert observed == [False]
    assert control.quota_origin is first
    assert control.quota_trigger is trigger

    # When
    control.resume_after_quota()

    # Then
    assert control.quota_origin is None
    assert control.quota_trigger is None
    assert control.dispatch_allowed()


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
    control = RunControl(_notify=lambda: None)

    # When
    if paused:
        control.pause_for_quota(_origin(1))
    if stopped:
        control.latch_stop(RuntimeError("stop"))

    # Then
    assert control.dispatch_allowed() is dispatch
    assert control._pause_or_stop() is pause_ready
    assert control._dispatch_or_stop() is dispatch_ready


async def test_dispatch_wait_rechecks_stop_after_injected_wait() -> None:
    # Given
    async def stop_during_wait(ready: Callable[[], bool]) -> None:
        """Simulate a stop while the dispatch waiter is suspended."""
        await asyncio.sleep(0)
        assert not ready()
        control.latch_stop(RuntimeError("stop"))
        assert ready()

    control = RunControl(_notify=lambda: None, _wait=stop_during_wait)
    control.pause_for_quota(_origin(1))

    # When
    result = await control.wait_dispatchable()

    # Then
    assert not result


async def test_dispatch_rechecks_pause_after_wait() -> None:
    # Given
    async def pause_during_wait(ready: Callable[[], bool]) -> None:
        """Simulate a pause before the awaiting caller resumes."""
        await asyncio.sleep(0)
        assert ready()
        control.pause_for_quota(_origin(1))

    control = RunControl(_notify=lambda: None, _wait=pause_during_wait)

    # When
    result = await control.wait_dispatchable()

    # Then
    assert not result


async def test_default_wait_is_explicitly_pending() -> None:
    # Given
    control = RunControl()

    # When
    with pytest.raises(NotImplementedError) as error:
        await control.wait_dispatchable()

    # Then
    assert str(error.value) == "control waiting is pending"


def test_default_notification_is_pending_after_stop_latches() -> None:
    # Given
    control = RunControl()
    reason = RuntimeError("stop")

    # When
    with pytest.raises(NotImplementedError, match="notification is pending"):
        control.latch_stop(reason)

    # Then
    assert not control.dispatch_allowed()
    assert control.reason is not None
    assert control.reason.first is reason


async def test_pause_wait_predicate_wakes_for_stop_without_pause() -> None:
    # Given
    async def stop_during_wait(ready: Callable[[], bool]) -> None:
        """Simulate a stop while the pause waiter is suspended."""
        await asyncio.sleep(0)
        assert not ready()
        control.latch_stop(RuntimeError("stop"))
        assert ready()

    control = RunControl(_notify=lambda: None, _wait=stop_during_wait)

    # When
    result = await control.wait_for_quota_pause()

    # Then
    assert result is None


async def test_pause_wait_rechecks_stop_after_pause_is_ready() -> None:
    # Given
    async def stop_during_wait(ready: Callable[[], bool]) -> None:
        """Simulate stop winning before a ready pause is returned."""
        await asyncio.sleep(0)
        assert ready()
        control.latch_stop(RuntimeError("stop"))

    control = RunControl(_notify=lambda: None, _wait=stop_during_wait)
    control.pause_for_quota(_origin(1))

    # When
    result = await control.wait_for_quota_pause()

    # Then
    assert result is None


def test_default_notification_is_pending_after_pause_latches() -> None:
    # Given
    control = RunControl()
    origin = _origin(1)

    # When
    with pytest.raises(NotImplementedError, match="notification is pending"):
        control.pause_for_quota(origin)

    # Then
    assert not control.dispatch_allowed()
    assert control.quota_origin is origin
