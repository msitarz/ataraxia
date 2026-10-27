# SPDX-License-Identifier: Apache-2.0
"""Schedule bounded evaluation calls and persist their execution evidence."""

import asyncio
from collections.abc import Callable, Coroutine
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
import signal
from typing import Any, Literal, cast

from script.eval.evidence import EvidenceStore
from script.eval.model import (
    AttemptEvidence,
    AttemptNumber,
    AttemptRecord,
    CapacityWaitContext,
    HarnessConfig,
    QuotaObservation,
    QuotaProbeCancelled,
    QuotaProbeEvidence,
    QuotaProbeId,
    QuotaProbeRequest,
    QuotaProbeSchedule,
    QuotaProbeScheduled,
    QuotaProbeStarted,
    QuotaTelemetryEvent,
    QuotaWaitContext,
    RetryAssessment,
    RetryClass,
    RunRecord,
    WaitEnd,
    WaitEvent,
    WaitRecord,
)
from script.eval.runner.policy import (
    capacity_jitter_bound,
    capacity_retry_allowed,
    infrastructure_retry_allowed,
    quota_poll_delay,
    quota_probe_allowed,
    quota_wait_remaining,
)
from script.eval.runner.ports import (
    AttemptCall,
    BoundRun,
    CallWait,
    EffectiveCall,
    OutcomeClassifier,
    ProgressCounts,
    ProgressSink,
    ProgressSnapshot,
    QuotaStatusReader,
    Runtime,
)
from script.eval.runner.quota_evidence import quota_probe_evidence
from script.process_supervisor import (
    AttemptCancelled,
    AttemptFailureEvidence,
    AttemptResult,
    Completed,
    InfrastructureFailure,
    OutputLimitExceeded,
    TimedOut,
    failure_evidence,
)

type CaptureReturnedAttempt = Callable[
    [EffectiveCall, AttemptResult, str, str], AttemptEvidence
]
type _RetryReason = Literal["infrastructure", "capacity"]
type _RecoveryAction = Literal["continue", "resume", "stop"]


@dataclass(frozen=True)
class _SettledAttempt:
    """One durable attempt and its optional passive quota observation."""

    call: EffectiveCall
    attempt_number: AttemptNumber
    evidence: AttemptEvidence
    record: AttemptRecord
    observation: QuotaObservation | None


@dataclass(frozen=True)
class _QuotaPauseState:
    """One persisted pause with its monotonic start and cumulative bound."""

    trigger: _SettledAttempt
    context: QuotaWaitContext
    wait_id: str
    started_at_utc: str
    started_at_monotonic: float
    cumulative_waited_before_seconds: float


class _DispatchStopped(Exception):
    """Internal signal that no further attempt may enter the supervisor."""


class _QuotaRecoveryStopped(RuntimeError):
    """Policy stop when fresh quota evidence or configured bounds fail."""

    def __init__(
        self, message: str, end: Literal["bound", "stop", "unknown"] = "unknown"
    ) -> None:
        super().__init__(message)
        self.end = end


@dataclass
class _DispatchGate:
    """Atomically gate attempts by stop, quota pause, and active capacity."""

    reason: AttemptResult | BaseException | None = None
    active: int = 0
    paused: bool = False
    ready: asyncio.Event = field(default_factory=asyncio.Event)
    idle: asyncio.Event = field(default_factory=asyncio.Event)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def __post_init__(self) -> None:
        self.ready.set()
        self.idle.set()

    def __call__(self, reason: AttemptResult | BaseException, /) -> None:
        """Retain the first reason that forbids later attempt dispatch."""
        if self.reason is None:
            self.reason = reason
            self.ready.set()

    def pause(self) -> None:
        """Synchronously close the dispatch gate before yielding control."""
        self.paused = True
        self.ready.clear()

    def resume(self) -> None:
        """Reopen dispatch after fresh quota availability is confirmed."""
        self.paused = False
        self.ready.set()

    async def enter(self, semaphore: asyncio.Semaphore, /) -> None:
        """Acquire one slot and recheck all gates immediately before dispatch.

        Raises:
            _DispatchStopped: A stop gate closes before the slot is granted.
        """
        while True:
            await self.ready.wait()
            if self.stopped():
                raise _DispatchStopped
            await semaphore.acquire()
            async with self.lock:
                if self.stopped():
                    semaphore.release()
                    raise _DispatchStopped
                if self.paused:
                    semaphore.release()
                    continue
                self.active += 1
                self.idle.clear()
                return

    def release_slot(self, semaphore: asyncio.Semaphore, /) -> None:
        """Release process capacity after supervisor cleanup, before persistence."""
        semaphore.release()

    def settle_attempt(self, /) -> None:
        """Release the quota barrier after required attempt evidence settles."""
        self.active -= 1
        if self.active == 0:
            self.idle.set()

    async def wait_for_resume(self) -> None:
        """Wait until quota recovery resumes or stop closes the run.

        Raises:
            _DispatchStopped: The run stopped while this call waited.
        """
        await self.ready.wait()
        if self.stopped():
            raise _DispatchStopped

    def stopped(self) -> bool:
        """Report whether the run has latched a stop reason.

        Returns:
            Whether dispatch remains stopped.
        """
        return self.reason is not None


@dataclass
class _CoordinatorState:
    """Mutable execution facts retained by one otherwise frozen coordinator."""

    attempts: dict[int, list[AttemptRecord]] = field(default_factory=dict)
    waits: list[WaitRecord] = field(default_factory=list)
    statuses: dict[
        int,
        Literal[
            "queued",
            "running",
            "retry_wait",
            "evidence_pending",
            "complete",
            "failed",
            "cancelled",
        ],
    ] = field(default_factory=dict)
    quota_observation: QuotaObservation | None = None
    retry_reasons: dict[RetryClass, int] = field(default_factory=dict)
    quota_waited_seconds: float = 0.0
    probes_started: int = 0
    probes_scheduled: int = 0
    settled: dict[int, _SettledAttempt] = field(default_factory=dict)
    call_waits: dict[int, CallWait] = field(default_factory=dict)
    category_retries: dict[int, dict[_RetryReason, int]] = field(default_factory=dict)
    pending_attempts: set[int] = field(default_factory=set)
    pending_calls: set[int] = field(default_factory=set)
    started_positions: set[int] = field(default_factory=set)
    pending_probes: int = 0
    workers: set[asyncio.Task[None]] = field(default_factory=set)
    active_workers: dict[int, asyncio.Task[None] | None] = field(default_factory=dict)
    internal_cancellations: set[asyncio.Task[None] | None] = field(default_factory=set)
    gate: _DispatchGate | None = None
    quota_recovery_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    signal_handlers: dict[signal.Signals, object] | None = None
    interrupt_signal: str | None = None
    cancellation: asyncio.CancelledError | None = None
    raised_error: BaseException | None = None
    recording_error: BaseException | None = None
    run_incomplete: bool = False
    active_attempts: dict[int, AttemptNumber] = field(default_factory=dict)
    active_probes: int = 0
    probes_completed: int = 0
    probes_failed: int = 0
    probes_cancelled: int = 0
    quota_trigger: _SettledAttempt | None = None


@dataclass(frozen=True)
class Coordinator:
    """Own one bound run's bounded dispatch, retries, recovery, and accounting.

    The scheduler executes independent matrix calls concurrently within the
    configured limit, and this instance owns their stop and recovery state.
    """

    bound_run: BoundRun
    evidence: EvidenceStore
    attempt: AttemptCall
    classifier: OutcomeClassifier
    quota_status: QuotaStatusReader
    runtime: Runtime
    progress: ProgressSink
    capture_returned_attempt: CaptureReturnedAttempt = field(
        default_factory=lambda: _capture_returned_attempt
    )
    _state: _CoordinatorState = field(default_factory=_CoordinatorState, compare=False)

    @property
    def config(self) -> HarnessConfig:
        """Configuration frozen into this coordinator's plan."""
        return self.bound_run.plan.configuration

    async def run(self) -> RunRecord:
        """Run the frozen plan, settle owned work, and persist final accounting.

        Returns:
            Final run accounting after all owned attempts and writes settle.

        Raises:
            ValueError: Dry-run plans must return through the reporting path.
        """
        if self.config.dry_run:
            raise ValueError("dry-run plans do not enter the coordinator")
        gate = _DispatchGate()
        self._state.gate = gate
        self._state.statuses = {
            call.planned_call.position: "queued" for call in self.bound_run.calls
        }
        self._install_stop_handlers()
        try:
            semaphore = asyncio.Semaphore(self.config.concurrency)
            workers = {
                asyncio.create_task(
                    self._run_call(call, semaphore),
                    name=f"eval-call-{call.planned_call.position}",
                )
                for call in self.bound_run.calls
            }
            self._state.workers = workers
            await self._run_workers(workers)
            record = _assemble_run_record(self)
            await self._finalize_run(record)
            self._publish_progress("final")
            terminal_error = (
                self._state.cancellation
                or self._state.raised_error
                or self._state.recording_error
            )
            if terminal_error is not None:
                raise terminal_error
            return record
        finally:
            self._restore_stop_handlers()

    async def _run_workers(self, workers: set[asyncio.Task[None]], /) -> None:
        """Await all call workers and preserve stop settlement on failure."""
        try:
            await asyncio.gather(*workers)
        except BaseException as error:
            await self._stop_and_settle(error, workers)
            self._remember_terminal_error(error)

    async def _finalize_run(self, record: RunRecord, /) -> None:
        """Persist final accounting without masking an earlier terminal cause."""
        try:
            _, cancellation = await self._settle_write(
                self.evidence.finalize(record), "finalize evidence"
            )
        except BaseException as error:
            self._state.recording_error = self._state.recording_error or error
            self._state.run_incomplete = True
            self._remember_terminal_error(error)
            return
        if cancellation is not None:
            self._state.cancellation = self._state.cancellation or cancellation

    def _install_stop_handlers(self) -> None:
        """Own SIGINT/SIGTERM handlers for the lifetime of one active run."""
        task = asyncio.current_task()
        if task is None:
            return
        previous: dict[signal.Signals, object] = {}
        for signum in (signal.SIGINT, signal.SIGTERM):
            prior = signal.getsignal(signum)

            def handle(received: signal.Signals = signum) -> None:
                self._state.interrupt_signal = received.name
                task.cancel(f"evaluation interrupted by {received.name}")

            try:
                signal.signal(
                    signum, lambda _number, _frame, callback=handle: callback()
                )
            except ValueError:
                continue
            previous[signum] = prior
        self._state.signal_handlers = previous

    def _restore_stop_handlers(self) -> None:
        """Restore the exact handlers that preceded this run."""
        previous = self._state.signal_handlers
        self._state.signal_handlers = None
        if previous is None:
            return
        for signum, prior in previous.items():
            try:
                signal.signal(signum, cast(Any, prior))
            except ValueError:
                continue

    async def _run_call(  # ruff: ignore[too-many-statements]
        self, call: EffectiveCall, semaphore: asyncio.Semaphore, /
    ) -> None:
        """Run one call's independent retry lifecycle without blocking peers.

        Raises:
            asyncio.CancelledError: The owner cancels this worker.
        """
        position = call.planned_call.position
        attempt_number: AttemptNumber = 1
        try:  # ruff: ignore[too-many-statements-in-try-clause]
            while True:
                gate = self._require_gate()
                await gate.enter(semaphore)
                self._state.statuses[position] = "running"
                self._state.started_positions.add(position)
                self._state.active_attempts[position] = attempt_number
                self._state.active_workers[position] = asyncio.current_task()
                self._publish_progress("quota_paused" if gate.paused else "running")
                settled = await self._execute_attempt(
                    call, attempt_number, gate, semaphore
                )
                self._state.active_workers.pop(position, None)
                if self._call_must_stop(settled, position, gate):
                    return
                next_attempt = await self._schedule_next_attempt(
                    call, settled, attempt_number, gate
                )
                if next_attempt is None:
                    return
                attempt_number = next_attempt
        except _DispatchStopped:
            return
        except asyncio.CancelledError as cancellation:
            if self._handle_worker_cancellation(position, cancellation):
                return
            raise
        except BaseException as error:
            self._handle_worker_failure(position, error)
            raise

    def _handle_worker_cancellation(
        self, position: int, cancellation: asyncio.CancelledError, /
    ) -> bool:
        """Swallow internal stop cancellation while retaining owner cancellation.

        Returns:
            Whether this was an internal cancellation owned by the coordinator.
        """
        task = asyncio.current_task()
        if task in self._state.internal_cancellations:
            self._state.internal_cancellations.discard(task)
            return True
        self._state.cancellation = self._state.cancellation or cancellation
        self._require_gate()(cancellation)
        self._state.statuses[position] = (
            "cancelled" if position in self._state.attempts else "queued"
        )
        return False

    def _handle_worker_failure(self, position: int, error: BaseException, /) -> None:
        """Latch one worker failure and its truthful evidence-pending state."""
        self._remember_terminal_error(error)
        self._require_gate()(error)
        self._state.run_incomplete = True
        self._state.statuses[position] = (
            "evidence_pending" if position in self._state.pending_calls else "failed"
        )
        self._cancel_active_workers()

    def _call_must_stop(
        self, settled: _SettledAttempt, position: int, gate: _DispatchGate, /
    ) -> bool:
        """Apply run-level cancellation, failure, and stop to one settled call.

        Returns:
            Whether this call must end without another attempt.
        """
        task = asyncio.current_task()
        internal_stop = task in self._state.internal_cancellations
        self._state.internal_cancellations.discard(task)
        if self._state.cancellation is not None:
            gate(self._state.cancellation)
            self._cancel_active_workers()
            self._state.statuses[position] = "cancelled"
            return True
        if self._state.raised_error is not None:
            gate(self._state.raised_error)
            self._cancel_active_workers()
            self._state.statuses[position] = "failed"
            return True
        if gate.stopped() or internal_stop:
            self._state.statuses[position] = _call_status(settled)
            return True
        return False

    async def _schedule_next_attempt(
        self,
        call: EffectiveCall,
        settled: _SettledAttempt,
        attempt_number: AttemptNumber,
        gate: _DispatchGate,
        /,
    ) -> AttemptNumber | None:
        """Choose quota recovery or one local retry without holding a slot.

        Returns:
            The next attempt number, or ``None`` when this call is terminal.
        """
        position = call.planned_call.position
        if not self._retry_is_safe(settled):
            self._state.statuses[position] = _call_status(settled)
            if settled.evidence.control_flow != "returned" or not _dispatch_safe(
                settled
            ):
                self._state.run_incomplete = True
                gate(RuntimeError("attempt settlement forbids further dispatch"))
                self._cancel_active_workers()
            self._publish_progress("stopping" if gate.stopped() else "running")
            return None
        if self._quota_exhausted(settled):
            return await self._retry_after_quota(settled, attempt_number, gate)
        return await self._retry_after_ordinary_failure(settled, attempt_number, gate)

    async def _retry_after_quota(
        self,
        settled: _SettledAttempt,
        attempt_number: AttemptNumber,
        gate: _DispatchGate,
        /,
    ) -> AttemptNumber | None:
        """Pause globally and retry only a confidently absent quota result.

        Returns:
            The next attempt number, or ``None`` when no quota retry is eligible.
        """
        position = settled.call.planned_call.position
        gate.pause()
        self._state.statuses[position] = _call_status(settled)
        if not await self._recover_quota_pause(settled, gate):
            return None
        if not _quota_retry_eligible(settled):
            self._state.statuses[position] = _call_status(settled)
            return None
        return attempt_number + 1

    async def _retry_after_ordinary_failure(
        self,
        settled: _SettledAttempt,
        attempt_number: AttemptNumber,
        gate: _DispatchGate,
        /,
    ) -> AttemptNumber | None:
        """Wait for quota to reopen, then apply this call's finite retry budget.

        Returns:
            The next attempt number, or ``None`` when no retry is eligible.
        """
        if gate.paused:
            await gate.wait_for_resume()
        reason = self._retry_reason_for(settled)
        if reason is None:
            self._state.statuses[settled.call.planned_call.position] = _call_status(
                settled
            )
            return None
        position = settled.call.planned_call.position
        self._state.retry_reasons[reason] = self._state.retry_reasons.get(reason, 0) + 1
        category_uses = self._state.category_retries.setdefault(position, {})
        category_index = category_uses.get(reason, 0)
        category_uses[reason] = category_index + 1
        self._state.statuses[position] = "retry_wait"
        self._publish_progress("running")
        if reason == "capacity":
            await self._wait_capacity(settled, category_index, gate)
        if gate.paused:
            await gate.wait_for_resume()
        return None if gate.stopped() else attempt_number + 1

    def _retry_reason_for(self, settled: _SettledAttempt, /) -> _RetryReason | None:
        """Apply the independent retry counter for this call's classified type.

        Returns:
            Its next eligible retry category, or ``None``.
        """
        if isinstance(settled.evidence.outcome, Completed):
            if (
                settled.evidence.outcome.exit_status == 0
                or not self.config.retry_nonzero_exit
            ):
                return None
        elif not isinstance(
            settled.evidence.outcome, (TimedOut, InfrastructureFailure)
        ):
            return None
        assessment = settled.record.retry_assessment
        if assessment is None:
            return None
        uses = self._state.category_retries.get(settled.call.planned_call.position, {})
        category = assessment.retry_class
        if category not in {"infrastructure", "capacity"}:
            return None
        return _retry_reason(assessment, uses.get(category, 0), self.config)

    async def _recover_quota_pause(
        self, trigger: _SettledAttempt, gate: _DispatchGate, /
    ) -> bool:
        """Run one awaited recovery after every active attempt has settled.

        Returns:
            Whether dispatch may resume after the current pause.
        """
        async with self._state.quota_recovery_lock:
            if gate.stopped():
                return False
            if not gate.paused:
                return True
            if self._state.quota_trigger is None:
                self._state.quota_trigger = trigger
            await gate.idle.wait()
            if gate.stopped():
                return False
            try:
                await self._wait_for_quota(self._state.quota_trigger, gate)
            except _QuotaRecoveryStopped as error:
                self._state.run_incomplete = True
                gate(error)
                self._publish_progress("stopping")
                self._cancel_active_workers()
                return False
            self._state.quota_trigger = None
            gate.resume()
            self._publish_progress("running")
            return True

    async def _stop_and_settle(
        self, error: BaseException, workers: set[asyncio.Task[None]], /
    ) -> None:
        """Latch stop and retain all worker cleanup despite repeated cancellation."""
        gate = self._require_gate()
        gate(error)
        self._remember_terminal_error(error)
        self._state.run_incomplete = True
        self._publish_progress("stopping")
        for task in workers:
            if not task.done():
                self._state.internal_cancellations.add(task)
                task.cancel()
        settlement = asyncio.gather(*workers, return_exceptions=True)
        while not settlement.done():
            try:
                await asyncio.shield(settlement)
            except asyncio.CancelledError as cancellation:
                self._state.cancellation = self._state.cancellation or cancellation
                gate(cancellation)
        for result in settlement.result():
            if isinstance(result, BaseException) and result is not error:
                self._remember_terminal_error(result)
        for position, status in tuple(self._state.statuses.items()):
            if status == "retry_wait":
                self._state.statuses[position] = "cancelled"

    def _cancel_active_workers(self) -> None:
        """Cancel other owned attempts after a global unsafe stop."""
        current = asyncio.current_task()
        for task in self._state.workers:
            if task is not None and task is not current and not task.done():
                self._state.internal_cancellations.add(task)
                task.cancel()

    def _require_gate(self) -> _DispatchGate:
        """Return this run's sole dispatch gate.

        Raises:
            RuntimeError: No run has initialized dispatch state.
        """
        gate = self._state.gate
        if gate is None:
            raise RuntimeError("coordinator run has no dispatch gate")
        return gate

    def _remember_terminal_error(self, error: BaseException, /) -> None:
        """Retain cancellation or the first unexpected failure as primary."""
        if isinstance(error, asyncio.CancelledError):
            if self._state.cancellation is None:
                self._state.cancellation = error
                if self._state.raised_error is not None:
                    error.add_note(
                        "Additional failure while stopping: "
                        f"{self._state.raised_error!r}"
                    )
            elif self._state.cancellation is not error:
                self._state.cancellation.add_note(
                    f"Additional cancellation while stopping: {error!r}"
                )
        elif self._state.cancellation is not None:
            self._state.cancellation.add_note(
                f"Additional failure while stopping: {error!r}"
            )
        elif self._state.raised_error is None:
            self._state.raised_error = error
        else:
            self._state.raised_error.add_note(
                f"Additional error while stopping: {error!r}"
            )

    def _retry_is_safe(self, settled: _SettledAttempt, /) -> bool:
        """Require returned evidence with cleanup that permits new dispatch.

        Returns:
            Whether retry policy may consider the attempt.
        """
        if settled.evidence.control_flow != "returned":
            return False
        outcome = settled.evidence.outcome
        if isinstance(outcome, (AttemptCancelled, OutputLimitExceeded)):
            return False
        observation = getattr(outcome, "observation", None)
        return observation is not None and observation.cleanup.dispatch_permitted

    def _quota_exhausted(self, settled: _SettledAttempt, /) -> bool:
        """Require quota classification, verified scope, and exhausted state.

        Returns:
            Whether this observation may pause the bound run.
        """
        observation = settled.observation
        assessment = settled.record.retry_assessment
        return (
            self.config.quota_wait_enabled
            and assessment is not None
            and assessment.retry_class == "quota"
            and observation is not None
            and observation.scope is not None
            and observation.scope == self.bound_run.binding.quota_scope
            and bool(observation.windows)
            and all(
                window.state not in {"unknown", "unavailable"}
                for window in observation.windows
            )
            and any(window.state == "exhausted" for window in observation.windows)
        )

    async def _wait_capacity(  # ruff: ignore[too-many-statements]
        self,
        settled: _SettledAttempt,
        retry_index: int,
        stop: _DispatchGate,
        /,
    ) -> None:
        """Persist and await one call-local jittered capacity delay.

        Raises:
            asyncio.CancelledError: The owner cancels the wait.
            RuntimeError: Configuration is invalid or the global stop is latched.
        """
        base = self.config.capacity_backoff_base_seconds
        cap = self.config.capacity_backoff_cap_seconds
        if base is None or cap is None or stop.stopped():
            raise RuntimeError("capacity backoff is unavailable or dispatch stopped")
        index = retry_index
        bound = capacity_jitter_bound(index, base, cap)
        delay = self.runtime.uniform(0.0, bound)
        wait_id = f"{settled.call.call_id}:capacity:{index}"
        context = CapacityWaitContext(
            kind="capacity",
            call_id=settled.call.call_id,
            failed_attempt_number=settled.attempt_number,
            retry_index=index,
            base_seconds=base,
            cap_seconds=cap,
            jitter_bound_seconds=bound,
            sampled_seconds=delay,
        )
        started = self.runtime.monotonic()
        started_at_utc = self.runtime.utc_now()
        try:
            _, cancellation = await self._settle_write(
                self.evidence.record_wait_event(
                    WaitEvent(
                        run_id=settled.call.run_id,
                        wait_id=wait_id,
                        context=context,
                        kind="started",
                        observed_at_utc=started_at_utc,
                        elapsed_seconds=0.0,
                        quota_observation=None,
                        end=None,
                        diagnostic=None,
                    )
                ),
                "capacity wait start",
            )
        except BaseException as error:
            self._state.recording_error = self._state.recording_error or error
            self._state.run_incomplete = True
            stop(error)
            raise
        if cancellation is not None:
            self._state.cancellation = self._state.cancellation or cancellation
            stop(cancellation)
            raise cancellation
        self._state.call_waits[settled.call.planned_call.position] = CallWait(
            call_id=settled.call.call_id,
            reason="capacity",
            attempt_number=settled.attempt_number,
            elapsed_seconds=0.0,
            remaining_seconds=delay,
        )
        self._publish_progress("running")
        try:
            await self.runtime.sleep(delay)
        except asyncio.CancelledError as cancellation:
            await self._finish_capacity_wait(
                settled, context, wait_id, started_at_utc, started, "cancelled"
            )
            raise
        await self._finish_capacity_wait(
            settled, context, wait_id, started_at_utc, started, "delay_elapsed"
        )
        self._state.call_waits.pop(settled.call.planned_call.position, None)
        if stop.stopped():
            raise RuntimeError("dispatch stopped during capacity backoff")

    async def _finish_capacity_wait(
        self,
        settled: _SettledAttempt,
        context: CapacityWaitContext,
        wait_id: str,
        started_at_utc: str,
        started_at_monotonic: float,
        end: Literal["cancelled", "delay_elapsed"],
        /,
    ) -> None:
        """Persist a completed capacity wait and retain its summary."""
        ended_at_utc = self.runtime.utc_now()
        elapsed = max(0.0, self.runtime.monotonic() - started_at_monotonic)
        try:
            _, cancellation = await self._settle_write(
                self.evidence.record_wait_event(
                    WaitEvent(
                        run_id=settled.call.run_id,
                        wait_id=wait_id,
                        context=context,
                        kind="finished",
                        observed_at_utc=ended_at_utc,
                        elapsed_seconds=elapsed,
                        quota_observation=None,
                        end=end,
                        diagnostic=None,
                    )
                ),
                "capacity wait finish",
            )
        except BaseException as error:
            self._state.recording_error = self._state.recording_error or error
            self._state.run_incomplete = True
            self._require_gate()(error)
            raise
        if cancellation is not None:
            self._state.cancellation = self._state.cancellation or cancellation
            self._require_gate()(cancellation)
        self._state.waits.append(
            WaitRecord(
                wait_id=wait_id,
                context=context,
                started_at_utc=started_at_utc,
                ended_at_utc=ended_at_utc,
                elapsed_seconds=elapsed,
                end=end,
                diagnostic=None,
            )
        )

    def _publish_progress(
        self, phase: Literal["running", "quota_paused", "stopping", "final"], /
    ) -> None:
        """Publish a best-effort snapshot from current call and attempt state."""
        states = tuple(
            self._state.statuses.get(call.planned_call.position, "queued")
            for call in self.bound_run.calls
        )
        attempts = tuple(
            record for records in self._state.attempts.values() for record in records
        )
        counts = self._progress_counts(phase, states, attempts)
        final_status = _final_progress_status(phase, counts, self._state)
        observation = self._state.quota_observation
        now = datetime.fromisoformat(self.runtime.utc_now().replace("Z", "+00:00"))
        ages = (
            ()
            if observation is None
            else tuple(
                (
                    window.window_id,
                    None
                    if window.source_observed_at_utc is None
                    else max(
                        0.0,
                        (
                            now
                            - datetime.fromisoformat(
                                window.source_observed_at_utc.replace("Z", "+00:00")
                            )
                        ).total_seconds(),
                    ),
                )
                for window in observation.windows
            )
        )
        with suppress(Exception):
            self.progress.publish(
                ProgressSnapshot(
                    run_id=self.bound_run.plan.run_id,
                    phase=phase,
                    final_status=final_status,
                    counts=counts,
                    retry_reasons=tuple(sorted(self._state.retry_reasons.items())),
                    call_waits=tuple(self._state.call_waits.values()),
                    quota_observation=observation,
                    quota_window_ages_seconds=ages,
                )
            )

    def _progress_counts(
        self,
        phase: Literal["running", "quota_paused", "stopping", "final"],
        states: tuple[str, ...],
        attempts: tuple[AttemptRecord, ...],
        /,
    ) -> ProgressCounts:
        """Project disjoint call, attempt, and probe lifecycle counts.

        Returns:
            Counts for the current disjoint call and evidence states.
        """
        successful = sum(_attempt_record_successful(record) for record in attempts)
        cancelled = sum(record.control_flow == "cancelled" for record in attempts)
        active = self._state.active_attempts
        pending = self._state.pending_attempts
        terminal = self._state.probes_completed + self._state.probes_failed
        terminal += self._state.probes_cancelled
        return ProgressCounts(
            calls_queued=0
            if phase in {"final", "stopping"}
            else states.count("queued"),
            calls_stopped_not_started=(
                states.count("queued") if phase in {"final", "stopping"} else 0
            ),
            calls_active=states.count("running"),
            calls_retry_wait=states.count("retry_wait"),
            calls_evidence_pending=states.count("evidence_pending"),
            calls_succeeded=states.count("complete"),
            calls_failed=states.count("failed"),
            calls_cancelled=states.count("cancelled"),
            attempts_started=len(attempts) + len(active) + len(pending),
            retries_started=(
                sum(len(records) - 1 for records in self._state.attempts.values())
                + sum(number > 1 for number in active.values())
                + sum(position in self._state.attempts for position in pending)
            ),
            attempts_active=len(active),
            attempts_evidence_pending=len(pending),
            attempts_succeeded=successful,
            attempts_failed=len(attempts) - successful - cancelled,
            attempts_cancelled=cancelled,
            probes_started=terminal
            + self._state.active_probes
            + self._state.pending_probes,
            probes_active=self._state.active_probes,
            probes_evidence_pending=self._state.pending_probes,
            probes_completed=self._state.probes_completed,
            probes_failed=self._state.probes_failed,
            probes_cancelled=self._state.probes_cancelled,
        )

    async def _execute_attempt(  # ruff: ignore[too-many-statements]
        self,
        call: EffectiveCall,
        attempt_number: AttemptNumber,
        stop: _DispatchGate,
        semaphore: asyncio.Semaphore,
        /,
    ) -> _SettledAttempt:
        """Capture, release the process slot, and durably settle one attempt.

        Returns:
            The settled attempt and its passive quota observation, if enabled.
        """
        position = call.planned_call.position
        captured = False
        try:
            started_at = self.runtime.utc_now()
            attempt_evidence = await self._capture_attempt(call, stop, started_at)
            if not _attempt_evidence_dispatch_safe(attempt_evidence):
                self._state.run_incomplete = True
                stop(RuntimeError("attempt cleanup forbids further dispatch"))
            captured = True
        finally:
            self._state.active_attempts.pop(position, None)
            if captured:
                self._state.pending_attempts.add(position)
                self._state.pending_calls.add(position)
                self._state.statuses[position] = "evidence_pending"
            if not captured:
                stop.release_slot(semaphore)
                stop.settle_attempt()
        self._publish_progress("running")
        try:
            attempt_record, cancellation = await self._persist_attempt(
                call, attempt_number, attempt_evidence, stop
            )
            self._state.attempts.setdefault(position, []).append(attempt_record)
            self._state.pending_attempts.discard(position)
            if (
                cancellation is not None
                and asyncio.current_task() not in self._state.internal_cancellations
            ):
                self._state.cancellation = self._state.cancellation or cancellation
                stop(cancellation)
            observation = await self._observe_attempt(
                call, attempt_number, attempt_evidence
            )
            self._state.pending_calls.discard(position)
            settled = self._retain_settled(
                call, attempt_number, attempt_evidence, attempt_record, observation
            )
            if self._quota_exhausted(settled):
                stop.pause()
            self._state.statuses[position] = _call_status(settled)
            self._publish_progress("quota_paused" if stop.paused else "running")
            return settled
        finally:
            stop.release_slot(semaphore)
            stop.settle_attempt()

    async def _persist_attempt(
        self,
        call: EffectiveCall,
        attempt_number: AttemptNumber,
        evidence: AttemptEvidence,
        stop: _DispatchGate,
        /,
    ) -> tuple[AttemptRecord, asyncio.CancelledError | None]:
        """Persist one attempt or latch an evidence failure before dispatch.

        Returns:
            The persisted attempt record and cancellation observed during writing.
        """
        try:
            return await self._settle_write(
                self._record_attempt(call, attempt_number, evidence),
                "attempt evidence",
            )
        except BaseException as error:
            self._state.recording_error = self._state.recording_error or error
            self._state.run_incomplete = True
            stop(error)
            self._cancel_active_workers()
            raise

    def _retain_settled(
        self,
        call: EffectiveCall,
        attempt_number: AttemptNumber,
        attempt_evidence: AttemptEvidence,
        attempt_record: AttemptRecord,
        observation: QuotaObservation | None,
        /,
    ) -> _SettledAttempt:
        """Retain one durable attempt and latch its quota pause if applicable.

        Returns:
            The settled in-memory attempt associated with durable evidence.
        """
        settled = _SettledAttempt(
            call=call,
            attempt_number=attempt_number,
            evidence=attempt_evidence,
            record=attempt_record,
            observation=observation,
        )
        self._state.settled[call.planned_call.position] = settled
        if self._quota_exhausted(settled) and self._state.quota_trigger is None:
            self._state.quota_trigger = settled
        return settled

    async def _capture_attempt(
        self,
        call: EffectiveCall,
        stop: _DispatchGate,
        started_at: str,
        /,
    ) -> AttemptEvidence:
        """Capture a returned, cancelled, or safely failed supervisor outcome.

        Returns:
            Typed attempt evidence preserving the supervisor observation.
        """
        try:
            outcome = await self.attempt(call.request, stop)
        except AttemptCancelled as cancellation:
            return self._capture_cancelled_attempt(call, cancellation, started_at, stop)
        except asyncio.CancelledError as cancellation:
            return self._capture_unobserved_cancellation(
                call, cancellation, started_at, stop
            )
        except BaseException as error:
            return self._capture_failed_attempt(call, error, started_at, stop)
        ended_at = self.runtime.utc_now()
        assert isinstance(
            outcome,
            (Completed, TimedOut, OutputLimitExceeded, InfrastructureFailure),
        )
        return self.capture_returned_attempt(call, outcome, started_at, ended_at)

    def _capture_cancelled_attempt(
        self,
        call: EffectiveCall,
        cancellation: asyncio.CancelledError,
        started_at: str,
        stop: _DispatchGate,
        /,
    ) -> AttemptEvidence:
        """Retain supervisor cancellation facts for final cancellation reporting.

        Returns:
            Typed cancelled attempt evidence.
        """
        if not stop.stopped():
            self._state.cancellation = cancellation
        stop(cancellation)
        outcome = (
            cancellation
            if isinstance(cancellation, AttemptCancelled)
            else failure_evidence(cancellation)
        )
        return AttemptEvidence(
            control_flow="cancelled",
            outcome=outcome,
            error_type=None,
            diagnostic=None,
            request=call.request,
            started_at_utc=started_at,
            ended_at_utc=self.runtime.utc_now(),
            usage_telemetry=_captured_stdout(outcome),
        )

    def _capture_unobserved_cancellation(
        self,
        call: EffectiveCall,
        cancellation: asyncio.CancelledError,
        started_at: str,
        stop: _DispatchGate,
        /,
    ) -> AttemptEvidence:
        """Retain cancellation even when the supervisor supplies no process facts.

        Returns:
            Cancellation evidence with no invented process observation.
        """
        task = asyncio.current_task()
        internal = task in self._state.internal_cancellations
        if not internal:
            self._state.cancellation = self._state.cancellation or cancellation
        stop(cancellation)
        return AttemptEvidence(
            control_flow="cancelled",
            outcome=failure_evidence(cancellation),
            error_type=type(cancellation).__name__,
            diagnostic=str(cancellation),
            request=call.request,
            started_at_utc=started_at,
            ended_at_utc=self.runtime.utc_now(),
            usage_telemetry=_captured_stdout(failure_evidence(cancellation)),
        )

    def _capture_failed_attempt(
        self,
        call: EffectiveCall,
        error: BaseException,
        started_at: str,
        stop: _DispatchGate,
        /,
    ) -> AttemptEvidence:
        """Retain attached cleanup evidence and remember the original failure.

        Returns:
            Typed failed attempt evidence when cleanup evidence is attached.
        """
        supervisor_evidence = failure_evidence(error)
        stop(error)
        self._state.raised_error = self._state.raised_error or error
        self._state.run_incomplete = True
        return AttemptEvidence(
            control_flow="raised",
            outcome=supervisor_evidence,
            error_type=type(error).__name__,
            diagnostic=str(error),
            request=call.request,
            started_at_utc=started_at,
            ended_at_utc=self.runtime.utc_now(),
            usage_telemetry=_captured_stdout(supervisor_evidence),
        )

    async def _record_attempt(
        self,
        call: EffectiveCall,
        attempt_number: AttemptNumber,
        attempt_evidence: AttemptEvidence,
        /,
    ) -> AttemptRecord:
        """Classify and durably persist one captured evaluation outcome.

        Returns:
            The immutable evidence record after its persistence succeeds.
        """
        assessment = self.classifier.assess(attempt_evidence)
        attempt_record = await self.evidence.record_attempt(
            call.run_id,
            call.call_id,
            call.planned_call.position,
            attempt_number,
            attempt_evidence,
            assessment,
        )
        return attempt_record

    async def _observe_attempt(
        self,
        call: EffectiveCall,
        attempt_number: AttemptNumber,
        attempt_evidence: AttemptEvidence,
        /,
    ) -> QuotaObservation | None:
        """Ingest and persist optional passive quota telemetry after the attempt.

        Returns:
            The observation, or ``None`` when quota telemetry is disabled.
        """
        observation = None
        if self.config.quota_wait_enabled:
            observation = await self.quota_status.observe_settled_attempt(
                attempt_evidence
            )
            try:
                _, cancellation = await self._settle_write(
                    self.evidence.record_quota_telemetry(
                        QuotaTelemetryEvent(
                            run_id=call.run_id,
                            call_id=call.call_id,
                            attempt_number=attempt_number,
                            observation=observation,
                        )
                    ),
                    "quota telemetry",
                )
            except BaseException as error:
                self._state.recording_error = self._state.recording_error or error
                self._state.run_incomplete = True
                self._require_gate()(error)
                raise
            if (
                cancellation is not None
                and asyncio.current_task() not in self._state.internal_cancellations
            ):
                self._state.cancellation = self._state.cancellation or cancellation
                self._require_gate()(cancellation)
            self._retain_quota_observation(observation)
        return observation

    def _retain_quota_observation(
        self, observation: QuotaObservation | None, /
    ) -> None:
        """Expose only durably recorded observations for the bound scope."""
        expected_scope = self.quota_status.expected_scope
        if (
            observation is not None
            and observation.scope is not None
            and observation.scope == self.bound_run.binding.quota_scope
            and observation.scope == expected_scope
        ):
            self._state.quota_observation = observation

    async def _settle_write[T](
        self, write: Coroutine[Any, Any, T], label: str, /
    ) -> tuple[T, asyncio.CancelledError | None]:
        """Shield one submitted persistence operation through owner cancellation.

        Returns:
            The write result and any cancellation received while it settled.

        Raises:
            asyncio.CancelledError: The submitted persistence operation was cancelled.
        """
        task = asyncio.create_task(
            write, name=f"eval-evidence-{label.replace(' ', '-')}"
        )
        cancellation: asyncio.CancelledError | None = None
        while not task.done():
            try:
                await asyncio.shield(task)
            except asyncio.CancelledError as error:
                cancellation = cancellation or error
            except Exception:
                break  # Inspect the settled task below to preserve cancellation.
        if task.cancelled():
            raise asyncio.CancelledError(f"{label} persistence task was cancelled")
        if (error := task.exception()) is not None:
            if cancellation is not None and isinstance(error, Exception):
                raise cancellation from error
            raise error
        return task.result(), cancellation

    async def _wait_for_quota(
        self, trigger: _SettledAttempt, stop: _DispatchGate, /
    ) -> None:
        """Record and run one pause until fresh quota permits resumption.

        Raises:
            _QuotaRecoveryStopped: Policy bounds or unknown observations stop recovery.
        """
        if self.quota_status.expected_scope != self.bound_run.binding.quota_scope:
            raise _QuotaRecoveryStopped(
                "quota reader scope does not match the bound run", "unknown"
            )
        pause = await self._start_quota_wait(trigger)
        prior_probe: QuotaProbeEvidence | None = None
        finished = False
        try:  # ruff: ignore[too-many-statements-in-try-clause]
            while True:
                action, probe, remaining = await self._quota_recovery_step(
                    pause, trigger, prior_probe, stop
                )
                if action == "continue":
                    prior_probe = probe
                    continue
                finished = True
                await self._finish_quota_wait(
                    pause.trigger,
                    pause.context,
                    pause.wait_id,
                    pause.started_at_utc,
                    pause.started_at_monotonic,
                    "quota_available"
                    if action == "resume"
                    else "bound"
                    if remaining is not None and remaining <= 0.0
                    else "unknown",
                    probe.observation,
                )
                if action == "stop":
                    raise _QuotaRecoveryStopped(  # ruff: ignore[raise-within-try]
                        "quota recovery stopped without resumption"
                    )
                return
        except BaseException as error:
            self._update_quota_elapsed(pause)
            if not finished:
                await self._finish_quota_wait(
                    pause.trigger,
                    pause.context,
                    pause.wait_id,
                    pause.started_at_utc,
                    pause.started_at_monotonic,
                    _quota_wait_end(error, stop),
                    None,
                )
            raise

    async def _quota_recovery_step(
        self,
        pause: _QuotaPauseState,
        trigger: _SettledAttempt,
        prior_probe: QuotaProbeEvidence | None,
        stop: _DispatchGate,
        /,
    ) -> tuple[_RecoveryAction, QuotaProbeEvidence, float | None]:
        """Persist one poll and classify it against this pause's live bounds.

        Returns:
            The action, settled probe, and remaining cumulative wait.

        Raises:
            _QuotaRecoveryStopped: Stop, unknown state, or wait bounds prevent recovery.
        """
        remaining = await self._quota_wait_remaining(pause, stop)
        request = await self._schedule_quota_probe(pause, prior_probe, remaining)
        request = await self._await_probe_due(pause, request, remaining)
        remaining = self._pause_remaining(pause)
        probe = await self._poll_and_settle_probe(request, stop, pause, remaining)
        self._update_quota_elapsed(pause)
        if stop.stopped():
            raise _QuotaRecoveryStopped("dispatch stopped during quota probe", "stop")
        action = _decide_quota_recovery(self, trigger, prior_probe, probe)
        remaining = self._pause_remaining(pause)
        if remaining is not None and remaining <= 0.0:
            action = "stop"
        await self._record_quota_recheck(pause, action, probe)
        return action, probe, remaining

    def _pause_remaining(self, pause: _QuotaPauseState, /) -> float | None:
        """Return time left across all cadence and probe work in this pause."""
        elapsed = pause.cumulative_waited_before_seconds + max(
            0.0, self.runtime.monotonic() - pause.started_at_monotonic
        )
        return quota_wait_remaining(self.config, elapsed)

    def _update_quota_elapsed(self, pause: _QuotaPauseState, /) -> None:
        """Retain monotonic quota wait after every cadence, probe, and write."""
        elapsed = pause.cumulative_waited_before_seconds + max(
            0.0, self.runtime.monotonic() - pause.started_at_monotonic
        )
        self._state.quota_waited_seconds = max(
            self._state.quota_waited_seconds, elapsed
        )

    async def _start_quota_wait(self, trigger: _SettledAttempt, /) -> _QuotaPauseState:
        """Persist one pause's initial context before waiting or probing.

        Returns:
            The recorded pause state.

        Raises:
            RuntimeError: The triggering attempt has no quota observation.
        """
        observation = trigger.observation
        if observation is None:
            raise RuntimeError("quota pause has no observation")
        cumulative = self._state.quota_waited_seconds
        wait_id = _quota_pause_id(trigger)
        context = QuotaWaitContext(
            kind="quota",
            trigger_call_id=trigger.call.call_id,
            trigger_attempt_number=trigger.attempt_number,
            cumulative_waited_before_seconds=cumulative,
            wait_limit_seconds=self.config.quota_wait_limit_seconds,
            quota_observation=observation,
            selected_reset_at_utc=_latest_reset_hint(observation),
        )
        started_at_utc = self.runtime.utc_now()
        started_at_monotonic = self.runtime.monotonic()
        try:
            _, cancellation = await self._settle_write(
                self.evidence.record_wait_event(
                    WaitEvent(
                        run_id=trigger.call.run_id,
                        wait_id=wait_id,
                        context=context,
                        kind="started",
                        observed_at_utc=started_at_utc,
                        elapsed_seconds=0.0,
                        quota_observation=observation,
                        end=None,
                        diagnostic=None,
                    )
                ),
                "quota wait start",
            )
        except BaseException as error:
            self._state.recording_error = self._state.recording_error or error
            self._state.run_incomplete = True
            self._require_gate()(error)
            raise
        if cancellation is not None:
            self._state.cancellation = self._state.cancellation or cancellation
            self._require_gate()(cancellation)
            raise cancellation
        return _QuotaPauseState(
            trigger, context, wait_id, started_at_utc, started_at_monotonic, cumulative
        )

    async def _quota_wait_remaining(
        self, pause: _QuotaPauseState, stop: _DispatchGate, /
    ) -> float | None:
        """Enforce cumulative wait and probe bounds before scheduling a poll.

        Returns:
            Remaining wait seconds, or ``None`` when unbounded.

        Raises:
            _QuotaRecoveryStopped: Stop, wait, or probe limits prevent another poll.
        """
        elapsed = pause.cumulative_waited_before_seconds + max(
            0.0, self.runtime.monotonic() - pause.started_at_monotonic
        )
        remaining = quota_wait_remaining(self.config, elapsed)
        reason = (
            "dispatch was stopped during quota recovery"
            if stop.stopped()
            else "quota wait limit is exhausted"
            if remaining is not None and remaining <= 0.0
            else "quota probe budget is exhausted"
            if not quota_probe_allowed(self.config, self._state.probes_started)
            else None
        )
        if reason is not None:
            raise _QuotaRecoveryStopped(reason, "stop" if stop.stopped() else "bound")
        return remaining

    async def _schedule_quota_probe(
        self,
        pause: _QuotaPauseState,
        prior_probe: QuotaProbeEvidence | None,
        remaining: float | None,
        /,
    ) -> QuotaProbeRequest:
        """Persist one cadence decision and cap its delay to remaining wait.

        Returns:
            The scheduled quota probe request.
        """
        request = _prepare_quota_probe(self, pause.trigger, prior_probe)
        if remaining is not None and request.scheduled_wait_seconds >= remaining:
            request = request.model_copy(update={"scheduled_wait_seconds": remaining})
        self._state.probes_scheduled += 1
        try:
            _, cancellation = await self._settle_write(
                self.evidence.record_quota_probe_event(
                    QuotaProbeScheduled(kind="scheduled", schedule=request.schedule)
                ),
                "quota probe schedule",
            )
        except BaseException as error:
            self._state.recording_error = self._state.recording_error or error
            self._state.run_incomplete = True
            self._require_gate()(error)
            raise
        if cancellation is not None:
            self._state.cancellation = self._state.cancellation or cancellation
            self._require_gate()(cancellation)
            raise cancellation
        return request

    async def _await_probe_due(
        self,
        pause: _QuotaPauseState,
        request: QuotaProbeRequest,
        remaining: float | None,
        /,
    ) -> QuotaProbeRequest:
        """Await cadence, persist prelaunch cancellation, and timestamp dispatch.

        Returns:
            A request stamped with actual poll dispatch time and elapsed cadence.

        Raises:
            asyncio.CancelledError: The owner cancels the scheduled cadence.
            _QuotaRecoveryStopped: Stop or the bounded wait prevents polling.
        """
        remaining = self._pause_remaining(pause)
        if self._require_gate().stopped():
            await self._cancel_scheduled_probe(
                request, self.runtime.monotonic(), "stop"
            )
            raise _QuotaRecoveryStopped(
                "dispatch was stopped before quota probe cadence", "stop"
            )
        if remaining is not None and remaining <= 0.0:
            await self._cancel_scheduled_probe(
                request, self.runtime.monotonic(), "stop"
            )
            self._store_quota_wait_elapsed(pause)
            raise _QuotaRecoveryStopped("quota wait limit is exhausted", "bound")
        delay = (
            request.scheduled_wait_seconds
            if remaining is None
            else min(request.scheduled_wait_seconds, remaining)
        )
        request = request.model_copy(update={"scheduled_wait_seconds": delay})
        scheduled_start = self.runtime.monotonic()
        try:
            await self.runtime.sleep(delay)
        except asyncio.CancelledError:
            await self._cancel_scheduled_probe(request, scheduled_start, "cancelled")
            self._store_quota_wait_elapsed(pause)
            raise
        actual_wait = max(0.0, self.runtime.monotonic() - scheduled_start)
        if remaining is not None and actual_wait >= remaining:
            await self._cancel_scheduled_probe(request, scheduled_start, "stop")
            self._store_quota_wait_elapsed(pause)
            raise _QuotaRecoveryStopped("quota wait limit is exhausted", "bound")
        actual_started = self.runtime.utc_now()
        if (
            request.poll_started_at_utc == actual_started
            and request.scheduled_wait_seconds == actual_wait
        ):
            return request
        return request.model_copy(
            update={
                "poll_started_at_utc": actual_started,
                "scheduled_wait_seconds": actual_wait,
            }
        )

    async def _cancel_scheduled_probe(
        self,
        request: QuotaProbeRequest,
        started_at: float,
        cause: Literal["cancelled", "stop"],
        /,
    ) -> None:
        """Persist a scheduled probe cancelled before its poll invocation."""
        try:
            _, cancellation = await self._settle_write(
                self.evidence.record_quota_probe_event(
                    QuotaProbeCancelled(
                        kind="cancelled",
                        schedule=request.schedule,
                        cause=cause,
                        ended_at_utc=self.runtime.utc_now(),
                        elapsed_seconds=max(0.0, self.runtime.monotonic() - started_at),
                        elapsed_basis="monotonic",
                    )
                ),
                "quota probe prelaunch cancellation",
            )
        except BaseException as error:
            self._state.recording_error = self._state.recording_error or error
            self._state.run_incomplete = True
            self._require_gate()(error)
            raise
        if cancellation is not None:
            self._state.cancellation = self._state.cancellation or cancellation
            self._require_gate()(cancellation)
            raise cancellation

    def _store_quota_wait_elapsed(self, pause: _QuotaPauseState, /) -> None:
        """Retain cumulative monotonic wait after a prelaunch stop."""
        self._state.quota_waited_seconds = pause.cumulative_waited_before_seconds + max(
            0.0, self.runtime.monotonic() - pause.started_at_monotonic
        )

    async def _record_quota_recheck(
        self,
        pause: _QuotaPauseState,
        action: _RecoveryAction,
        probe: QuotaProbeEvidence,
        /,
    ) -> None:
        """Persist the source-backed observation before applying recovery."""
        ends: dict[_RecoveryAction, WaitEnd] = {
            "resume": "quota_available",
            "continue": "delay_elapsed",
            "stop": "unknown",
        }
        end = ends[action]
        try:
            _, cancellation = await self._settle_write(
                self.evidence.record_wait_event(
                    WaitEvent(
                        run_id=pause.trigger.call.run_id,
                        wait_id=pause.wait_id,
                        context=pause.context,
                        kind="recheck",
                        observed_at_utc=self.runtime.utc_now(),
                        elapsed_seconds=max(
                            0.0,
                            self.runtime.monotonic() - pause.started_at_monotonic,
                        ),
                        quota_observation=probe.observation,
                        end=end,
                        diagnostic=probe.classification_basis,
                    )
                ),
                "quota wait recheck",
            )
        except BaseException as error:
            self._state.recording_error = self._state.recording_error or error
            self._state.run_incomplete = True
            self._require_gate()(error)
            raise
        if cancellation is not None:
            self._state.cancellation = self._state.cancellation or cancellation
            self._require_gate()(cancellation)
            raise cancellation

    async def _finish_quota_wait(
        self,
        trigger: _SettledAttempt,
        context: QuotaWaitContext,
        wait_id: str,
        started_at_utc: str,
        started_at_monotonic: float,
        end: Literal["quota_available", "bound", "cancelled", "stop", "unknown"],
        observation: QuotaObservation | None,
        /,
    ) -> None:
        """Persist the final quota wait event before retaining its summary."""
        ended = self.runtime.utc_now()
        elapsed = max(0.0, self.runtime.monotonic() - started_at_monotonic)
        try:
            _, cancellation = await self._settle_write(
                self.evidence.record_wait_event(
                    WaitEvent(
                        run_id=trigger.call.run_id,
                        wait_id=wait_id,
                        context=context,
                        kind="finished",
                        observed_at_utc=ended,
                        elapsed_seconds=elapsed,
                        quota_observation=observation,
                        end=end,
                        diagnostic=None,
                    )
                ),
                "quota wait finish",
            )
        except BaseException as error:
            self._state.recording_error = self._state.recording_error or error
            self._state.run_incomplete = True
            self._require_gate()(error)
            raise
        if cancellation is not None:
            self._state.cancellation = self._state.cancellation or cancellation
            self._require_gate()(cancellation)
            raise cancellation
        self._state.waits.append(
            WaitRecord(
                wait_id=wait_id,
                context=context,
                started_at_utc=started_at_utc,
                ended_at_utc=ended,
                elapsed_seconds=elapsed,
                end=end,
                diagnostic=None,
            )
        )

    async def _poll_and_settle_probe(  # ruff: ignore[too-many-statements]
        self,
        request: QuotaProbeRequest,
        stop: _DispatchGate,
        pause: _QuotaPauseState,
        remaining: float | None,
        /,
    ) -> QuotaProbeEvidence:
        """Persist the start and settlement around one supervised poll.

        Returns:
            The quota probe evidence returned by the reader.

        Raises:
            _QuotaRecoveryStopped: A stop gate prevents starting the probe.
        """
        if stop.stopped():
            await self._cancel_scheduled_probe(
                request, self.runtime.monotonic(), "stop"
            )
            raise _QuotaRecoveryStopped(
                "dispatch stopped before quota probe start", "stop"
            )
        try:
            _, cancellation = await self._settle_write(
                self.evidence.record_quota_probe_event(
                    QuotaProbeStarted(kind="started", request=request)
                ),
                "quota probe start",
            )
        except BaseException as error:
            self._state.recording_error = self._state.recording_error or error
            self._state.run_incomplete = True
            stop(error)
            raise
        if cancellation is not None:
            self._state.cancellation = self._state.cancellation or cancellation
            stop(cancellation)
            self._retain_unsettled_probe_start()
            raise cancellation
        if stop.stopped():
            self._retain_unsettled_probe_start()
            raise _QuotaRecoveryStopped("dispatch stopped during probe start", "stop")
        self._state.probes_started += 1
        self._state.active_probes += 1
        self._publish_progress("quota_paused")
        try:
            if remaining is None:
                probe = await self.quota_status.poll(request, stop)
            else:
                async with asyncio.timeout(remaining):
                    probe = await self.quota_status.poll(request, stop)
        except BaseException as error:
            await self._settle_failed_probe(error, request, stop)
            if isinstance(error, TimeoutError):
                raise _QuotaRecoveryStopped(
                    "quota probe exceeded the cumulative wait limit", "bound"
                ) from error
            raise
        return await self._settle_successful_probe(probe, pause, stop)

    def _retain_unsettled_probe_start(self) -> None:
        """Keep a started lifecycle without fabricating an absent settlement."""
        self._state.probes_started += 1
        self._state.pending_probes += 1
        self._state.run_incomplete = True
        self._publish_progress("stopping")

    async def _settle_failed_probe(
        self,
        error: BaseException,
        request: QuotaProbeRequest,
        stop: _DispatchGate,
        /,
    ) -> None:
        """Persist failed poll evidence and retain its original control flow."""
        stop(error)
        self._state.active_probes -= 1
        owner_cancellation, persisted = await self._record_probe_after_failure(
            error, request
        )
        if persisted:
            if isinstance(error, asyncio.CancelledError):
                self._state.probes_cancelled += 1
            else:
                self._state.probes_failed += 1
        self._publish_progress("quota_paused")
        if owner_cancellation is not None:
            if isinstance(error, asyncio.CancelledError):
                error.add_note(
                    "Additional owner cancellation arrived while preserving "
                    "the probe cancellation"
                )
                raise error
            owner_cancellation.add_note(
                f"Quota probe failed while settling evidence: {error!r}"
            )
            raise owner_cancellation from error

    async def _settle_successful_probe(
        self,
        probe: QuotaProbeEvidence,
        pause: _QuotaPauseState,
        stop: _DispatchGate,
        /,
    ) -> QuotaProbeEvidence:
        """Persist returned probe evidence and update passive progress counts.

        Returns:
            The settled probe evidence.
        """
        self._state.active_probes -= 1
        self._state.pending_probes += 1
        self._publish_progress("quota_paused")
        try:
            _, cancellation = await self._settle_write(
                self.evidence.record_quota_probe_settled(probe),
                "quota probe settlement",
            )
        except BaseException as error:
            self._state.recording_error = self._state.recording_error or error
            self._state.run_incomplete = True
            stop(error)
            raise
        self._state.pending_probes -= 1
        self._retain_quota_observation(probe.observation)
        if cancellation is not None:
            self._state.cancellation = self._state.cancellation or cancellation
            stop(cancellation)
        if probe.quota_state in {"available", "exhausted"} and _probe_process_is_safe(
            probe
        ):
            self._state.probes_completed += 1
        else:
            self._state.probes_failed += 1
        self._update_quota_elapsed(pause)
        self._publish_progress("quota_paused")
        if cancellation is not None:
            raise cancellation
        return probe

    async def _record_probe_after_failure(
        self, error: BaseException, request: QuotaProbeRequest, /
    ) -> tuple[asyncio.CancelledError | None, bool]:
        """Persist attached evidence and report cancellation during settlement.

        Returns:
            Cancellation delivered to this owner while the evidence write settled.
            Whether attached probe evidence was durably persisted.
        """
        probe = quota_probe_evidence(error, request)
        if probe is None:
            self._state.pending_probes += 1
            self._state.run_incomplete = True
            return None, False
        self._state.pending_probes += 1
        try:
            _, owner_cancellation = await self._settle_write(
                self.evidence.record_quota_probe_settled(probe),
                "quota probe failure settlement",
            )
        except BaseException as persistence_error:
            error.add_note(
                f"Quota probe evidence could not be persisted: {persistence_error!r}"
            )
            self._state.recording_error = (
                self._state.recording_error or persistence_error
            )
            self._state.run_incomplete = True
            return None, False
        self._state.pending_probes -= 1
        self._retain_quota_observation(probe.observation)
        return owner_cancellation, True


def _prepare_quota_probe(
    coordinator: Coordinator,
    trigger: _SettledAttempt,
    prior_probe: QuotaProbeEvidence | None,
    /,
) -> QuotaProbeRequest:
    """Schedule one scoped probe from a reset hint or periodic interval.

    Returns:
        A durably identifiable probe due at the earlier hint or poll interval.

    Raises:
        RuntimeError: The settled exhaustion observation lacks verified scope.
    """
    trigger_observation = trigger.observation
    observation = (
        prior_probe.observation
        if prior_probe is not None
        and prior_probe.observation is not None
        and trigger_observation is not None
        and prior_probe.observation.scope == trigger_observation.scope
        and prior_probe.quota_state == "exhausted"
        else trigger_observation
    )
    scope = coordinator.bound_run.binding.quota_scope
    if observation is None or scope is None or observation.scope != scope:
        raise RuntimeError("quota probe requires a scoped exhaustion observation")
    now = coordinator.runtime.utc_now()
    hint = _latest_reset_hint(observation)
    delay = quota_poll_delay(coordinator.config.quota_poll_interval_seconds, now, hint)
    reason = (
        "reset_hint"
        if hint is not None and delay < coordinator.config.quota_poll_interval_seconds
        else "periodic"
    )
    created = datetime.fromisoformat(now.replace("Z", "+00:00"))
    due_at = (
        datetime
        .fromtimestamp(created.timestamp() + delay, UTC)
        .isoformat()
        .replace("+00:00", "Z")
    )
    ordinal = coordinator._state.probes_scheduled + 1
    schedule = QuotaProbeSchedule(
        run_id=trigger.call.run_id,
        probe_id=QuotaProbeId(f"{trigger.call.run_id}-quota-{ordinal}"),
        scope=scope,
        reason=reason,
        created_at_utc=now,
        due_at_utc=due_at,
        interval_seconds=coordinator.config.quota_poll_interval_seconds,
        reset_hint_at_utc=hint,
    )
    return QuotaProbeRequest(
        schedule=schedule,
        pause_wait_id=_quota_pause_id(trigger),
        poll_started_at_utc=due_at,
        scheduled_wait_seconds=delay,
        scheduled_wait_elapsed_basis="monotonic",
    )


def _decide_quota_recovery(
    coordinator: Coordinator,
    trigger: _SettledAttempt,
    prior_probe: QuotaProbeEvidence | None,
    probe: QuotaProbeEvidence,
    /,
) -> _RecoveryAction:
    """Resume only from fresh scoped availability for the current pause.

    Returns:
        Continue, resume, or stop according to the settled probe facts.
    """
    del prior_probe
    observation = probe.observation
    scope = coordinator.bound_run.binding.quota_scope
    pause_id = _quota_pause_id(trigger)
    if observation is None or scope is None or observation.scope != scope:
        return "stop"
    if probe.request.pause_wait_id != pause_id:
        return "stop"
    if not _probe_process_is_safe(probe):
        return "stop"
    if probe.quota_state == "exhausted":
        return "continue"
    if probe.quota_state != "available" or not observation.windows:
        return "stop"
    if any(window.state != "available" for window in observation.windows):
        return "stop"
    observed = tuple(window.source_observed_at_utc for window in observation.windows)
    source_value = observed[0]
    if source_value is None or any(value != source_value for value in observed):
        return "stop"
    source_at = datetime.fromisoformat(source_value.replace("Z", "+00:00"))
    started = datetime.fromisoformat(
        probe.request.poll_started_at_utc.replace("Z", "+00:00")
    )
    ended = probe.process.ended_at_utc
    if (
        ended is None
        or source_at < started
        or source_at > datetime.fromisoformat(ended.replace("Z", "+00:00"))
    ):
        return "stop"
    return "resume"


def _probe_process_is_safe(probe: QuotaProbeEvidence, /) -> bool:
    """Require normal completion and safe cleanup before interpreting quota.

    Returns:
        Whether the probe evidence permits interpreting its quota observation.
    """
    outcome = probe.process.outcome
    if probe.process.control_flow != "returned" or not isinstance(outcome, Completed):
        return False
    if outcome.exit_status != 0 and probe.quota_state != "exhausted":
        return False
    return outcome.observation.cleanup.dispatch_permitted


def _quota_pause_id(trigger: _SettledAttempt, /) -> str:
    """Build a pause identity unique to a call and triggering attempt.

    Returns:
        The pause lifecycle key.
    """
    return f"{trigger.call.call_id}:quota:{trigger.attempt_number}"


def _quota_wait_end(
    error: BaseException, stop: _DispatchGate, /
) -> Literal["bound", "cancelled", "stop", "unknown"]:
    """Project the exception and live stop latch into a persisted wait ending.

    Returns:
        The ending appropriate to the settled wait.
    """
    if isinstance(error, asyncio.CancelledError):
        return "cancelled"
    if isinstance(error, _QuotaRecoveryStopped):
        return error.end
    if isinstance(error, TimeoutError):
        return "bound"
    return "stop" if stop.stopped() else "unknown"


def _capture_returned_attempt(
    call: EffectiveCall,
    outcome: AttemptResult,
    started_at: str,
    ended_at: str,
    /,
) -> AttemptEvidence:
    """Capture a returned supervisor outcome as typed attempt evidence.

    Returns:
        Exact control, request, timestamp, and any typed infrastructure facts.
    """
    return AttemptEvidence(
        control_flow="returned",
        outcome=outcome,
        error_type=(
            outcome.error_type if isinstance(outcome, InfrastructureFailure) else None
        ),
        diagnostic=(
            outcome.diagnostic if isinstance(outcome, InfrastructureFailure) else None
        ),
        request=call.request,
        started_at_utc=started_at,
        ended_at_utc=ended_at,
        usage_telemetry=_captured_stdout(outcome),
    )


def _captured_stdout(
    outcome: AttemptResult | AttemptCancelled | AttemptFailureEvidence | None, /
) -> bytes | None:
    """Return exact captured stdout used by thread-scoped quota correlation."""
    if outcome is None:
        return None
    output = outcome.observation.output
    return None if output is None else output.stdout


def _latest_reset_hint(observation: QuotaObservation, /) -> str | None:
    """Select the latest known reset among exhausted quota windows.

    Returns:
        The latest source-provided hint, or ``None`` when unavailable.
    """
    hints = tuple(
        window.reset_at_utc
        for window in observation.windows
        if window.state == "exhausted" and window.reset_at_utc is not None
    )
    return max(hints) if hints else None


def _retry_reason(
    assessment: RetryAssessment | None,
    retries_used: int,
    config: HarnessConfig,
    /,
) -> _RetryReason | None:
    """Return the one exhausted-attempt category still eligible for retry.

    Returns:
        Infrastructure, capacity, or no remaining eligible retry category.
    """
    if assessment is None:
        return None
    if infrastructure_retry_allowed(assessment, retries_used, config):
        return "infrastructure"
    if capacity_retry_allowed(assessment, retries_used, config):
        return "capacity"
    return None


def _call_status(
    settled: _SettledAttempt, /
) -> Literal["complete", "failed", "cancelled"]:
    """Project one latest outcome into the supported call-state schema.

    Returns:
        The truthful terminal status for the last settled attempt.
    """
    if settled.evidence.control_flow == "cancelled":
        return "cancelled"
    if _successful_attempt(settled):
        return "complete"
    return "failed"


def _successful_attempt(settled: _SettledAttempt, /) -> bool:
    """Require normal zero-exit completion and supervisor-permitted dispatch.

    Returns:
        Whether this settled outcome succeeded operationally.
    """
    outcome = settled.evidence.outcome
    return (
        settled.evidence.control_flow == "returned"
        and isinstance(outcome, Completed)
        and outcome.exit_status == 0
        and outcome.observation.cleanup.dispatch_permitted
    )


def _attempt_record_successful(record: AttemptRecord, /) -> bool:
    """Require persisted completion, zero exit, and known-safe cleanup facts.

    Returns:
        Whether persisted process facts prove operational success.
    """
    cleanup = record.cleanup
    return (
        record.control_flow == "returned"
        and record.outcome_kind == "completed"
        and record.exit_status == 0
        and cleanup is not None
        and cleanup.process == "owned"
        and cleanup.direct_wait == "reaped"
        and cleanup.wait_diagnostic is None
        and all(
            signal.outcome in {"sent", "no_target"} and signal.diagnostic is None
            for signal in cleanup.signals
        )
    )


def _final_progress_status(
    phase: Literal["running", "quota_paused", "stopping", "final"],
    counts: ProgressCounts,
    state: _CoordinatorState,
    /,
) -> Literal["success", "failure", "cancelled", "incomplete_evidence"] | None:
    """Classify final progress after checking cancellation and evidence gates.

    Returns:
        A final status, or ``None`` for an intermediate snapshot.
    """
    if phase != "final":
        return None
    if state.cancellation is not None or counts.calls_cancelled:
        return "cancelled"
    if (
        state.run_incomplete
        or state.raised_error is not None
        or state.recording_error is not None
    ):
        return "incomplete_evidence"
    if counts.calls_stopped_not_started:
        return "incomplete_evidence"
    if counts.calls_evidence_pending or counts.attempts_evidence_pending:
        return "incomplete_evidence"
    if counts.probes_evidence_pending:
        return "incomplete_evidence"
    return "failure" if counts.calls_failed else "success"


def _dispatch_safe(settled: _SettledAttempt, /) -> bool:
    """Require observed cleanup that proves another child may be acquired.

    Returns:
        Whether the supervisor's cleanup permits later dispatch.
    """
    outcome = settled.evidence.outcome
    observation = getattr(outcome, "observation", None)
    return (
        settled.evidence.control_flow == "returned"
        and observation is not None
        and observation.cleanup.dispatch_permitted
        and not isinstance(outcome, OutputLimitExceeded)
    )


def _attempt_evidence_dispatch_safe(evidence: AttemptEvidence, /) -> bool:
    """Latch stop before releasing process capacity when cleanup is uncertain.

    Returns:
        Whether cleanup permits later dispatch.
    """
    outcome = evidence.outcome
    observation = getattr(outcome, "observation", None)
    return (
        evidence.control_flow == "returned"
        and observation is not None
        and observation.cleanup.dispatch_permitted
        and not isinstance(outcome, OutputLimitExceeded)
    )


def _quota_retry_eligible(settled: _SettledAttempt, /) -> bool:
    """Retry only a confidently absent semantic result after quota recovery.

    Returns:
        Whether quota policy permits another evaluation attempt.
    """
    assessment = settled.record.retry_assessment
    return (
        assessment is not None
        and assessment.retry_class == "quota"
        and assessment.no_result_basis == "confident_absence"
        and not _successful_attempt(settled)
    )


def _assemble_run_record(coordinator: Coordinator) -> RunRecord:
    """Build call accounting from the plan and successfully persisted attempts.

    Returns:
        A complete run record with an entry for every frozen call position.
    """
    from script.eval.model import CallRecord

    records = tuple(
        CallRecord(
            run_id=call.run_id,
            call_id=call.call_id,
            position=call.planned_call.position,
            state=(
                "not_started"
                if not coordinator._state.attempts.get(call.planned_call.position)
                and call.planned_call.position
                not in coordinator._state.started_positions
                else "failed"
                if not coordinator._state.attempts.get(call.planned_call.position)
                else "complete"
                if _attempt_record_successful(
                    coordinator._state.attempts[call.planned_call.position][-1]
                )
                else "failed"
            ),
            source_paths=tuple(
                coordinator.bound_run.plan.snapshots[index].repository_path
                for index in call.planned_call.context_indices
            ),
            source_sha256=tuple(
                coordinator.bound_run.plan.snapshots[index].content_sha256
                for index in call.planned_call.context_indices
            ),
            boundary_bytes_hex=tuple(
                value.hex() for value in coordinator.bound_run.plan.boundary_bytes
            ),
            prompt_sha256=call.planned_call.prompt_sha256,
            model=call.planned_call.model,
            effort=call.planned_call.effort,
            effective_settings_sha256=sha256(
                repr(coordinator.bound_run.binding.effective_settings).encode()
            ).hexdigest(),
            attempts=tuple(
                coordinator._state.attempts.get(call.planned_call.position, ())
            ),
        )
        for call in coordinator.bound_run.calls
    )
    return RunRecord(
        run_id=coordinator.bound_run.plan.run_id,
        repository_root=str(coordinator.bound_run.plan.repository_root),
        head_commit=coordinator.bound_run.plan.head_commit,
        state=(
            "complete"
            if len(coordinator._state.attempts) == len(coordinator.bound_run.calls)
            and coordinator._state.cancellation is None
            and coordinator._state.raised_error is None
            and coordinator._state.recording_error is None
            and not coordinator._state.run_incomplete
            else "incomplete"
        ),
        runner_version=coordinator.bound_run.binding.runner_version,
        codex_path=str(coordinator.bound_run.binding.executable_path),
        cli_version=coordinator.bound_run.binding.cli_version,
        effective_settings=coordinator.bound_run.binding.effective_settings,
        calls=records,
        waits=tuple(coordinator._state.waits),
    )
