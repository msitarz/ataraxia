# SPDX-License-Identifier: Apache-2.0
"""Thin run composition; scheduling, shutdown and record projection remain pending."""

import asyncio
from collections.abc import Callable
from contextlib import suppress

from script.eval.evidence import EvidenceStore
from script.eval.model import QuotaWaitContext, RunRecord
from script.eval.runner.ports import (
    AttemptCall,
    BoundRun,
    OutcomeClassifier,
    ProgressFinalStatus,
    ProgressRunPhase,
    ProgressSink,
    QuotaStatusReader,
    Runtime,
)

from .call_states import (
    CallHistory,
    CallState,
    EvidencePending,
    Finished,
    Queued,
    Stopped,
)
from .calls import CallOwner
from .control import RunControl
from .progress import ProgressView, project
from .quota import QuotaOwner
from .quota_states import Draining, Open, QuotaHistory
from .settlement import SettledFailure, Settlement, settle

type RunProjection = Callable[
    [BoundRun, tuple[CallState, ...], QuotaHistory], RunRecord
]


class Coordinator:
    """Own the collaborators for one prepared, provider-bound run.

    The current thin path accepts at most one call and no quota recovery. The
    private projection seam is unfinished; it must be supplied to exercise the
    path until final metadata projection is implemented.
    """

    def __init__(
        self,
        bound_run: BoundRun,
        evidence: EvidenceStore,
        attempt: AttemptCall,
        classifier: OutcomeClassifier,
        quota_status: QuotaStatusReader,
        runtime: Runtime,
        progress: ProgressSink,
        *,
        _projection: RunProjection | None = None,
    ) -> None:
        """Bind a prepared run without reading inputs or starting effects."""
        self._bound_run = bound_run
        self._evidence = evidence
        self._quota_status = quota_status
        self._runtime = runtime
        self._progress = progress
        self._projection = _projection
        self._control = RunControl()
        self._slots = asyncio.Semaphore(bound_run.plan.configuration.concurrency)
        self._calls = tuple(
            CallOwner(
                Queued(CallHistory(call, (), ())),
                bound_run.plan.configuration,
                self._control,
                self._slots,
                attempt,
                classifier,
                quota_status,
                evidence,
                runtime,
            )
            for call in bound_run.calls
        )
        self._quota_history = QuotaHistory((), ())
        self._used = False

    async def run(self) -> RunRecord:
        """Run the exercised thin path, then retain finalization.

        Returns:
            The projected, durably finalized record.

        Unsupported scheduling and projection raise NotImplementedError.
        Reusing an instance raises RuntimeError.
        """
        self._check_ready()
        assert self._projection is not None
        error: BaseException | None = None
        try:
            self._publish("running", None)
            if self._calls:
                await self._calls[0].run()
        except BaseException as caught:
            error = caught
            self._control.latch_stop(caught)
        record = self._projection(self._bound_run, self._states(), self._quota_history)
        result = await settle(asyncio.create_task(self._evidence.finalize(record)))
        _raise_outcome(error, result)
        self._publish("final", _final_status(record, self._states()))
        return record

    def _check_ready(self) -> None:
        """Refuse unsupported paths before any invocation or evidence effect.

        Raises:
            RuntimeError: This coordinator already ran.
        """
        if self._used:
            raise RuntimeError("coordinator already ran")
        self._used = True
        if self._projection is None:
            raise NotImplementedError("final record projection is pending")
        if (
            len(self._calls) > 1
            or self._bound_run.plan.configuration.quota_wait_enabled
        ):
            raise NotImplementedError(
                "multi-call scheduling and quota recovery are pending"
            )

    def _states(self) -> tuple[CallState, ...]:
        """Return current call facts for projection."""
        return tuple(owner.state for owner in self._calls)

    def _publish(
        self, phase: ProgressRunPhase, final_status: ProgressFinalStatus | None
    ) -> None:
        """Project snapshots and isolate expected presentation failures."""
        assert phase in ("running", "final")
        snapshot = project(
            ProgressView(
                self._bound_run.plan.run_id,
                phase,
                final_status,
                self._states(),
                Open(),
                self._quota_history,
                None,
                self._runtime.monotonic(),
                self._runtime.utc_now(),
            )
        )
        with suppress(OSError):
            self._progress.publish(snapshot)

    async def _recover_quota(self, context: QuotaWaitContext) -> None:
        """Await one drained pause; the pending scheduler must call this seam."""
        owner = QuotaOwner(
            Draining(context),
            self._quota_history,
            self._bound_run.plan.configuration,
            self._control,
            self._quota_status,
            self._evidence,
            self._runtime,
            self._bound_run.plan.run_id,
        )
        await owner.recover()
        self._quota_history = owner.history


def _raise_outcome(error: BaseException | None, result: Settlement[None]) -> None:
    """Preserve the local primary control flow after the final write settles."""
    cancellation = result.cancellation
    if isinstance(error, asyncio.CancelledError):
        if isinstance(result, SettledFailure):
            raise error from result.error
        raise error
    if cancellation is not None:
        cause = result.error if isinstance(result, SettledFailure) else error
        raise cancellation from cause
    if error is not None:
        if isinstance(result, SettledFailure):
            raise error from result.error
        raise error
    if isinstance(result, SettledFailure):
        raise result.error


def _final_status(
    record: RunRecord, states: tuple[CallState, ...]
) -> ProgressFinalStatus:
    """Return a status distinguished by accounting and durable call outcomes."""
    if record.state == "incomplete" or any(
        isinstance(state, EvidencePending) for state in states
    ):
        return "incomplete_evidence"
    if any(
        isinstance(state, (Finished, Stopped)) and state.outcome == "cancelled"
        for state in states
    ):
        return "cancelled"
    if any(
        not isinstance(state, Finished) or state.outcome != "success"
        for state in states
    ):
        return "failure"
    return "success"
