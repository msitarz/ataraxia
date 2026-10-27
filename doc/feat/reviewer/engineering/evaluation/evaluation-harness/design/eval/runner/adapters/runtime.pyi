# SPDX-License-Identifier: Apache-2.0
"""Historical signature sketch.

The runtime module is authoritative.
"""

from ..ports import Runtime  # ruff: ignore[relative-imports]

class SystemRuntime(Runtime):
    """Use UTC wall time, monotonic duration, asyncio sleep, and uniform jitter."""

    def utc_now(self) -> str: ...
    def monotonic(self) -> float: ...
    async def sleep(self, seconds: float, /) -> None:
        """Use cancellable asyncio sleep; zero seconds still yields."""
        ...
    def uniform(self, lower: float, upper: float, /) -> float: ...
