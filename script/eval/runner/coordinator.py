# SPDX-License-Identifier: Apache-2.0
"""Schedule bounded evaluation calls and persist their execution evidence."""

import asyncio
from collections.abc import Callable, Coroutine
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
from typing import Literal, assert_never

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
    AttemptResult,
    Completed,
    DispatchStop,
    InfrastructureFailure,
    OutputLimitExceeded,
    TimedOut,
    failure_evidence,
)

type CaptureReturnedAttempt = Callable[
    [EffectiveCall, AttemptResult, str, str], AttemptEvidence
]
type _RecoveryAction = Literal["continue", "resume", "stop"]
type _RetryReason = Literal["infrastructure", "capacity"]


@dataclass(frozen=True)
class _SettledAttempt:
    """One durable attempt and its optional passive quota observation."""

    call: EffectiveCall
    attempt_number: AttemptNumber
    evidence: AttemptEvidence
    record: AttemptRecord
    observation: QuotaObservation | None


@dataclass(frozen=True)
class _DispatchAttempt:
    """Select one planned call attempt for coordinator-owned execution."""

    call: EffectiveCall
    attempt_number: AttemptNumber


@dataclass(frozen=True)
class _QuotaPaused:
    """Select quota recovery after a settled attempt blocks further dispatch."""

    trigger: _SettledAttempt


@dataclass(frozen=True)
class _QuotaPauseState:
    """One persisted pause with its monotonic start and cumulative bound."""

    trigger: _SettledAttempt
    context: QuotaWaitContext
    wait_id: str
    started_at_utc: str
    started_at_monotonic: float
    cumulative_waited_before_seconds: float


@dataclass(frozen=True)
class _DispatchComplete:
    """Finish dispatch with the run record assembled by its policy owner."""

    record: RunRecord


type _DispatchDecision = _DispatchAttempt | _QuotaPaused | _DispatchComplete
type _SelectDispatch = Callable[
    ["Coordinator", _SettledAttempt | None, DispatchStop],
    Coroutine[None, None, _DispatchDecision],
]
type _PrepareQuotaProbe = Callable[
    ["Coordinator", _SettledAttempt, QuotaProbeEvidence | None],
    Coroutine[None, None, QuotaProbeRequest],
]
type _DecideQuotaRecovery = Callable[
    [
        "Coordinator",
        _SettledAttempt,
        QuotaProbeEvidence | None,
        QuotaProbeEvidence,
    ],
    Coroutine[None, None, _RecoveryAction],
]


@dataclass
class _DispatchGate:
    """Latch the first supervisor or coordinator stop reason."""

    reason: AttemptResult | BaseException | None = None

    def __call__(self, reason: AttemptResult | BaseException, /) -> None:
        """Retain the first reason that forbids later attempt dispatch."""
        if self.reason is None:
            self.reason = reason

    def stopped(self) -> bool:
        """Report whether the run has latched a stop reason.

        Returns:
            Whether dispatch remains stopped.
        """
        return self.reason is not None


@dataclass
class _CoordinatorState:
    """Mutable execution facts retained by one otherwise frozen coordinator."""

    next_position: int = 0
    attempts: dict[int, list[AttemptRecord]] = field(default_factory=dict)
    waits: list[WaitRecord] = field(default_factory=list)
    statuses: dict[
        int,
        Literal["queued", "running", "retry_wait", "complete", "failed", "cancelled"],
    ] = field(default_factory=dict)
    quota_observation: QuotaObservation | None = None
    retry_reasons: dict[RetryClass, int] = field(default_factory=dict)
    quota_waited_seconds: float = 0.0
    probes_started: int = 0
    settled: dict[int, _SettledAttempt] = field(default_factory=dict)
    call_waits: dict[int, CallWait] = field(default_factory=dict)
    cancellation: asyncio.CancelledError | None = None
    raised_error: BaseException | None = None
    active_attempts: dict[int, AttemptNumber] = field(default_factory=dict)
    active_probes: int = 0
    probes_completed: int = 0
    probes_failed: int = 0
    probes_cancelled: int = 0
    quota_trigger: _SettledAttempt | None = None
    deferred_retries: list[tuple[EffectiveCall, AttemptNumber]] = field(
        default_factory=list
    )


@dataclass(frozen=True)
class Coordinator:
    """Own one bound run's bounded dispatch, retries, recovery, and accounting.

    The default scheduler executes independent matrix calls concurrently within
    the configured limit. Injected selection remains available for focused
    policy wiring tests.
    """

    bound_run: BoundRun
    evidence: EvidenceStore
    attempt: AttemptCall
    classifier: OutcomeClassifier
    quota_status: QuotaStatusReader
    runtime: Runtime
    progress: ProgressSink
    select_dispatch: _SelectDispatch = field(default_factory=lambda: _select_dispatch)
    prepare_quota_probe: _PrepareQuotaProbe = field(
        default_factory=lambda: _prepare_quota_probe
    )
    decide_quota_recovery: _DecideQuotaRecovery = field(
        default_factory=lambda: _decide_quota_recovery
    )
    capture_returned_attempt: CaptureReturnedAttempt = field(
        default_factory=lambda: _capture_returned_attempt
    )
    _state: _CoordinatorState = field(default_factory=_CoordinatorState, compare=False)

    @property
    def config(self) -> HarnessConfig:
        """Configuration frozen into this coordinator's plan."""
        return self.bound_run.plan.configuration

    async def run(self) -> RunRecord:
        """Run selected effects and finalize the record they return.

        Returns:
            The finalized run record.

        Raises:
            ValueError: Dry-run plans must return through the reporting path.
        """
        if self.config.dry_run:
            raise ValueError("dry-run plans do not enter the coordinator")
        record = await self._dispatch()
        await self.evidence.finalize(record)
        self._publish_progress("final")
        if self._state.cancellation is not None:
            raise self._state.cancellation
        if self._state.raised_error is not None:
            raise self._state.raised_error
        return record

    async def _dispatch(self) -> RunRecord:
        """Execute selector decisions and retain durable attempt state.

        Returns:
            The completed run record.

        Raises:
            RuntimeError: A decision conflicts with the stop or pause state.
        """
        if self.select_dispatch is _select_dispatch:
            return await self._dispatch_bounded()
        stop = _DispatchGate()
        settled: _SettledAttempt | None = None
        while True:
            decision = await self.select_dispatch(self, settled, stop)
            match decision:
                case _DispatchAttempt(call, attempt_number):
                    if stop.stopped():
                        raise RuntimeError("dispatch was stopped before this attempt")
                    settled = await self._execute_attempt(call, attempt_number, stop)
                case _QuotaPaused(trigger):
                    await self._await_recovery_for_pause(trigger, settled, stop)
                    settled = None
                case _DispatchComplete(record):
                    if stop.stopped():
                        raise RuntimeError("dispatch was stopped before completion")
                    return record
                case unreachable:
                    assert_never(unreachable)

    async def _dispatch_bounded(self) -> RunRecord:
        """Run independent calls under the configured concurrency ceiling.

        Each completed attempt releases its slot before retry policy or wait
        work runs. Any unsafe outcome latches the shared stop before remaining
        tasks are cancelled and awaited.

        Returns:
            Final accounting for every scheduled position.
        """
        stop = _DispatchGate()
        pending: dict[asyncio.Task[_SettledAttempt], EffectiveCall] = {}
        semaphore = asyncio.Semaphore(self.config.concurrency)
        try:
            return await self._schedule_calls(pending, stop, semaphore)
        except BaseException as error:
            return await self._stop_bounded_run(error, stop, pending)

    async def _schedule_calls(
        self,
        pending: dict[asyncio.Task[_SettledAttempt], EffectiveCall],
        stop: _DispatchGate,
        semaphore: asyncio.Semaphore,
        /,
    ) -> RunRecord:
        """Fill slots, settle attempts, and await any global quota pause.

        Returns:
            A run record accounting for every scheduled position.
        """
        next_index = 0
        quota_paused = False
        while next_index < len(self.bound_run.calls) or pending:
            next_index = self._launch_pending(
                next_index, pending, semaphore, stop, quota_paused
            )
            if not pending:
                if next_index < len(self.bound_run.calls) and not stop.stopped():
                    continue
                break
            done, _ = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            quota_paused |= await self._settle_completed(done, pending, semaphore, stop)
            if quota_paused and not pending:
                if not await self._recover_quota_pause(stop, pending, semaphore):
                    break
                quota_paused = False
        return _assemble_run_record(self)

    async def _recover_quota_pause(
        self,
        stop: _DispatchGate,
        pending: dict[asyncio.Task[_SettledAttempt], EffectiveCall],
        semaphore: asyncio.Semaphore,
        /,
    ) -> bool:
        """Recover or stop after the global pause settles all attempts.

        Returns:
            Whether recovery confirmed availability and permits dispatch.
        """
        trigger = self._state.quota_trigger
        if trigger is None:
            trigger = next(
                item for item in self._settled_attempts() if self._quota_exhausted(item)
            )
        try:
            await self._wait_for_quota(trigger, stop)
        except RuntimeError as reason:
            stop(reason)
            return False
        self._state.quota_trigger = None
        self._dispatch_deferred_retries(pending, semaphore, stop)
        self._publish_progress("running")
        return True

    async def _stop_bounded_run(
        self,
        error: BaseException,
        stop: _DispatchGate,
        pending: dict[asyncio.Task[_SettledAttempt], EffectiveCall],
        /,
    ) -> RunRecord:
        """Latch stop, settle tasks, and preserve cancellation accounting.

        Returns:
            Incomplete accounting after cancellation.

        """
        stop(error)
        if isinstance(error, asyncio.CancelledError):
            self._state.cancellation = error
        self._publish_progress("stopping")
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
        if not isinstance(error, asyncio.CancelledError):
            raise error
        for position, status in self._state.statuses.items():
            if status == "retry_wait":
                self._state.statuses[position] = "cancelled"
        for call in pending.values():
            self._state.statuses[call.planned_call.position] = "cancelled"
        return _assemble_run_record(self)

    def _launch_pending(
        self,
        next_index: int,
        pending: dict[asyncio.Task[_SettledAttempt], EffectiveCall],
        semaphore: asyncio.Semaphore,
        stop: _DispatchGate,
        quota_paused: bool,
        /,
    ) -> int:
        """Fill free slots from the ordered plan unless a run gate is latched.

        Returns:
            The next not-yet-launched plan position.
        """
        while (
            not quota_paused
            and self._state.quota_trigger is None
            and not stop.stopped()
            and next_index < len(self.bound_run.calls)
            and len(pending) < self.config.concurrency
        ):
            call = self.bound_run.calls[next_index]
            next_index += 1
            self._state.statuses[call.planned_call.position] = "running"
            task = asyncio.create_task(
                self._run_bounded_attempt(call, 1, semaphore, stop),
                name=f"eval-call-{call.planned_call.position}",
            )
            pending[task] = call
            self._publish_progress("running")
        return next_index

    def _dispatch_deferred_retries(
        self,
        pending: dict[asyncio.Task[_SettledAttempt], EffectiveCall],
        semaphore: asyncio.Semaphore,
        stop: _DispatchGate,
        /,
    ) -> None:
        """Resume waits already released from their call slots after quota clears."""
        for call, attempt_number in self._state.deferred_retries:
            self._state.statuses[call.planned_call.position] = "running"
            task = asyncio.create_task(
                self._run_bounded_attempt(call, attempt_number, semaphore, stop),
                name=f"eval-retry-{call.planned_call.position}-{attempt_number}",
            )
            pending[task] = call
        self._state.deferred_retries.clear()

    async def _settle_completed(
        self,
        done: set[asyncio.Task[_SettledAttempt]],
        pending: dict[asyncio.Task[_SettledAttempt], EffectiveCall],
        semaphore: asyncio.Semaphore,
        stop: _DispatchGate,
        /,
    ) -> bool:
        """Record completed calls and report whether quota recovery is needed.

        Returns:
            Whether a settled call established a global quota pause.
        """
        quota_paused = False
        for task in done:
            call = pending.pop(task)
            try:
                settled = task.result()
            except BaseException as error:
                stop(error)
                raise
            settled, paused = await self._retry_call(call, settled, semaphore, stop)
            quota_paused = quota_paused or paused
            self._state.statuses[call.planned_call.position] = (
                "failed" if paused else _call_status(settled)
            )
            self._publish_progress("quota_paused" if quota_paused else "running")
        return quota_paused

    async def _retry_call(
        self,
        call: EffectiveCall,
        settled: _SettledAttempt,
        semaphore: asyncio.Semaphore,
        stop: _DispatchGate,
        /,
    ) -> tuple[_SettledAttempt, bool]:
        """Apply retry policies after safe durable settlement.

        Returns:
            The last settled attempt and whether it triggered quota recovery.
        """
        while self._retry_is_safe(settled):
            if self._quota_exhausted(settled):
                return settled, True
            assessment = settled.record.retry_assessment
            attempts_used = settled.attempt_number
            reason = _retry_reason(assessment, attempts_used, self.config)
            if reason is None:
                break
            self._state.retry_reasons[reason] = (
                self._state.retry_reasons.get(reason, 0) + 1
            )
            self._state.statuses[call.planned_call.position] = "retry_wait"
            self._publish_progress("running")
            if reason == "capacity":
                await self._wait_capacity(settled, stop)
            if self._state.quota_trigger is not None:
                self._state.deferred_retries.append((call, attempts_used + 1))
                return settled, True
            settled = await self._run_bounded_attempt(
                call, attempts_used + 1, semaphore, stop
            )
        return settled, False

    async def _run_bounded_attempt(
        self,
        call: EffectiveCall,
        attempt_number: AttemptNumber,
        semaphore: asyncio.Semaphore,
        stop: _DispatchGate,
        /,
    ) -> _SettledAttempt:
        """Hold a concurrency slot through cleanup and evidence.

        Returns:
            The settled attempt after its required evidence is durable.
        """
        async with semaphore:
            position = call.planned_call.position
            self._state.active_attempts[position] = attempt_number
            self._publish_progress("running")
            try:
                settled = await self._execute_attempt(call, attempt_number, stop)
            finally:
                self._state.active_attempts.pop(position, None)
            observation = getattr(settled.evidence.outcome, "observation", None)
            if (
                isinstance(
                    settled.evidence.outcome, (AttemptCancelled, OutputLimitExceeded)
                )
                or observation is None
                or not observation.cleanup.dispatch_permitted
            ):
                stop(RuntimeError("attempt did not settle with dispatch permitted"))
            return settled

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

    def _settled_attempts(self) -> tuple[_SettledAttempt, ...]:
        """Return the latest settled attempt per call.

        Returns:
            Settled values in planned-position order.
        """
        return tuple(self._state.settled.values())

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

    async def _wait_capacity(
        self, settled: _SettledAttempt, stop: _DispatchGate, /
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
        index = max(0, settled.attempt_number - 1)
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
        await self.evidence.record_wait_event(
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
        )
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
        except asyncio.CancelledError:
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
        await self.evidence.record_wait_event(
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
        )
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
        successful_attempts = sum(
            record.exit_status == 0
            and record.cleanup is not None
            and record.cleanup.process == "owned"
            and record.cleanup.direct_wait == "reaped"
            for record in attempts
        )
        cancelled_attempts = sum(
            record.outcome_kind == "cancelled" for record in attempts
        )
        counts = ProgressCounts(
            calls_queued=0 if phase == "final" else states.count("queued"),
            calls_stopped_not_started=(
                states.count("queued") if phase == "final" else 0
            ),
            calls_active=states.count("running"),
            calls_retry_wait=states.count("retry_wait"),
            calls_evidence_pending=0,
            calls_succeeded=states.count("complete"),
            calls_failed=states.count("failed"),
            calls_cancelled=states.count("cancelled"),
            attempts_started=len(attempts) + len(self._state.active_attempts),
            retries_started=(
                sum(len(records) - 1 for records in self._state.attempts.values())
                + sum(number > 1 for number in self._state.active_attempts.values())
            ),
            attempts_active=len(self._state.active_attempts),
            attempts_evidence_pending=0,
            attempts_succeeded=successful_attempts,
            attempts_failed=len(attempts) - successful_attempts - cancelled_attempts,
            attempts_cancelled=cancelled_attempts,
            probes_started=(
                self._state.probes_completed
                + self._state.probes_failed
                + self._state.probes_cancelled
                + self._state.active_probes
            ),
            probes_active=self._state.active_probes,
            probes_evidence_pending=0,
            probes_completed=self._state.probes_completed,
            probes_failed=self._state.probes_failed,
            probes_cancelled=self._state.probes_cancelled,
        )
        final_status = None
        if phase == "final":
            final_status = (
                "cancelled"
                if self._state.cancellation is not None or counts.calls_cancelled
                else "incomplete_evidence"
                if counts.calls_stopped_not_started
                else "failure"
                if counts.calls_failed
                else "success"
            )
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

    async def _await_recovery_for_pause(
        self,
        trigger: _SettledAttempt,
        settled: _SettledAttempt | None,
        stop: _DispatchGate,
        /,
    ) -> None:
        """Validate the latest pause decision and await its recovery flow.

        Raises:
            RuntimeError: Recovery is disabled or the pause is no longer current.
        """
        if not self.config.quota_wait_enabled:
            raise RuntimeError("quota recovery is disabled")
        if stop.stopped():
            raise RuntimeError("dispatch was stopped before quota recovery")
        if trigger is not settled:
            raise RuntimeError("quota recovery requires the latest settled attempt")
        await self._wait_for_quota(trigger, stop)

    async def _execute_attempt(
        self,
        call: EffectiveCall,
        attempt_number: AttemptNumber,
        stop: DispatchStop,
        /,
    ) -> _SettledAttempt:
        """Run and durably record an attempt before passive quota ingestion.

        Returns:
            The settled attempt and its passive quota observation, if enabled.
        """
        started_at = self.runtime.utc_now()
        attempt_evidence = await self._capture_attempt(call, stop, started_at)
        attempt_record = await self._record_attempt(
            call, attempt_number, attempt_evidence
        )
        observation = await self._observe_attempt(
            call, attempt_number, attempt_evidence
        )
        return self._retain_settled(
            call, attempt_number, attempt_evidence, attempt_record, observation
        )

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
        stop: DispatchStop,
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
        cancellation: AttemptCancelled,
        started_at: str,
        stop: DispatchStop,
        /,
    ) -> AttemptEvidence:
        """Retain supervisor cancellation facts for final cancellation reporting.

        Returns:
            Typed cancelled attempt evidence.
        """
        self._state.cancellation = cancellation
        stop(cancellation)
        return AttemptEvidence(
            control_flow="cancelled",
            outcome=cancellation,
            error_type=None,
            diagnostic=None,
            request=call.request,
            started_at_utc=started_at,
            ended_at_utc=self.runtime.utc_now(),
            usage_telemetry=None,
        )

    def _capture_failed_attempt(
        self,
        call: EffectiveCall,
        error: BaseException,
        started_at: str,
        stop: DispatchStop,
        /,
    ) -> AttemptEvidence:
        """Retain attached cleanup evidence and remember the original failure.

        Returns:
            Typed failed attempt evidence when cleanup evidence is attached.
        """
        supervisor_evidence = failure_evidence(error)
        stop(error)
        if supervisor_evidence is None:
            raise error
        self._state.raised_error = error
        return AttemptEvidence(
            control_flow="raised",
            outcome=supervisor_evidence,
            error_type=type(error).__name__,
            diagnostic=str(error),
            request=call.request,
            started_at_utc=started_at,
            ended_at_utc=self.runtime.utc_now(),
            usage_telemetry=None,
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
        self._state.attempts.setdefault(call.planned_call.position, []).append(
            attempt_record
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
            await self.evidence.record_quota_telemetry(
                QuotaTelemetryEvent(
                    run_id=call.run_id,
                    call_id=call.call_id,
                    attempt_number=attempt_number,
                    observation=observation,
                )
            )
        return observation

    async def _wait_for_quota(
        self, trigger: _SettledAttempt, stop: _DispatchGate, /
    ) -> None:
        """Record and run one pause until fresh quota permits resumption.

        Raises:
            RuntimeError: Policy bounds or unknown observations stop recovery.
        """
        pause = await self._start_quota_wait(trigger)
        prior_probe: QuotaProbeEvidence | None = None
        while True:
            remaining = await self._quota_wait_remaining(pause, stop)
            request = await self._schedule_quota_probe(pause, prior_probe, remaining)
            request = await self._await_probe_due(pause, request, remaining)
            probe = await self._poll_and_settle_probe(request, stop)
            self._state.quota_waited_seconds = max(
                self._state.quota_waited_seconds,
                pause.cumulative_waited_before_seconds
                + max(0.0, self.runtime.monotonic() - pause.started_at_monotonic),
            )
            action = await self.decide_quota_recovery(self, trigger, prior_probe, probe)
            await self._record_quota_recheck(pause, action, probe)
            match action:
                case "resume":
                    await self._finish_quota_wait(
                        pause.trigger,
                        pause.context,
                        pause.wait_id,
                        pause.started_at_utc,
                        pause.started_at_monotonic,
                        "quota_available",
                        probe.observation,
                    )
                    return
                case "stop":
                    await self._finish_quota_wait(
                        pause.trigger,
                        pause.context,
                        pause.wait_id,
                        pause.started_at_utc,
                        pause.started_at_monotonic,
                        "unknown",
                        probe.observation,
                    )
                    raise RuntimeError("quota recovery stopped without resumption")
                case "continue":
                    prior_probe = probe
                case unreachable:
                    assert_never(unreachable)

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
        wait_id = f"{trigger.call.run_id}:quota:{trigger.attempt_number}"
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
        await self.evidence.record_wait_event(
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
        )
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
            RuntimeError: Stop, wait, or probe limits prevent another poll.
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
            end = "stop" if stop.stopped() else "bound"
            await self._finish_quota_wait(
                pause.trigger,
                pause.context,
                pause.wait_id,
                pause.started_at_utc,
                pause.started_at_monotonic,
                end,
                None,
            )
            raise RuntimeError(reason)
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
        request = await self.prepare_quota_probe(self, pause.trigger, prior_probe)
        if remaining is not None and request.scheduled_wait_seconds >= remaining:
            request = request.model_copy(update={"scheduled_wait_seconds": remaining})
        await self.evidence.record_quota_probe_event(
            QuotaProbeScheduled(kind="scheduled", schedule=request.schedule)
        )
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
            RuntimeError: The bounded wait expires before the poll is due.
        """
        scheduled_start = self.runtime.monotonic()
        try:
            await self.runtime.sleep(request.scheduled_wait_seconds)
        except asyncio.CancelledError:
            await self._cancel_scheduled_probe(request, scheduled_start, "cancelled")
            self._store_quota_wait_elapsed(pause)
            await self._finish_quota_wait(
                pause.trigger,
                pause.context,
                pause.wait_id,
                pause.started_at_utc,
                pause.started_at_monotonic,
                "cancelled",
                None,
            )
            raise
        actual_wait = max(0.0, self.runtime.monotonic() - scheduled_start)
        if remaining is not None and actual_wait >= remaining:
            await self._cancel_scheduled_probe(request, scheduled_start, "stop")
            self._store_quota_wait_elapsed(pause)
            await self._finish_quota_wait(
                pause.trigger,
                pause.context,
                pause.wait_id,
                pause.started_at_utc,
                pause.started_at_monotonic,
                "bound",
                None,
            )
            raise RuntimeError("quota wait limit is exhausted")
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
        await self.evidence.record_quota_probe_event(
            QuotaProbeCancelled(
                kind="cancelled",
                schedule=request.schedule,
                cause=cause,
                ended_at_utc=self.runtime.utc_now(),
                elapsed_seconds=max(0.0, self.runtime.monotonic() - started_at),
                elapsed_basis="monotonic",
            )
        )

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
        await self.evidence.record_wait_event(
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
        )

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
        await self.evidence.record_wait_event(
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
        )
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

    async def _poll_and_settle_probe(
        self, request: QuotaProbeRequest, stop: _DispatchGate, /
    ) -> QuotaProbeEvidence:
        """Persist the start and settlement around one supervised poll.

        Returns:
            The quota probe evidence returned by the reader.

        """
        await self.evidence.record_quota_probe_event(
            QuotaProbeStarted(kind="started", request=request)
        )
        self._state.probes_started += 1
        self._state.active_probes += 1
        self._publish_progress("quota_paused")
        try:
            probe = await self.quota_status.poll(request, stop)
        except BaseException as error:
            await self._settle_failed_probe(error, request, stop)
            raise
        return await self._settle_successful_probe(probe)

    async def _settle_failed_probe(
        self,
        error: BaseException,
        request: QuotaProbeRequest,
        stop: _DispatchGate,
        /,
    ) -> None:
        """Persist failed poll evidence and retain its original control flow."""
        stop(error)
        owner_cancellation = await self._record_probe_after_failure(error, request)
        self._state.active_probes -= 1
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
        self, probe: QuotaProbeEvidence, /
    ) -> QuotaProbeEvidence:
        """Persist returned probe evidence and update passive progress counts.

        Returns:
            The settled probe evidence.
        """
        await self.evidence.record_quota_probe_settled(probe)
        self._state.active_probes -= 1
        if probe.quota_state in {"available", "exhausted"}:
            self._state.probes_completed += 1
        else:
            self._state.probes_failed += 1
        self._publish_progress("quota_paused")
        return probe

    async def _record_probe_after_failure(
        self, error: BaseException, request: QuotaProbeRequest, /
    ) -> asyncio.CancelledError | None:
        """Persist attached evidence and report cancellation during settlement.

        Returns:
            Cancellation delivered to this owner while the evidence write settled.
        """
        probe = quota_probe_evidence(error, request)
        if probe is None:
            return None
        settlement = asyncio.create_task(
            self.evidence.record_quota_probe_settled(probe),
            name=f"quota-probe-settlement-{request.schedule.probe_id}",
        )
        owner_cancellation: asyncio.CancelledError | None = None
        while not settlement.done():
            try:
                await asyncio.shield(settlement)
            except asyncio.CancelledError as cancellation:
                if settlement.cancelled():
                    error.add_note("Quota probe evidence settlement was cancelled")
                    return owner_cancellation
                if owner_cancellation is None:
                    owner_cancellation = cancellation
            except BaseException as persistence_error:
                error.add_note(
                    "Quota probe evidence could not be persisted: "
                    f"{persistence_error!r}"
                )
                return owner_cancellation
        if settlement.cancelled():
            error.add_note("Quota probe evidence settlement was cancelled")
        elif (persistence_error := settlement.exception()) is not None:
            error.add_note(
                f"Quota probe evidence could not be persisted: {persistence_error!r}"
            )
        return owner_cancellation


async def _select_dispatch(
    coordinator: Coordinator,
    settled: _SettledAttempt | None,
    stop: DispatchStop,
    /,
) -> _DispatchDecision:
    """Select plan-order attempts and finalize when all positions settle.

    The selector is intentionally deterministic and does no I/O.

    Returns:
        The next attempt decision or the final run record.

    Raises:
        RuntimeError: A stop was already latched.
    """
    if isinstance(stop, _DispatchGate) and stop.stopped():
        raise RuntimeError("dispatch was stopped")
    if settled is not None:
        coordinator._state.next_position = max(
            coordinator._state.next_position, settled.call.planned_call.position + 1
        )
    if coordinator._state.next_position < len(coordinator.bound_run.calls):
        call = coordinator.bound_run.calls[coordinator._state.next_position]
        coordinator._state.next_position += 1
        return _DispatchAttempt(call, 1)
    await asyncio.sleep(0)
    return _DispatchComplete(_assemble_run_record(coordinator))


async def _prepare_quota_probe(
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
    await asyncio.sleep(0)
    observation = trigger.observation
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
    ordinal = coordinator._state.probes_started + 1
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
        pause_wait_id=f"{trigger.call.run_id}:quota:{trigger.attempt_number}",
        poll_started_at_utc=due_at,
        scheduled_wait_seconds=delay,
        scheduled_wait_elapsed_basis="monotonic",
    )


async def _decide_quota_recovery(
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
    await asyncio.sleep(0)
    del prior_probe
    observation = probe.observation
    scope = coordinator.bound_run.binding.quota_scope
    pause_id = f"{trigger.call.run_id}:quota:{trigger.attempt_number}"
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
    """Require a normally returned, zero-exit probe with safe cleanup.

    Returns:
        Whether the probe evidence permits interpreting its quota observation.
    """
    outcome = probe.process.outcome
    if probe.process.control_flow != "returned" or not isinstance(outcome, Completed):
        return False
    if outcome.exit_status != 0:
        return False
    return outcome.observation.cleanup.dispatch_permitted


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
        usage_telemetry=None,
    )


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
    attempt_number: AttemptNumber,
    config: HarnessConfig,
    /,
) -> _RetryReason | None:
    """Return the one exhausted-attempt category still eligible for retry.

    Returns:
        Infrastructure, capacity, or no remaining eligible retry category.
    """
    if assessment is None:
        return None
    retries_used = attempt_number - 1
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
    if settled.record.outcome_kind == "cancelled":
        return "cancelled"
    if settled.record.exit_status == 0 and settled.evidence.control_flow == "returned":
        return "complete"
    return "failed"


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
                else "complete"
                if coordinator._state.attempts[call.planned_call.position][
                    -1
                ].exit_status
                == 0
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
            else "incomplete"
        ),
        runner_version=coordinator.bound_run.binding.runner_version,
        codex_path=str(coordinator.bound_run.binding.executable_path),
        cli_version=coordinator.bound_run.binding.cli_version,
        effective_settings=coordinator.bound_run.binding.effective_settings,
        calls=records,
        waits=tuple(coordinator._state.waits),
    )
