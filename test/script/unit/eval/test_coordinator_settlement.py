# SPDX-License-Identifier: Apache-2.0
"""Settlement outcome wiring and pending retained-task lifecycle."""

import asyncio
from asyncio import CancelledError, Task

import pytest

from script.eval.runner.coordinator.settlement import (
    SettledFailure,
    SettledValue,
    _settle,
    settle,
)


@pytest.mark.parametrize(
    "cancelled", [False, True], ids=["no-cancellation", "cancelled"]
)
async def test_settlement_preserves_task_value_and_owner_cancellation(
    cancelled: bool,
) -> None:
    # Given
    ready = asyncio.Event()
    ready.set()

    async def produce() -> int:
        await ready.wait()
        return 42

    task: Task[int] = asyncio.create_task(produce())
    cancellation = CancelledError("owner") if cancelled else None

    async def retain(submitted: Task[int]) -> CancelledError | None:
        assert submitted is task
        await asyncio.wait({submitted})
        return cancellation

    # When
    result = await _settle(task, retain)

    # Then
    assert isinstance(result, SettledValue)
    assert result.value == 42
    assert result.cancellation is cancellation


@pytest.mark.parametrize(
    "cancelled", [False, True], ids=["no-cancellation", "cancelled"]
)
async def test_settlement_preserves_task_failure_and_owner_cancellation(
    cancelled: bool,
) -> None:
    # Given
    failure = ValueError("write failed")
    ready = asyncio.Event()
    ready.set()

    async def fail() -> int:
        await ready.wait()
        raise failure

    task: Task[int] = asyncio.create_task(fail())
    cancellation = CancelledError("owner") if cancelled else None

    async def retain(submitted: Task[int]) -> CancelledError | None:
        assert submitted is task
        await asyncio.wait({submitted})
        return cancellation

    # When
    result = await _settle(task, retain)

    # Then
    assert isinstance(result, SettledFailure)
    assert result.error is failure
    assert result.cancellation is cancellation


@pytest.mark.parametrize(
    "cancelled", [False, True], ids=["no-owner-cancellation", "owner-cancelled"]
)
async def test_settlement_preserves_leaf_cancellation_separately(
    cancelled: bool,
) -> None:
    # Given
    async def cancel_self() -> int:
        current = asyncio.current_task()
        assert current is not None
        current.cancel("leaf")
        await asyncio.Event().wait()
        raise AssertionError("self-cancellation was not delivered")

    task: Task[int] = asyncio.create_task(cancel_self())
    cancellation = CancelledError("owner") if cancelled else None

    async def retain(submitted: Task[int]) -> CancelledError | None:
        assert submitted is task
        await asyncio.wait({submitted})
        return cancellation

    # When
    result = await _settle(task, retain)

    # Then
    assert isinstance(result, SettledFailure)
    assert isinstance(result.error, CancelledError)
    assert result.error.args == ("leaf",)
    assert result.error is not cancellation
    assert result.cancellation is cancellation


async def test_public_settlement_exposes_pending_retained_task_loop() -> None:
    # Given
    ready = asyncio.Event()
    ready.set()

    async def produce() -> int:
        await ready.wait()
        return 42

    task: Task[int] = asyncio.create_task(produce())
    await asyncio.wait({task})

    # When / Then
    with pytest.raises(NotImplementedError, match="retained-task loop"):
        await settle(task)


@pytest.mark.skip(reason="retained-task loop is not implemented")
async def test_repeated_owner_cancellation_waits_for_successful_task() -> None:
    """A retained task completes before its value and cancellation are returned."""


@pytest.mark.skip(reason="retained-task loop is not implemented")
async def test_repeated_owner_cancellation_preserves_task_failure() -> None:
    """A retained task's failure and owner cancellation both survive settlement."""


@pytest.mark.skip(reason="retained-task loop is not implemented")
async def test_task_cancellation_is_separate_from_owner_cancellation() -> None:
    """A cancelled submitted task is a failure distinct from owner cancellation."""
