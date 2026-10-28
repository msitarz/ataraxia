# SPDX-License-Identifier: Apache-2.0
"""Control wiring with injected notification and waiting leaves."""

import asyncio
from asyncio import CancelledError
from collections.abc import Callable
from typing import cast

import pytest

from script.eval.model import QuotaObservation
from script.eval.runner.coordinator.control import RunControl
from script.eval.runner.coordinator.quota_states import PauseOrigin, PauseTrigger
from script.eval.runner.ports import EffectiveCall


def _origin(number: int) -> PauseOrigin:
    return PauseOrigin(cast(EffectiveCall, object()), number)


def test_supervisor_stop_precedes_notification_and_retains_cancellation() -> None:
    observed: list[bool] = []
    control = RunControl(_notify=lambda: observed.append(control.dispatch_allowed()))
    first = RuntimeError("unsafe cleanup")
    cancellation = CancelledError("leaf")
    failure = RuntimeError("write")

    control.supervisor_stop(first)
    control.note_cancellation(cancellation, "leaf")
    control.note_cancellation(CancelledError("later"), "owner")
    control.note_recording_failure(failure)

    assert observed == [False]
    assert control.reason is not None
    assert control.reason.first is first
    assert control.reason.cancellation is cancellation
    assert control.reason.cancellation_origin == "leaf"
    assert control.reason.recording_failure is failure


def test_pause_first_origin_and_durable_trigger_ownership() -> None:
    observed: list[bool] = []
    control = RunControl(_notify=lambda: observed.append(control.dispatch_allowed()))
    first, later = _origin(1), _origin(2)
    trigger = PauseTrigger(first, cast(QuotaObservation, object()))
    control.pause_for_quota(first)
    control.pause_for_quota(later)
    with pytest.raises(ValueError, match="current pause"):
        control.publish_quota_trigger(PauseTrigger(later, trigger.observation))
    control.publish_quota_trigger(trigger)

    assert observed == [False]
    assert control.quota_origin is first
    assert control.quota_trigger is trigger
    control.resume_after_quota()
    assert control.quota_origin is None
    assert control.quota_trigger is None
    assert control.dispatch_allowed()


async def test_waits_recheck_stop_after_injected_wait() -> None:
    control = RunControl(_notify=lambda: None)
    control.pause_for_quota(_origin(1))

    async def stop_during_wait(ready: Callable[[], bool]) -> None:
        await asyncio.sleep(0)
        assert not ready()
        control.latch_stop(RuntimeError("stop"))
        assert ready()

    control._wait = stop_during_wait
    assert not await control.wait_dispatchable()

    async def already_ready(ready: Callable[[], bool]) -> None:
        await asyncio.sleep(0)
        assert ready()

    control._wait = already_ready
    assert await control.wait_for_quota_pause() is None


async def test_dispatch_rechecks_pause_after_wait() -> None:
    control = RunControl(_notify=lambda: None)

    async def pause_during_wait(ready: Callable[[], bool]) -> None:
        await asyncio.sleep(0)
        assert ready()
        control.pause_for_quota(_origin(1))

    control._wait = pause_during_wait
    assert not await control.wait_dispatchable()


async def test_default_wait_is_explicitly_pending() -> None:
    control = RunControl()
    with pytest.raises(NotImplementedError, match="waiting is pending"):
        await control.wait_dispatchable()


async def test_pause_wait_predicate_wakes_for_stop_without_pause() -> None:
    control = RunControl(_notify=lambda: None)

    async def stop_during_wait(ready: Callable[[], bool]) -> None:
        await asyncio.sleep(0)
        assert not ready()
        control.latch_stop(RuntimeError("stop"))
        assert ready()

    control._wait = stop_during_wait
    assert await control.wait_for_quota_pause() is None
