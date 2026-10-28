# SPDX-License-Identifier: Apache-2.0
"""Retain submitted tasks and preserve cancellation with their outcome."""

import asyncio
from asyncio import CancelledError, Task
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

    Return the task outcome and the first owner cancellation separately. The
    caller decides precedence, exception chaining, and any required closure.

    Returns:
        The task value or failure and any owner cancellation.
    """
    cancellation = await _retain_task(task)
    try:
        value: T = task.result()
    except BaseException as error:
        return SettledFailure(error=error, cancellation=cancellation)
    return SettledValue(value=value, cancellation=cancellation)


async def _retain_task[T](task: Task[T], /) -> CancelledError | None:
    """Wait for completion without forwarding cancellation to the task.

    Returns:
        The first owner cancellation, if any.
    """
    # The waiter reports completion without propagating a leaf cancellation.
    waiter = asyncio.create_task(asyncio.wait({task}))
    cancellation: CancelledError | None = None
    while not waiter.done():
        try:
            await asyncio.shield(waiter)
        except CancelledError as error:
            if cancellation is None:
                cancellation = error
    return cancellation
