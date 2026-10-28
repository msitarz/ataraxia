# SPDX-License-Identifier: Apache-2.0
"""Shared stop latch and quota dispatch gate."""

from asyncio import CancelledError, Event
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from typing import Literal

from script.eval.runner.coordinator.quota_states import PauseOrigin, PauseTrigger
from script.eval.runner.coordinator.state import StopReason
from script.process_supervisor import AttemptResult, DispatchStop


@dataclass
class RunControl:
    """Own a run's immediate stop and quota decisions.

    State changes and waits belong to one asyncio event-loop thread. Each
    change wakes all current waiters, which recheck their own predicate.
    """

    _changed: Event = field(default_factory=Event, init=False)
    _reason: StopReason | None = field(default=None, init=False)
    _quota_origin: PauseOrigin | None = field(default=None, init=False)
    _quota_trigger: PauseTrigger | None = field(default=None, init=False)

    @property
    def reason(self) -> StopReason | None:
        """The retained stop and cancellation facts."""
        return self._reason

    @property
    def supervisor_stop(self) -> DispatchStop:
        """The supervisor's immediate stop hook."""
        return self.latch_stop

    def latch_stop(self, reason: BaseException | AttemptResult, /) -> None:
        """Close dispatch on the first stop before notifying waiters."""
        if self._reason is None:
            self._reason = StopReason(reason, None, None, None)
            self._notify()

    def note_cancellation(
        self, cancellation: CancelledError, origin: Literal["owner", "leaf"], /
    ) -> None:
        """Retain the first external cancellation, even after a stop."""
        self.latch_stop(cancellation)
        assert self._reason is not None
        if self._reason.cancellation is None:
            self._reason = replace(
                self._reason, cancellation=cancellation, cancellation_origin=origin
            )

    def note_recording_failure(self, error: BaseException, /) -> None:
        """Stop and retain the first recording failure."""
        self.latch_stop(error)
        assert self._reason is not None
        if self._reason.recording_failure is None:
            self._reason = replace(self._reason, recording_failure=error)

    @property
    def quota_origin(self) -> PauseOrigin | None:
        """The first origin of the current pause."""
        return self._quota_origin

    @property
    def quota_trigger(self) -> PauseTrigger | None:
        """The durable trigger published for the current pause."""
        return self._quota_trigger

    def pause_for_quota(self, origin: PauseOrigin, /) -> None:
        """Close dispatch immediately and retain the first pause origin."""
        if self._quota_origin is None and self._reason is None:
            self._quota_origin = origin
            self._notify()

    def publish_quota_trigger(self, trigger: PauseTrigger, /) -> None:
        """Publish a durable trigger only for the current pause origin.

        Raises:
            ValueError: The trigger is not for the current pause.
        """
        if self._quota_origin is None or trigger.origin != self._quota_origin:
            raise ValueError("trigger does not match the current pause")
        self._quota_trigger = trigger

    async def wait_for_quota_pause(self) -> PauseOrigin | None:
        """Wait for a pause or stop, then recheck stop.

        Returns:
            The origin, or None if stopped.
        """
        await self._wait_until(self._pause_or_stop)
        return None if self._reason is not None else self._quota_origin

    def resume_after_quota(self) -> None:
        """Clear the current pause and notify dispatch waiters."""
        self._quota_origin = None
        self._quota_trigger = None
        self._notify()

    def dispatch_allowed(self) -> bool:
        """Return whether neither stop nor quota pause closes dispatch."""
        return self._reason is None and self._quota_origin is None

    async def wait_dispatchable(self) -> bool:
        """Wait for an open gate or stop, then recheck the gate.

        Returns:
            Whether dispatch remains allowed after the wait.
        """
        await self._wait_until(self._dispatch_or_stop)
        return self.dispatch_allowed()

    def _pause_or_stop(self) -> bool:
        """Return whether a pause or stop has latched."""
        return self._quota_origin is not None or self._reason is not None

    def _dispatch_or_stop(self) -> bool:
        """Return whether the gate is open or the run has stopped."""
        return self.dispatch_allowed() or self._reason is not None

    def _notify(self) -> None:
        """Wake current waiters and give later waits a fresh event."""
        changed = self._changed
        self._changed = Event()
        changed.set()

    async def _wait_until(self, ready: Callable[[], bool]) -> None:
        """Recheck readiness after each state change without losing wakeups."""
        while not ready():
            changed = self._changed
            await changed.wait()
