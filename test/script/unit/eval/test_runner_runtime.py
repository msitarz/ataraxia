# SPDX-License-Identifier: Apache-2.0
"""System runtime adapter behavior."""

import asyncio
from datetime import UTC, datetime
import random
import time

import pytest

from script.eval.runner.adapters import SystemRuntime


def test_utc_now_returns_the_persisted_utc_timestamp_format() -> None:
    # Given
    runtime = SystemRuntime()

    # When
    timestamp = runtime.utc_now()

    # Then
    assert timestamp.endswith("Z")
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() == UTC.utcoffset(parsed)


def test_monotonic_uses_the_standard_monotonic_clock() -> None:
    # Given
    runtime = SystemRuntime()
    before = time.monotonic()

    # When
    elapsed_seconds = runtime.monotonic()

    # Then
    after = time.monotonic()
    assert before <= elapsed_seconds <= after


@pytest.mark.asyncio
async def test_zero_sleep_yields_to_the_event_loop() -> None:
    # Given
    runtime = SystemRuntime()
    events: list[str] = []
    asyncio.get_running_loop().call_soon(events.append, "callback")

    # When
    await runtime.sleep(0)
    events.append("sleep_complete")

    # Then
    assert events == ["callback", "sleep_complete"]


@pytest.mark.asyncio
async def test_sleep_propagates_task_cancellation() -> None:
    # Given
    runtime = SystemRuntime()
    started = asyncio.Event()

    async def wait() -> None:
        started.set()
        await runtime.sleep(3600)

    sleeping = asyncio.create_task(wait())
    await started.wait()

    # When
    sleeping.cancel()

    # Then
    with pytest.raises(asyncio.CancelledError):
        await sleeping


def test_uniform_uses_the_standard_random_bounds() -> None:
    # Given
    runtime = SystemRuntime()
    initial_state = random.getstate()
    random.seed(2718)
    expected = random.Random(2718).uniform(2.5, 7.5)

    # When
    try:
        sample = runtime.uniform(2.5, 7.5)
    finally:
        random.setstate(initial_state)

    # Then
    assert sample == expected
