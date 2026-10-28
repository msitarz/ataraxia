# SPDX-License-Identifier: Apache-2.0
"""Retained task settlement through owner and leaf cancellation."""

import asyncio
from asyncio import CancelledError
from collections.abc import Coroutine

from script.eval.runner.coordinator.settlement import (
    SettledFailure,
    SettledValue,
    Settlement,
    settle,
)


async def _checkpoint() -> None:
    """Let callbacks already queued by cancellation run before continuing."""
    reached = asyncio.Event()
    asyncio.get_running_loop().call_soon(reached.set)
    await reached.wait()


async def _cancel_owner_twice[T](
    operation: Coroutine[None, None, T], ready: asyncio.Event
) -> tuple[Settlement[T], list[tuple[bool, bool]]]:
    """Cancel an owner twice and record whether either task has ended."""
    submitted = asyncio.create_task(operation)
    owner = asyncio.create_task(settle(submitted))
    await _checkpoint()
    owner.cancel("first")
    await _checkpoint()
    states = [(owner.done(), submitted.cancelled())]
    owner.cancel("second")
    await _checkpoint()
    states.append((owner.done(), submitted.cancelled()))
    ready.set()
    return await owner, states


async def test_repeated_owner_cancellation_waits_for_successful_task() -> None:
    # Given
    release = asyncio.Event()

    async def produce() -> int:
        await release.wait()
        return 42

    ready = asyncio.Event()
    owner = asyncio.create_task(_cancel_owner_twice(produce(), ready))
    await ready.wait()

    # When
    release.set()
    result, states = await owner

    # Then
    assert states == [(False, False), (False, False)]
    assert isinstance(result, SettledValue)
    assert result.value == 42
    assert result.cancellation is not None
    assert result.cancellation.args == ("first",)


async def test_repeated_owner_cancellation_preserves_task_failure() -> None:
    # Given
    release = asyncio.Event()
    failure = ValueError("write failed")

    async def fail() -> int:
        await release.wait()
        raise failure

    ready = asyncio.Event()
    owner = asyncio.create_task(_cancel_owner_twice(fail(), ready))
    await ready.wait()

    # When
    release.set()
    result, states = await owner

    # Then
    assert states == [(False, False), (False, False)]
    assert isinstance(result, SettledFailure)
    assert result.error is failure
    assert result.cancellation is not None
    assert result.cancellation.args == ("first",)


async def test_leaf_cancellation_is_separate_from_owner_cancellation() -> None:
    # Given
    release = asyncio.Event()

    async def cancel_self() -> int:
        await release.wait()
        current = asyncio.current_task()
        assert current is not None
        current.cancel("leaf")
        await asyncio.Event().wait()
        raise AssertionError("self-cancellation was not delivered")

    ready = asyncio.Event()
    owner = asyncio.create_task(_cancel_owner_twice(cancel_self(), ready))
    await ready.wait()

    # When
    release.set()
    result, states = await owner

    # Then
    assert states == [(False, False), (False, False)]
    assert isinstance(result, SettledFailure)
    assert isinstance(result.error, CancelledError)
    assert result.error.args == ("leaf",)
    assert result.cancellation is not None
    assert result.cancellation.args == ("first",)
    assert result.error is not result.cancellation


async def test_pending_task_completes_without_owner_cancellation() -> None:
    # Given
    release = asyncio.Event()

    async def produce() -> int:
        await release.wait()
        return 42

    task = asyncio.create_task(produce())
    owner = asyncio.create_task(settle(task))
    await _checkpoint()

    # When
    release.set()
    result = await owner

    # Then
    assert result == SettledValue(value=42, cancellation=None)


async def test_pending_leaf_cancellation_is_not_owner_cancellation() -> None:
    # Given
    release = asyncio.Event()

    async def cancel_self() -> int:
        await release.wait()
        raise CancelledError("leaf")

    task = asyncio.create_task(cancel_self())
    owner = asyncio.create_task(settle(task))
    await _checkpoint()

    # When
    release.set()
    result = await owner

    # Then
    assert isinstance(result, SettledFailure)
    assert isinstance(result.error, CancelledError)
    assert result.error.args == ("leaf",)
    assert result.cancellation is None


async def test_already_settled_value_is_preserved() -> None:
    # Given
    async def produce() -> int:
        await _checkpoint()
        return 42

    task = asyncio.create_task(produce())
    await asyncio.wait({task})

    # When
    result = await settle(task)

    # Then
    assert result == SettledValue(value=42, cancellation=None)


async def test_already_settled_failure_is_preserved() -> None:
    # Given
    failure = ValueError("write failed")

    async def fail() -> int:
        await _checkpoint()
        raise failure

    task = asyncio.create_task(fail())
    await asyncio.wait({task})

    # When
    result = await settle(task)

    # Then
    assert result == SettledFailure(error=failure, cancellation=None)


async def test_already_cancelled_task_is_a_leaf_failure() -> None:
    # Given
    async def cancel_self() -> int:
        await _checkpoint()
        raise CancelledError("leaf")

    task = asyncio.create_task(cancel_self())
    await asyncio.wait({task})

    # When
    result = await settle(task)

    # Then
    assert isinstance(result, SettledFailure)
    assert isinstance(result.error, CancelledError)
    assert result.error.args == ("leaf",)
    assert result.cancellation is None


async def test_same_turn_completion_and_owner_cancellation_preserve_both() -> None:
    # Given
    release = asyncio.Event()

    async def produce() -> int:
        await release.wait()
        return 42

    task = asyncio.create_task(produce())
    owner = asyncio.create_task(settle(task))
    await _checkpoint()

    # When
    release.set()
    owner.cancel("owner")
    result = await owner

    # Then
    assert isinstance(result, SettledValue)
    assert result.value == 42
    assert result.cancellation is not None
    assert result.cancellation.args == ("owner",)


async def test_same_turn_failure_and_owner_cancellation_preserve_both() -> None:
    # Given
    release = asyncio.Event()
    failure = ValueError("write failed")

    async def fail() -> int:
        await release.wait()
        raise failure

    task = asyncio.create_task(fail())
    owner = asyncio.create_task(settle(task))
    await _checkpoint()

    # When
    release.set()
    owner.cancel("owner")
    result = await owner

    # Then
    assert isinstance(result, SettledFailure)
    assert result.error is failure
    assert result.cancellation is not None
    assert result.cancellation.args == ("owner",)
