# SPDX-License-Identifier: Apache-2.0
"""Standard-library clock, async wait, and randomness adapter."""

import asyncio
from datetime import UTC, datetime
import random
import time

from ..ports import Runtime  # ruff: ignore[relative-imports]


class SystemRuntime(Runtime):
    """Use UTC wall time, monotonic duration, async waits, and uniform jitter.

    Example:
        >>> runtime = SystemRuntime()
        >>> runtime.monotonic() >= 0
        True
    """

    def utc_now(self) -> str:
        """Return the current UTC time as an ISO 8601 string ending in ``Z``."""
        return datetime.now(UTC).isoformat().replace("+00:00", "Z")

    def monotonic(self) -> float:
        """Return monotonic seconds for measuring elapsed durations."""
        return time.monotonic()

    async def sleep(self, seconds: float, /) -> None:
        """Wait asynchronously; cancellation interrupts and zero waits yield."""
        await asyncio.sleep(seconds)

    def uniform(self, lower: float, upper: float, /) -> float:
        """Sample jitter uniformly from the supplied inclusive bounds.

        Returns:
            A random value between ``lower`` and ``upper``.
        """
        return random.uniform(lower, upper)
