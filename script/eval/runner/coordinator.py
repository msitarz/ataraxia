# SPDX-License-Identifier: Apache-2.0
"""Compose dispatch decisions, attempt effects, and paused quota recovery.

Dispatch selection and quota recovery policy remain explicit pending leaves.
"""

import asyncio
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from typing import Literal, assert_never

from script.eval.evidence import EvidenceStore
from script.eval.model import (
    AttemptEvidence,
    AttemptNumber,
    AttemptRecord,
    HarnessConfig,
    QuotaObservation,
    QuotaProbeEvidence,
    QuotaProbeRequest,
    QuotaProbeStarted,
    QuotaTelemetryEvent,
    RunRecord,
)
from script.eval.runner.ports import (
    AttemptCall,
    BoundRun,
    EffectiveCall,
    OutcomeClassifier,
    ProgressSink,
    QuotaStatusReader,
    Runtime,
)
from script.eval.runner.quota_evidence import quota_probe_evidence
from script.process_supervisor import AttemptResult, DispatchStop

type CaptureReturnedAttempt = Callable[
    [EffectiveCall, AttemptResult, str, str], AttemptEvidence
]
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
class _DispatchAttempt:
    """Select one planned call attempt for coordinator-owned execution."""

    call: EffectiveCall
    attempt_number: AttemptNumber


@dataclass(frozen=True)
class _QuotaPaused:
    """Select quota recovery after a settled attempt blocks further dispatch."""

    trigger: _SettledAttempt


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


@dataclass(frozen=True)
class Coordinator:
    """Own one bound run and order its selected effects.

    Dispatch selection supplies one decision at a time. This coordinator owns
    attempt execution and durability, and directly awaits quota recovery only
    when selection reports a pause. The selection and recovery policy leaves
    remain pending.
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
        return record

    async def _dispatch(self) -> RunRecord:
        """Execute selector decisions and retain durable attempt state.

        Returns:
            The completed run record.

        Raises:
            RuntimeError: A decision conflicts with the stop or pause state.
        """
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
        outcome = await self.attempt(call.request, stop)
        ended_at = self.runtime.utc_now()
        attempt_evidence = self.capture_returned_attempt(
            call, outcome, started_at, ended_at
        )
        assessment = self.classifier.assess(attempt_evidence)
        attempt_record = await self.evidence.record_attempt(
            call.run_id,
            call.call_id,
            call.planned_call.position,
            attempt_number,
            attempt_evidence,
            assessment,
        )
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
        return _SettledAttempt(
            call=call,
            attempt_number=attempt_number,
            evidence=attempt_evidence,
            record=attempt_record,
            observation=observation,
        )

    async def _wait_for_quota(
        self, trigger: _SettledAttempt, stop: _DispatchGate, /
    ) -> None:
        """Poll serially while recovery policy keeps the run paused.

        Raises:
            RuntimeError: Recovery policy refuses resumption.
        """
        prior_probe: QuotaProbeEvidence | None = None
        while True:
            if stop.stopped():
                raise RuntimeError("dispatch was stopped during quota recovery")
            request = await self.prepare_quota_probe(self, trigger, prior_probe)
            probe = await self._poll_and_settle_probe(request, stop)
            action = await self.decide_quota_recovery(self, trigger, prior_probe, probe)
            match action:
                case "resume":
                    return
                case "stop":
                    raise RuntimeError("quota recovery stopped without resumption")
                case "continue":
                    prior_probe = probe
                case unreachable:
                    assert_never(unreachable)

    async def _poll_and_settle_probe(
        self, request: QuotaProbeRequest, stop: _DispatchGate, /
    ) -> QuotaProbeEvidence:
        """Persist the start and settlement around one supervised poll.

        Returns:
            The quota probe evidence returned by the reader.

        Raises:
            RuntimeError: Dispatch stop is latched during the probe.
        """
        await self.evidence.record_quota_probe_event(
            QuotaProbeStarted(kind="started", request=request)
        )
        if stop.stopped():
            raise RuntimeError("dispatch was stopped before quota probe")
        try:
            probe = await self.quota_status.poll(request, stop)
        except BaseException as error:
            stop(error)
            owner_cancellation = await self._record_probe_after_failure(error, request)
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
            raise
        await self.evidence.record_quota_probe_settled(probe)
        if stop.stopped():
            raise RuntimeError("dispatch was stopped during quota probe")
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
    """Select the next dispatch or completion decision.

    Raises:
        NotImplementedError: Dispatch selection is not implemented.
    """
    del coordinator, settled, stop
    await asyncio.sleep(0)
    raise NotImplementedError("dispatch selection is not implemented")


async def _prepare_quota_probe(
    coordinator: Coordinator,
    trigger: _SettledAttempt,
    prior_probe: QuotaProbeEvidence | None,
    /,
) -> QuotaProbeRequest:
    """Prepare one probe request for the current quota pause.

    Raises:
        NotImplementedError: Probe schedule and request policy are deferred.
    """
    del coordinator, trigger, prior_probe
    await asyncio.sleep(0)
    raise NotImplementedError("quota probe request preparation is not implemented")


async def _decide_quota_recovery(
    coordinator: Coordinator,
    trigger: _SettledAttempt,
    prior_probe: QuotaProbeEvidence | None,
    probe: QuotaProbeEvidence,
    /,
) -> _RecoveryAction:
    """Choose whether a persisted probe continues, resumes, or stops recovery.

    Raises:
        NotImplementedError: Recovery assessment policy is deferred.
    """
    del coordinator, trigger, prior_probe, probe
    await asyncio.sleep(0)
    raise NotImplementedError("quota recovery assessment is not implemented")


def _capture_returned_attempt(
    call: EffectiveCall,
    outcome: AttemptResult,
    started_at: str,
    ended_at: str,
    /,
) -> AttemptEvidence:
    """Capture a returned supervisor outcome as typed attempt evidence."""
    del call, outcome, started_at, ended_at
    raise NotImplementedError("supervisor evidence conversion is not implemented")
