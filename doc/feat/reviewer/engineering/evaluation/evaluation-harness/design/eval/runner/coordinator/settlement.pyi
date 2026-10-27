# SPDX-License-Identifier: Apache-2.0
"""Retain submitted tasks and preserve cancellation with their outcome."""

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

    A cancelling owner remains primary; the caller attaches any task failure as
    its cause and closes a successfully started wait before propagating it.
    """
    ...
