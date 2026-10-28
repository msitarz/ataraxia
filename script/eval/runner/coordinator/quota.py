# SPDX-License-Identifier: Apache-2.0
"""Quota wait ownership through durable start and bounded closure.

Probe scheduling and dispatch remain pending until the evidence port accepts the
reviewed preparation, dispatch, and not-dispatched events.
"""

import asyncio
from asyncio import CancelledError
from typing import Literal
from uuid import uuid4

from script.eval.evidence import EvidenceStore
from script.eval.model import (
    HarnessConfig,
    QuotaObservation,
    RunId,
    WaitEnd,
    WaitEvent,
    WaitRecord,
)
from script.eval.runner.policy import quota_probe_allowed, quota_wait_remaining
from script.eval.runner.ports import QuotaStatusReader, Runtime

from .control import RunControl
from .quota_states import (
    Draining,
    QuotaEvidencePending,
    QuotaHistory,
    QuotaState,
    Waiting,
)
from .settlement import SettledFailure, Settlement, settle
from .state import WaitWrite


class QuotaOwner:
    """Own one drained pause and its durable wait and probe history."""

    def __init__(
        self,
        initial: Draining,
        history: QuotaHistory,
        config: HarnessConfig,
        control: RunControl,
        reader: QuotaStatusReader,
        evidence: EvidenceStore,
        runtime: Runtime,
        run_id: RunId,
    ) -> None:
        """Bind the shared gate and effect boundaries for this pause."""
        self._state: QuotaState = initial
        self._history = history
        self._observation = initial.context.quota_observation
        self._config = config
        self._control = control
        self._reader = reader
        self._evidence = evidence
        self._runtime = runtime
        self._run_id = run_id

    @property
    def state(self) -> QuotaState:
        """The current authoritative quota state."""
        return self._state

    @property
    def history(self) -> QuotaHistory:
        """Only durably closed waits and probes."""
        return self._history

    @property
    def observation(self) -> QuotaObservation | None:
        """The latest observation retained for this pause."""
        match self._state:
            case Draining(context):
                return context.quota_observation
            case Waiting() as waiting:
                return waiting.observation
            case QuotaEvidencePending(waiting=waiting):
                return waiting.observation
            case _:
                return self._observation

    async def recover(self) -> QuotaState:
        """Recover after the caller closes the quota gate, drains and persists attempts.

        The current skeleton closes waits when the bound or probe budget is
        exhausted. Probe-capable recovery is an explicit pending leaf.

        Returns:
            The stopped or evidence-pending state.

        Cancellation propagates after required writes settle. Probe-capable
        recovery raises NotImplementedError at its pending seam.

        Raises:
            RuntimeError: Recovery was already invoked.
        """
        if not isinstance(self._state, Draining):
            raise RuntimeError("quota recovery already started")
        initial = self._state
        remaining = self._remaining(initial.context.cumulative_waited_before_seconds)
        if (
            self._control.reason is None
            and remaining != 0
            and quota_probe_allowed(self._config, len(self._history.probes))
        ):
            await _recover_with_probes(self._reader)
        return await self._start_wait(initial)

    def _remaining(self, elapsed: float) -> float | None:
        """Apply the cumulative configured bound to elapsed pause time.

        Returns:
            The remaining seconds, or None for an unbounded wait.
        """
        return quota_wait_remaining(self._config, elapsed)

    def _event(
        self,
        waiting: Waiting,
        kind: Literal["started", "finished"],
        end: WaitEnd | None,
    ) -> WaitEvent:
        """Capture an event with the retained wait identity and fresh clocks.

        Returns:
            The event to persist.
        """
        return WaitEvent(
            run_id=self._run_id,
            wait_id=waiting.wait_id,
            context=waiting.context,
            kind=kind,
            observed_at_utc=self._runtime.utc_now(),
            elapsed_seconds=max(
                0.0, self._runtime.monotonic() - waiting.started_monotonic
            ),
            quota_observation=waiting.observation,
            end=end,
            diagnostic=None,
        )

    async def _start_wait(self, initial: Draining) -> QuotaState:
        """Retain a start write and close every successfully started wait.

        Returns:
            The stopped or evidence-pending state.
        """
        waiting = Waiting(
            initial.context,
            str(uuid4()),
            self._runtime.utc_now(),
            self._runtime.monotonic(),
            "submitted",
            None,
            initial.context.quota_observation,
        )
        self._state = waiting
        event = self._event(waiting, "started", None)
        settled = await settle(
            asyncio.create_task(self._evidence.record_wait_event(event))
        )
        cancellation = self._cancellation(settled.cancellation, settled)
        if isinstance(settled, SettledFailure):
            self._control.note_recording_failure(settled.error)
            self._state = QuotaEvidencePending(
                waiting, WaitWrite(event, None), settled.error, None
            )
            if cancellation is settled.error:
                raise cancellation
            if cancellation is not None:
                raise cancellation from settled.error
            return self._state
        reason = self._control.reason
        end: Literal["bound", "stop", "cancelled"] = "bound"
        if cancellation is not None or (
            reason is not None and reason.cancellation is not None
        ):
            end = "cancelled"
        elif reason is not None:
            end = "stop"
        closure = self._closure(waiting, end)
        waiting = initial.started(waiting, cancellation, reason, closure)
        self._state = waiting
        return await self._close_wait(waiting, closure, cancellation)

    def _closure(
        self, waiting: Waiting, end: Literal["bound", "stop", "cancelled"]
    ) -> WaitRecord:
        """Build the exact summary owed by a durable start.

        Returns:
            The pending closure.
        """
        return WaitRecord(
            wait_id=waiting.wait_id,
            context=waiting.context,
            started_at_utc=waiting.started_at_utc,
            ended_at_utc=self._runtime.utc_now(),
            elapsed_seconds=max(
                0.0, self._runtime.monotonic() - waiting.started_monotonic
            ),
            end=end,
            diagnostic=None,
        )

    async def _close_wait(
        self, waiting: Waiting, closure: WaitRecord, cancellation: CancelledError | None
    ) -> QuotaState:
        """Settle closure before retaining history or propagating cancellation.

        Returns:
            The stopped or evidence-pending state.
        """
        event = self._event(waiting, "finished", closure.end)
        settled = await settle(
            asyncio.create_task(self._evidence.record_wait_event(event))
        )
        later = self._cancellation(settled.cancellation, settled)
        cancellation = cancellation or later
        if isinstance(settled, SettledFailure):
            self._control.note_recording_failure(settled.error)
            self._state = waiting.journal_failed(
                WaitWrite(event, closure), settled.error
            )
            if cancellation is settled.error:
                raise cancellation
            if cancellation is not None:
                raise cancellation from settled.error
            return self._state
        elapsed = waiting.context.cumulative_waited_before_seconds + max(
            0.0, self._runtime.monotonic() - waiting.started_monotonic
        )
        self._history, self._state = waiting.completed(
            self._history,
            closure,
            self._control.reason,
            self._remaining(elapsed),
            self._runtime.utc_now(),
        )
        if cancellation is not None:
            raise cancellation
        return self._state

    def _cancellation(
        self, cancellation: CancelledError | None, settled: Settlement[None]
    ) -> CancelledError | None:
        """Retain this operation's first local cancellation, never another owner's.

        Returns:
            The first local cancellation, if any.
        """
        if cancellation is not None:
            self._control.note_cancellation(cancellation, "owner")
        if isinstance(settled, SettledFailure) and isinstance(
            settled.error, CancelledError
        ):
            self._control.note_cancellation(settled.error, "leaf")
            return cancellation or settled.error
        return cancellation


async def _recover_with_probes(reader: QuotaStatusReader) -> None:
    """Pending: cadence, prepared dispatch, exact-request evidence and closure."""
    raise NotImplementedError("quota probe lifecycle is not wired")
