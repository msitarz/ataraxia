# SPDX-License-Identifier: Apache-2.0
"""Shared internal stop latch and quota dispatch gate."""

from asyncio import CancelledError
from typing import Literal

from script.process_supervisor import AttemptResult, DispatchStop

from .state import PauseOrigin, PauseTrigger, StopReason

class RunControl:
    """One run's mutable stop latch and global dispatch gate.

    A first stop closes dispatch immediately. The owner separately preserves
    later leaf or owner cancellation in ``reason`` even if stop was latched.
    Internal sibling cancellation never replaces it.
    """

    @property
    def reason(self) -> StopReason | None: ...
    @property
    def supervisor_stop(self) -> DispatchStop: ...
    def latch_stop(self, reason: BaseException | AttemptResult, /) -> None: ...
    def note_cancellation(
        self, cancellation: CancelledError, origin: Literal["owner", "leaf"], /
    ) -> None: ...
    def note_recording_failure(self, error: BaseException, /) -> None: ...
    @property
    def quota_origin(self) -> PauseOrigin | None: ...
    @property
    def quota_trigger(self) -> PauseTrigger | None: ...
    def pause_for_quota(self, origin: PauseOrigin, /) -> None:
        """Close dispatch immediately and retain the first origin for this pause."""
        ...
    def publish_quota_trigger(self, trigger: PauseTrigger, /) -> None:
        """Publish only the current origin after its observation is durable."""
        ...
    async def wait_for_quota_pause(self) -> PauseOrigin | None:
        """Wake on a latched pause, or return None when the run stops."""
        ...
    def resume_after_quota(self) -> None: ...
    def dispatch_allowed(self) -> bool: ...
    async def wait_dispatchable(self) -> bool:
        """Wait for an open gate or stop; caller rechecks before invocation."""
        ...
