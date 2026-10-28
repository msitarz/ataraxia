# SPDX-License-Identifier: Apache-2.0
"""Retain submitted tasks and preserve cancellation with their outcome."""

from asyncio import CancelledError, Task
from collections.abc import Callable, Coroutine
from dataclasses import dataclass


@dataclass(frozen=True)
class SettledValue[T]:
    """Successful task value and any concurrent owner cancellation."""

    value: T
    cancellation: CancelledError | None


@dataclass(frozen=True)
class SettledFailure:
    """Task failure and any concurrent owner cancellation, both preserved."""

    error: BaseException
    cancellation: CancelledError | None


type Settlement[T] = SettledValue[T] | SettledFailure


async def settle[T](task: Task[T], /) -> Settlement[T]:
    """Retain a submitted task through repeated owner cancellation.

    A cancelling owner remains primary; the caller attaches any task failure as
    its cause and closes a successfully started wait before propagating it.

    The retained-task loop is not implemented yet.

    Returns:
        The task value or failure and any owner cancellation.
    """
    return await _settle(task, _retain_task)


async def _settle[T](
    task: Task[T],
    retain: Callable[[Task[T]], Coroutine[None, None, CancelledError | None]],
    /,
) -> Settlement[T]:
    """Build the outcome after the retained task settles.

    Returns:
        The task value or failure and any owner cancellation.
    """
    cancellation: CancelledError | None = await retain(task)
    try:
        value: T = task.result()
    except BaseException as error:
        return SettledFailure(error=error, cancellation=cancellation)
    return SettledValue(value=value, cancellation=cancellation)


async def _retain_task[T](task: Task[T], /) -> CancelledError | None:
    """Wait for the task through owner cancellation; implementation pending."""
    raise NotImplementedError("retained-task loop is not implemented")
