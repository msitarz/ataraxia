# SPDX-License-Identifier: Apache-2.0
"""Coordinator decision wiring, evidence order, and paused recovery."""

import asyncio
from dataclasses import replace
from pathlib import Path
from typing import Literal, override

import pytest

from script.eval.evidence import EvidenceStore
from script.eval.model import (
    AttemptEvidence,
    AttemptNumber,
    AttemptRecord,
    DirectoryOption,
    FrozenPlan,
    HarnessConfig,
    PlannedCall,
    PreparedEvidence,
    QuotaAllowanceId,
    QuotaObservation,
    QuotaProbeEvidence,
    QuotaProbeId,
    QuotaProbeLifecycleInput,
    QuotaProbeRecord,
    QuotaProbeRequest,
    QuotaProbeSchedule,
    QuotaProbeSettled,
    QuotaProbeStarted,
    QuotaProviderId,
    QuotaScope,
    QuotaTelemetryEvent,
    RetryAssessment,
    RunRecord,
    WaitEvent,
)
from script.eval.runner.coordinator import (
    Coordinator,
    _DispatchAttempt,
    _DispatchComplete,
    _DispatchDecision,
    _QuotaPaused,
    _RecoveryAction,
    _SelectDispatch,
    _SettledAttempt,
)
from script.eval.runner.ports import (
    AttemptCall,
    BoundRun,
    CliBinding,
    EffectiveCall,
    OutcomeClassifier,
    ProgressSink,
    ProgressSnapshot,
    QuotaStatusReader,
    Runtime,
)
from script.eval.runner.quota_evidence import attach_quota_probe_evidence
from script.process_supervisor import (
    AttemptObservation,
    AttemptRequest,
    AttemptResult,
    CapturedOutput,
    CleanupEvidence,
    Completed,
    DispatchStop,
)


def configuration(
    *,
    quota: bool = False,
    dry_run: bool = False,
    concurrency: int = 1,
    quota_poll_interval: float = 7.5,
) -> HarnessConfig:
    """Build a valid run configuration with selectable scheduling settings."""
    return HarnessConfig(
        ordered_options=(DirectoryOption(position=0, path=Path("context")),),
        models=("model-a",),
        efforts=("low",),
        concurrency=concurrency,
        output_directory=None if dry_run else Path("output"),
        dry_run=dry_run,
        timeout_seconds=1.0,
        cleanup_timeout_seconds=1.0,
        grace_seconds=0.0,
        output_limit_bytes=0,
        quota_wait_enabled=quota,
        quota_poll_interval_seconds=quota_poll_interval,
        instructions_file_path=None,
    )


def bound_run(*, calls_count: int = 1, config: HarnessConfig | None = None) -> BoundRun:
    """Build a fully validated plan and matching effective calls."""
    actual_config = configuration() if config is None else config
    planned_calls = tuple(
        PlannedCall(
            position=position,
            context_indices=(),
            model="model-a",
            effort="low",
            prompt_sha256=f"prompt-{position}",
            prompt=f"prompt {position}".encode(),
        )
        for position in range(calls_count)
    )
    plan = FrozenPlan(
        run_id="run-1",
        configuration=actual_config,
        repository_root=Path("/repo"),
        head_commit="head-1",
        snapshots=(),
        boundary_bytes=(),
        instructions_file=None,
        calls=planned_calls,
    )
    calls = tuple(
        EffectiveCall(
            run_id="run-1",
            call_id=f"call-{position}",
            planned_call=planned,
            request=AttemptRequest(
                argv=("codex", "exec", str(position)),
                cwd=Path("/repo"),
                timeout_seconds=1.0,
                cleanup_timeout_seconds=1.0,
                output_limit_bytes=0,
                stdin="devnull",
            ),
        )
        for position, planned in enumerate(planned_calls)
    )
    return BoundRun(
        plan=plan,
        binding=CliBinding(
            executable_path=Path("/usr/bin/codex"),
            cli_version="1.0",
            runner_version="test",
            effective_settings=(),
            quota_scope=None,
        ),
        evidence=PreparedEvidence(
            output_directory=Path("output"),
            plan_artifact=Path("output/plan.json"),
            model_instructions_file=None,
        ),
        calls=calls,
    )


def run_record() -> RunRecord:
    """Return a valid selector-produced run record for finalization checks."""
    return RunRecord(
        run_id="run-1",
        repository_root="/repo",
        head_commit="head-1",
        state="complete",
        runner_version="test",
        codex_path=None,
        cli_version=None,
        effective_settings=(),
        calls=(),
    )


class FixedRuntime(Runtime):
    """Provide deterministic timestamps and ordinary cancellable waits."""

    def utc_now(self) -> str:
        return "2026-10-27T10:00:00Z"

    def monotonic(self) -> float:
        return 1.0

    async def sleep(self, seconds: float, /) -> None:
        await asyncio.sleep(seconds)

    def uniform(self, lower: float, upper: float, /) -> float:
        return lower


class FakeProgress(ProgressSink):
    """Retain any coordinator snapshots."""

    def __init__(self) -> None:
        self.snapshots: list[ProgressSnapshot] = []

    def publish(self, snapshot: ProgressSnapshot, /) -> None:
        self.snapshots.append(snapshot)


class FakeEvidence(EvidenceStore):
    """Record exact attempt and quota-probe values with their effect order."""

    def __init__(self, order: list[str]) -> None:
        self.events: list[str] = []
        self.order = order
        self.attempt_inputs: list[
            tuple[str, str, int, AttemptNumber, AttemptEvidence, RetryAssessment | None]
        ] = []
        self.attempt_records: list[AttemptRecord] = []
        self.telemetry_events: list[QuotaTelemetryEvent] = []
        self.probe_inputs: list[QuotaProbeEvidence] = []
        self.probe_events: list[QuotaProbeLifecycleInput] = []
        self.final_records: list[RunRecord] = []

    async def create(
        self, output_directory: Path, plan: FrozenPlan, /
    ) -> PreparedEvidence:
        raise AssertionError("coordinator receives an already prepared store")

    async def record_attempt(
        self,
        run_id: str,
        call_id: str,
        position: int,
        attempt_number: AttemptNumber,
        evidence: AttemptEvidence,
        retry_assessment: RetryAssessment | None,
        /,
    ) -> AttemptRecord:
        self.order.append("record_attempt")
        self.events.append("attempt")
        self.attempt_inputs.append((
            run_id,
            call_id,
            position,
            attempt_number,
            evidence,
            retry_assessment,
        ))
        record = AttemptRecord.model_validate({
            "run_id": run_id,
            "call_id": call_id,
            "position": position,
            "attempt_number": attempt_number,
            "control_flow": "returned",
            "outcome_kind": "completed",
            "started_at_utc": evidence.started_at_utc,
            "ended_at_utc": evidence.ended_at_utc,
            "argv": evidence.request.argv,
            "cwd": str(evidence.request.cwd),
            "timeout_seconds": 1.0,
            "cleanup_timeout_seconds": 1.0,
            "grace_seconds": 0.0,
            "output_limit_bytes": 0,
            "elapsed_seconds": 0.5,
            "elapsed_basis": "supervisor_observation",
            "exit_status": 0,
            "termination_reason": None,
            "cleanup": None,
            "stdout_artifact": None,
            "stderr_artifact": None,
            "usage_telemetry": evidence.usage_telemetry,
            "error_type": None,
            "diagnostic": None,
            "retry_assessment": retry_assessment,
        })
        self.attempt_records.append(record)
        return record

    async def record_wait_event(self, event: WaitEvent, /) -> None:
        self.events.append("wait")

    async def record_quota_probe_event(
        self, event: QuotaProbeLifecycleInput, /
    ) -> None:
        self.order.append("record_probe_start")
        self.events.append("probe-start")
        self.probe_events.append(event)

    async def record_quota_probe_settled(
        self, evidence: QuotaProbeEvidence, /
    ) -> QuotaProbeSettled:
        self.order.append("record_probe_settled")
        self.events.append("probe-settled")
        self.probe_inputs.append(evidence)
        process = evidence.process
        ended_at = process.ended_at_utc
        outcome_kind = (
            "completed"
            if process.control_flow == "returned"
            else "cancelled"
            if process.control_flow == "cancelled"
            else "unexpected_exception"
        )
        return QuotaProbeSettled(
            kind="settled",
            record=QuotaProbeRecord(
                request=evidence.request,
                quota_state=evidence.quota_state,
                observation=evidence.observation,
                classification_basis=evidence.classification_basis,
                control_flow=process.control_flow,
                outcome_kind=outcome_kind,
                started_at_utc=process.started_at_utc,
                ended_at_utc=process.ended_at_utc,
                argv=process.request.argv,
                cwd=str(process.request.cwd),
                timeout_seconds=1.0,
                cleanup_timeout_seconds=1.0,
                grace_seconds=0.0,
                output_limit_bytes=0,
                elapsed_seconds=0.5 if ended_at is not None else None,
                elapsed_basis=(
                    "supervisor_observation" if ended_at is not None else "unavailable"
                ),
                exit_status=0 if outcome_kind == "completed" else None,
                termination_reason=None,
                cleanup=None,
                stdout_artifact=None,
                stderr_artifact=None,
                usage_telemetry=process.usage_telemetry,
                error_type=None,
                diagnostic=None,
            ),
        )

    async def record_quota_telemetry(self, event: QuotaTelemetryEvent, /) -> None:
        self.order.append("record_telemetry")
        self.events.append("telemetry")
        self.telemetry_events.append(event)

    async def finalize(self, record: RunRecord, /) -> None:
        self.order.append("finalize")
        self.events.append("final")
        self.final_records.append(record)


class BlockingProbeEvidence(FakeEvidence):
    """Pause probe settlement until the test allows the durable write."""

    def __init__(self, order: list[str]) -> None:
        super().__init__(order)
        self.write_started = asyncio.Event()
        self.allow_write = asyncio.Event()
        self.write_finished = asyncio.Event()

    @override
    async def record_quota_probe_settled(
        self, evidence: QuotaProbeEvidence, /
    ) -> QuotaProbeSettled:
        self.write_started.set()
        await self.allow_write.wait()
        record = await super().record_quota_probe_settled(evidence)
        self.write_finished.set()
        return record


class FakeQuotaReader(QuotaStatusReader):
    """Return typed passive observations and an optional controlled probe."""

    def __init__(self, order: list[str]) -> None:
        self.order = order
        self.observations = 0
        self.probes = 0
        self.requests: list[QuotaProbeRequest] = []
        self.observation = QuotaObservation(
            scope=None,
            read_at_utc="2026-10-27T10:00:00Z",
            source_coordinate=None,
            windows=(),
            diagnostic="source unavailable",
        )
        self.probe_result: QuotaProbeEvidence | None = None
        self.probe_error: BaseException | None = None
        self.stop_reason: AttemptResult | BaseException | None = None

    @property
    def expected_scope(self) -> QuotaScope | None:
        return None

    async def observe_settled_attempt(
        self, evidence: AttemptEvidence, /
    ) -> QuotaObservation:
        self.observations += 1
        self.order.append("observe_quota")
        return self.observation

    async def poll(
        self, request: QuotaProbeRequest, stop_dispatch: DispatchStop, /
    ) -> QuotaProbeEvidence:
        self.probes += 1
        self.requests.append(request)
        self.order.append("poll")
        if self.stop_reason is not None:
            stop_dispatch(self.stop_reason)
        if self.probe_error is not None:
            raise self.probe_error
        assert self.probe_result is not None
        return self.probe_result


class FakeClassifier(OutcomeClassifier):
    """Retain exact evidence and return one fixed assessment."""

    def __init__(self, order: list[str]) -> None:
        self.order = order
        self.assessed: list[AttemptEvidence] = []
        self.assessment = RetryAssessment(
            retry_class="unknown",
            classification_basis=None,
            no_result_basis="present_or_unknown",
            diagnostic="not assessed",
        )

    def assess(self, evidence: AttemptEvidence, /) -> RetryAssessment:
        self.order.append("classify")
        self.assessed.append(evidence)
        return self.assessment


class AttemptThenPause:
    """Select one attempt, pause for quota, then stop without another call."""

    def __init__(self, call: EffectiveCall) -> None:
        self.call = call
        self.decisions = 0

    async def __call__(
        self,
        coordinator: Coordinator,
        settled: _SettledAttempt | None,
        stop: DispatchStop,
        /,
    ) -> _DispatchDecision:
        await asyncio.sleep(0)
        self.decisions += 1
        if self.decisions == 1:
            return _DispatchAttempt(self.call, 1)
        if self.decisions == 2 and settled is not None:
            return _QuotaPaused(settled)
        return _DispatchComplete(run_record())


class FixedProbeRequest:
    """Return one exact request while retaining pause and cadence inputs."""

    def __init__(self, request: QuotaProbeRequest) -> None:
        self.request = request
        self.inputs: list[tuple[_SettledAttempt, QuotaProbeEvidence | None]] = []

    async def __call__(
        self,
        coordinator: Coordinator,
        trigger: _SettledAttempt,
        prior_probe: QuotaProbeEvidence | None,
        /,
    ) -> QuotaProbeRequest:
        await asyncio.sleep(0)
        self.inputs.append((trigger, prior_probe))
        return self.request


class PauseThenResume:
    """Drive two calls with one awaited, durably settled quota probe."""

    def __init__(
        self,
        first: EffectiveCall,
        second: EffectiveCall,
        request: QuotaProbeRequest,
        probe: QuotaProbeEvidence,
        evidence: FakeEvidence,
        order: list[str],
    ) -> None:
        self.first = first
        self.second = second
        self.request_provider = FixedProbeRequest(request)
        self.probe = probe
        self.evidence = evidence
        self.order = order
        self.resumed = False
        self.seen: list[_SettledAttempt | None] = []
        self.recovery_inputs: list[tuple[_SettledAttempt, QuotaProbeEvidence]] = []

    async def select(
        self,
        coordinator: Coordinator,
        settled: _SettledAttempt | None,
        stop: DispatchStop,
        /,
    ) -> _DispatchDecision:
        await asyncio.sleep(0)
        self.seen.append(settled)
        if settled is None and len(self.seen) == 1:
            return _DispatchAttempt(self.first, 1)
        if settled is not None and not self.resumed:
            return _QuotaPaused(settled)
        if settled is None and self.resumed:
            return _DispatchAttempt(self.second, 1)
        return _DispatchComplete(run_record())

    async def prepare_probe(
        self,
        coordinator: Coordinator,
        trigger: _SettledAttempt,
        prior_probe: QuotaProbeEvidence | None,
        /,
    ) -> QuotaProbeRequest:
        self.order.append("prepare_probe")
        return await self.request_provider(coordinator, trigger, prior_probe)

    async def decide_recovery(
        self,
        coordinator: Coordinator,
        trigger: _SettledAttempt,
        prior_probe: QuotaProbeEvidence | None,
        probe: QuotaProbeEvidence,
        /,
    ) -> _RecoveryAction:
        await asyncio.sleep(0)
        assert prior_probe is None
        assert self.evidence.probe_inputs[0] is probe
        assert self.evidence.events[-1] == "probe-settled"
        self.recovery_inputs.append((trigger, probe))
        self.order.append("decide_recovery")
        self.resumed = True
        return "resume"


def successful_outcome() -> AttemptResult:
    """Return a safe completed supervisor result with captured bytes."""
    return Completed(
        observation=AttemptObservation(
            output=CapturedOutput(stdout=b"answer", stderr=b""),
            elapsed_seconds=0.5,
            cleanup=CleanupEvidence("owned", (), "reaped", None),
        ),
        exit_status=0,
    )


def make_attempt(
    order: list[str],
    outcomes: list[AttemptResult],
    requests: list[AttemptRequest],
) -> AttemptCall:
    """Return a supervisor fake that retains exact requests and outcomes."""
    outcomes_iterator = iter(outcomes)

    async def attempt(request: AttemptRequest, stop: DispatchStop, /) -> AttemptResult:
        await asyncio.sleep(0)
        order.append("attempt")
        requests.append(request)
        return next(outcomes_iterator)

    return attempt


def stopping_attempt(
    hooks: list[DispatchStop],
    requests: list[AttemptRequest],
    outcome: AttemptResult,
) -> AttemptCall:
    """Return an attempt fake that latches dispatch stop before settlement."""

    async def attempt(request: AttemptRequest, stop: DispatchStop, /) -> AttemptResult:
        await asyncio.sleep(0)
        hooks.append(stop)
        requests.append(request)
        stop(outcome)
        return outcome

    return attempt


def capture_attempt(
    call: EffectiveCall,
    outcome: AttemptResult,
    started_at: str,
    ended_at: str,
    /,
) -> AttemptEvidence:
    """Build attempt evidence with retained request and output telemetry."""
    return AttemptEvidence(
        control_flow="returned",
        outcome=outcome,
        error_type=None,
        diagnostic=None,
        request=call.request,
        started_at_utc=started_at,
        ended_at_utc=ended_at,
        usage_telemetry=b"answer",
    )


def make_probe_request(run: BoundRun, /) -> QuotaProbeRequest:
    """Build one validated probe request for the supplied run."""
    return QuotaProbeRequest(
        schedule=QuotaProbeSchedule(
            run_id=run.plan.run_id,
            probe_id=QuotaProbeId("probe-1"),
            scope=QuotaScope(
                provider_id=QuotaProviderId("codex"),
                allowance_id=QuotaAllowanceId("account-a"),
            ),
            reason="periodic",
            created_at_utc="2026-10-27T10:00:00Z",
            due_at_utc="2026-10-27T10:00:00Z",
            interval_seconds=7.5,
            reset_hint_at_utc=None,
        ),
        pause_wait_id="pause-1",
        poll_started_at_utc="2026-10-27T10:00:00Z",
        scheduled_wait_seconds=0.0,
        scheduled_wait_elapsed_basis="monotonic",
    )


def make_probe_evidence(
    request: QuotaProbeRequest,
    call: EffectiveCall,
    *,
    state: Literal["available", "exhausted", "unknown", "unavailable"] = "available",
    control_flow: Literal["returned", "cancelled", "raised"] = "returned",
) -> QuotaProbeEvidence:
    """Compose typed probe evidence from a returned fake attempt."""
    return QuotaProbeEvidence(
        request=request,
        process=AttemptEvidence(
            control_flow=control_flow,
            outcome=successful_outcome() if control_flow == "returned" else None,
            error_type=None if control_flow == "returned" else "test failure",
            diagnostic=None,
            request=call.request,
            started_at_utc="2026-10-27T10:00:00Z",
            ended_at_utc=(
                "2026-10-27T10:00:00Z" if control_flow == "returned" else None
            ),
            usage_telemetry=None,
        ),
        quota_state=state,
        observation=QuotaObservation(
            scope=request.schedule.scope,
            read_at_utc="2026-10-27T10:00:00Z",
            source_coordinate="session:1",
            windows=(),
            diagnostic=None,
        ),
        classification_basis="typed test observation",
    )


def make_coordinator(
    run: BoundRun,
    evidence: FakeEvidence,
    quota: FakeQuotaReader,
    order: list[str],
    *,
    selector: _SelectDispatch,
) -> tuple[Coordinator, FakeClassifier, list[AttemptRequest]]:
    """Compose a bound coordinator with exact fake collaborators."""
    requests: list[AttemptRequest] = []
    classifier = FakeClassifier(order)
    coordinator = Coordinator(
        bound_run=run,
        evidence=evidence,
        attempt=make_attempt(order, [successful_outcome()] * len(run.calls), requests),
        classifier=classifier,
        quota_status=quota,
        runtime=FixedRuntime(),
        progress=FakeProgress(),
        select_dispatch=selector,
        capture_returned_attempt=capture_attempt,
    )
    return coordinator, classifier, requests


def selection_sequence(
    decisions: list[_DispatchDecision], seen: list[_SettledAttempt | None]
) -> _SelectDispatch:
    """Return a selector fake that retains each settled value it receives."""

    async def select(
        coordinator: Coordinator,
        settled: _SettledAttempt | None,
        stop: DispatchStop,
        /,
    ) -> _DispatchDecision:
        await asyncio.sleep(0)
        seen.append(settled)
        return decisions.pop(0)

    return select


async def test_run_persists_attempt_before_passive_observation() -> None:
    """Pass the exact durable attempt and passive observation to selection."""
    # Given
    order: list[str] = []
    run = bound_run(
        config=configuration(quota=True, concurrency=3, quota_poll_interval=8.5)
    )
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    seen: list[_SettledAttempt | None] = []
    record = run_record()
    coordinator, classifier, requests = make_coordinator(
        run,
        evidence,
        quota,
        order,
        selector=selection_sequence(
            [_DispatchAttempt(run.calls[0], 1), _DispatchComplete(record)], seen
        ),
    )

    # When
    actual = await coordinator.run()

    # Then
    settled = seen[1]
    assert settled is not None
    assert seen[0] is None
    assert actual is record
    assert evidence.final_records == [record]
    assert coordinator.config is run.plan.configuration
    assert coordinator.config.concurrency == 3
    assert coordinator.config.quota_poll_interval_seconds == pytest.approx(8.5)
    assert requests == [run.calls[0].request]
    assert requests[0] is run.calls[0].request
    assert settled.call is run.calls[0]
    assert settled.record is evidence.attempt_records[0]
    assert settled.evidence is classifier.assessed[0]
    assert settled.observation is quota.observation
    assert evidence.telemetry_events[0].observation is quota.observation
    assert order == [
        "attempt",
        "classify",
        "record_attempt",
        "observe_quota",
        "record_telemetry",
        "finalize",
    ]


async def test_default_dispatch_selection_stays_explicitly_pending() -> None:
    """Do not finalize or launch attempts while dispatch selection is pending."""
    # Given
    order: list[str] = []
    run = bound_run()
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    requests: list[AttemptRequest] = []
    coordinator = Coordinator(
        bound_run=run,
        evidence=evidence,
        attempt=make_attempt(order, [successful_outcome()], requests),
        classifier=FakeClassifier(order),
        quota_status=quota,
        runtime=FixedRuntime(),
        progress=FakeProgress(),
        capture_returned_attempt=capture_attempt,
    )

    # When
    with pytest.raises(NotImplementedError, match="dispatch selection"):
        await coordinator.run()

    # Then
    assert requests == []
    assert evidence.events == []
    assert quota.observations == 0 and quota.probes == 0


async def test_attempt_stop_hook_refuses_a_later_selected_attempt() -> None:
    """Latch the exact supervisor stop hook before another attempt dispatches."""
    # Given
    order: list[str] = []
    run = bound_run(calls_count=2)
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    selector_hooks: list[DispatchStop] = []
    attempt_hooks: list[DispatchStop] = []
    requests: list[AttemptRequest] = []

    async def select(
        coordinator: Coordinator,
        settled: _SettledAttempt | None,
        stop: DispatchStop,
        /,
    ) -> _DispatchDecision:
        await asyncio.sleep(0)
        selector_hooks.append(stop)
        return next(decisions)

    decisions = iter((
        _DispatchAttempt(run.calls[0], 1),
        _DispatchAttempt(run.calls[1], 1),
    ))
    coordinator, _, _ = make_coordinator(run, evidence, quota, order, selector=select)
    coordinator = replace(
        coordinator,
        attempt=stopping_attempt(attempt_hooks, requests, successful_outcome()),
    )

    # When
    with pytest.raises(RuntimeError, match="dispatch was stopped"):
        await coordinator.run()

    # Then
    assert requests == [run.calls[0].request]
    assert selector_hooks[0] is selector_hooks[1] is attempt_hooks[0]
    assert len(evidence.attempt_inputs) == 1
    assert evidence.final_records == []


async def test_default_attempt_conversion_stays_explicitly_pending() -> None:
    """Keep returned supervisor evidence conversion visible at run boundary."""
    # Given
    order: list[str] = []
    run = bound_run()
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    requests: list[AttemptRequest] = []
    seen: list[_SettledAttempt | None] = []
    coordinator = Coordinator(
        bound_run=run,
        evidence=evidence,
        attempt=make_attempt(order, [successful_outcome()], requests),
        classifier=FakeClassifier(order),
        quota_status=quota,
        runtime=FixedRuntime(),
        progress=FakeProgress(),
        select_dispatch=selection_sequence(
            [_DispatchAttempt(run.calls[0], 1), _DispatchComplete(run_record())], seen
        ),
    )

    # When
    with pytest.raises(NotImplementedError, match="evidence conversion"):
        await coordinator.run()

    # Then
    assert requests == [run.calls[0].request]
    assert evidence.attempt_inputs == []
    assert evidence.final_records == []


async def test_quota_recovery_is_pause_gated_and_persists_before_next_attempt() -> None:
    """Await recovery only for a settled pause and persist probe before resuming."""
    # Given
    order: list[str] = []
    run = bound_run(calls_count=2, config=configuration(quota=True))
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    probe_request = make_probe_request(run)
    probe_result = make_probe_evidence(probe_request, run.calls[0])
    quota.probe_result = probe_result
    recovery = PauseThenResume(
        run.calls[0],
        run.calls[1],
        probe_request,
        probe_result,
        evidence,
        order,
    )

    coordinator, _, requests = make_coordinator(
        run, evidence, quota, order, selector=recovery.select
    )
    coordinator = replace(
        coordinator,
        prepare_quota_probe=recovery.prepare_probe,
        decide_quota_recovery=recovery.decide_recovery,
    )

    # When
    actual = await coordinator.run()

    # Then
    trigger = recovery.seen[1]
    assert trigger is not None
    assert recovery.recovery_inputs == [(trigger, probe_result)]
    assert recovery.request_provider.inputs == [(trigger, None)]
    assert quota.requests == [probe_request]
    assert quota.requests[0] is probe_request
    assert isinstance(evidence.probe_events[0], QuotaProbeStarted)
    assert evidence.probe_events[0].request is probe_request
    assert requests == [run.calls[0].request, run.calls[1].request]
    assert evidence.probe_inputs == [probe_result]
    assert evidence.probe_inputs[0] is probe_result
    assert actual is evidence.final_records[0]
    assert order == [
        "attempt",
        "classify",
        "record_attempt",
        "observe_quota",
        "record_telemetry",
        "prepare_probe",
        "record_probe_start",
        "poll",
        "record_probe_settled",
        "decide_recovery",
        "attempt",
        "classify",
        "record_attempt",
        "observe_quota",
        "record_telemetry",
        "finalize",
    ]


async def test_default_probe_request_preparation_stays_pending() -> None:
    """Do not poll when recovery request policy has not been supplied."""
    # Given
    order: list[str] = []
    run = bound_run(config=configuration(quota=True))
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    selection = AttemptThenPause(run.calls[0])
    coordinator, _, _ = make_coordinator(
        run, evidence, quota, order, selector=selection
    )

    # When
    with pytest.raises(NotImplementedError, match="request preparation"):
        await coordinator.run()

    # Then
    assert len(evidence.attempt_inputs) == 1
    assert quota.probes == 0
    assert evidence.final_records == []


async def test_default_recovery_assessment_stays_pending_after_durable_probe() -> None:
    """Persist returned probe evidence before the default assessment leaf fails."""
    # Given
    order: list[str] = []
    run = bound_run(config=configuration(quota=True))
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    request = make_probe_request(run)
    probe = make_probe_evidence(request, run.calls[0])
    quota.probe_result = probe
    coordinator, _, _ = make_coordinator(
        run,
        evidence,
        quota,
        order,
        selector=AttemptThenPause(run.calls[0]),
    )
    coordinator = replace(coordinator, prepare_quota_probe=FixedProbeRequest(request))

    # When
    with pytest.raises(NotImplementedError, match="recovery assessment"):
        await coordinator.run()

    # Then
    assert evidence.probe_inputs == [probe]
    assert evidence.probe_inputs[0] is probe
    assert evidence.events[-1] == "probe-settled"
    assert evidence.final_records == []


async def test_quota_reader_is_never_probed_without_a_pause_decision() -> None:
    """Keep enabled quota observation passive when selection never pauses."""
    # Given
    order: list[str] = []
    run = bound_run(config=configuration(quota=True))
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    seen: list[_SettledAttempt | None] = []
    coordinator, _, _ = make_coordinator(
        run,
        evidence,
        quota,
        order,
        selector=selection_sequence(
            [_DispatchAttempt(run.calls[0], 1), _DispatchComplete(run_record())], seen
        ),
    )

    # When
    await coordinator.run()

    # Then
    assert quota.observations == 1
    assert quota.probes == 0
    assert evidence.probe_inputs == []


async def test_disabled_quota_wait_rejects_pause_before_any_probe() -> None:
    """Refuse a pause decision when quota recovery is disabled in the plan."""
    # Given
    order: list[str] = []
    run = bound_run(config=configuration(quota=False))
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    settled_values: list[_SettledAttempt | None] = []

    async def select(
        coordinator: Coordinator,
        settled: _SettledAttempt | None,
        stop: DispatchStop,
        /,
    ) -> _DispatchDecision:
        await asyncio.sleep(0)
        settled_values.append(settled)
        if settled is None:
            return _DispatchAttempt(run.calls[0], 1)
        return _QuotaPaused(settled)

    coordinator, _, _ = make_coordinator(run, evidence, quota, order, selector=select)

    # When
    with pytest.raises(RuntimeError, match="quota recovery is disabled"):
        await coordinator.run()

    # Then
    assert len(settled_values) == 2
    assert quota.observations == 0
    assert quota.probes == 0
    assert evidence.final_records == []


async def test_probe_failure_persists_attached_evidence_without_resuming() -> None:
    """Persist exact attached probe evidence, then retain the primary failure."""
    # Given
    order: list[str] = []
    run = bound_run(config=configuration(quota=True))
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    probe_request = make_probe_request(run)
    probe = make_probe_evidence(
        probe_request, run.calls[0], state="unknown", control_flow="raised"
    )
    error = RuntimeError("probe failed")
    attach_quota_probe_evidence(error, probe)
    quota.probe_error = error
    selection = AttemptThenPause(run.calls[0])
    request_source = FixedProbeRequest(probe_request)
    coordinator, _, attempts = make_coordinator(
        run, evidence, quota, order, selector=selection
    )
    coordinator = replace(coordinator, prepare_quota_probe=request_source)

    # When
    with pytest.raises(RuntimeError, match="probe failed") as raised:
        await coordinator.run()

    # Then
    assert raised.value is error
    assert evidence.probe_inputs == [probe]
    assert evidence.probe_inputs[0] is probe
    assert attempts == [run.calls[0].request]
    assert evidence.final_records == []
    assert order[-1] == "record_probe_settled"


async def test_probe_failure_without_evidence_stays_incomplete() -> None:
    """Keep missing probe evidence incomplete and prevent another attempt."""
    # Given
    order: list[str] = []
    run = bound_run(calls_count=2, config=configuration(quota=True))
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    request = make_probe_request(run)
    quota.probe_error = RuntimeError("probe evidence unavailable")
    coordinator, _, requests = make_coordinator(
        run,
        evidence,
        quota,
        order,
        selector=AttemptThenPause(run.calls[0]),
    )
    coordinator = replace(coordinator, prepare_quota_probe=FixedProbeRequest(request))

    # When
    with pytest.raises(RuntimeError, match="probe evidence unavailable"):
        await coordinator.run()

    # Then
    assert requests == [run.calls[0].request]
    assert evidence.probe_inputs == []
    assert evidence.final_records == []


async def test_cancelled_probe_with_attached_evidence_never_resumes() -> None:
    """Settle attached cancellation evidence and propagate cancellation."""
    # Given
    order: list[str] = []
    run = bound_run(config=configuration(quota=True))
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    probe_request = make_probe_request(run)
    probe = make_probe_evidence(
        probe_request, run.calls[0], state="unknown", control_flow="cancelled"
    )
    cancellation = asyncio.CancelledError()
    attach_quota_probe_evidence(cancellation, probe)
    quota.probe_error = cancellation
    selection = AttemptThenPause(run.calls[0])
    request_source = FixedProbeRequest(probe_request)
    coordinator, _, _ = make_coordinator(
        run, evidence, quota, order, selector=selection
    )
    coordinator = replace(coordinator, prepare_quota_probe=request_source)

    # When
    with pytest.raises(asyncio.CancelledError) as raised:
        await coordinator.run()

    # Then
    assert raised.value is cancellation
    assert evidence.probe_inputs == [probe]
    assert evidence.final_records == []


def start_probe_with_attached_failure(
    run: BoundRun,
    evidence: BlockingProbeEvidence,
    quota: FakeQuotaReader,
    error: BaseException,
    order: list[str],
    /,
) -> tuple[asyncio.Task[RunRecord], QuotaProbeEvidence, list[AttemptRequest]]:
    """Start a paused run whose failing poll carries exact request evidence."""
    request = make_probe_request(run)
    control_flow: Literal["cancelled", "raised"] = (
        "cancelled" if isinstance(error, asyncio.CancelledError) else "raised"
    )
    probe = make_probe_evidence(
        request, run.calls[0], state="unknown", control_flow=control_flow
    )
    attach_quota_probe_evidence(error, probe)
    quota.probe_error = error
    coordinator, _, requests = make_coordinator(
        run,
        evidence,
        quota,
        order,
        selector=AttemptThenPause(run.calls[0]),
    )
    coordinator = replace(coordinator, prepare_quota_probe=FixedProbeRequest(request))
    return asyncio.create_task(coordinator.run()), probe, requests


async def test_probe_stop_latch_blocks_recovery_and_later_attempts() -> None:
    """Keep a stop raised by the probe adapter latched through settlement."""
    # Given
    order: list[str] = []
    run = bound_run(calls_count=2, config=configuration(quota=True))
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    request = make_probe_request(run)
    probe = make_probe_evidence(request, run.calls[0])
    quota.probe_result = probe
    quota.stop_reason = RuntimeError("probe cleanup unsafe")
    selection = AttemptThenPause(run.calls[0])
    coordinator, _, requests = make_coordinator(
        run, evidence, quota, order, selector=selection
    )
    coordinator = replace(coordinator, prepare_quota_probe=FixedProbeRequest(request))

    # When
    with pytest.raises(RuntimeError, match="stopped during quota probe"):
        await coordinator.run()

    # Then
    assert requests == [run.calls[0].request]
    assert evidence.probe_inputs == [probe]
    assert selection.decisions == 2
    assert evidence.final_records == []


async def test_repeated_cancellation_waits_for_attached_probe_evidence() -> None:
    """Finish the durable evidence write despite repeated owner cancellation."""
    # Given
    order: list[str] = []
    run = bound_run(config=configuration(quota=True))
    evidence = BlockingProbeEvidence(order)
    quota = FakeQuotaReader(order)
    cancellation = asyncio.CancelledError()
    run_task, probe, requests = start_probe_with_attached_failure(
        run, evidence, quota, cancellation, order
    )

    # When
    await evidence.write_started.wait()
    run_task.cancel()
    await asyncio.sleep(0)
    assert not run_task.done()
    assert not evidence.write_finished.is_set()
    run_task.cancel()
    await asyncio.sleep(0)
    assert not run_task.done()
    assert not evidence.write_finished.is_set()
    evidence.allow_write.set()

    # Then
    with pytest.raises(asyncio.CancelledError) as raised:
        await run_task
    assert raised.value is cancellation
    assert evidence.write_finished.is_set()
    assert evidence.probe_inputs == [probe]
    assert requests == [run.calls[0].request]
    assert evidence.final_records == []


async def test_owner_cancellation_wins_during_probe_failure_settlement() -> None:
    """Prefer owner cancellation after preserving attached failure evidence."""
    # Given
    order: list[str] = []
    run = bound_run(config=configuration(quota=True))
    evidence = BlockingProbeEvidence(order)
    quota = FakeQuotaReader(order)
    failure = RuntimeError("probe failed")
    run_task, probe, requests = start_probe_with_attached_failure(
        run, evidence, quota, failure, order
    )

    # When
    await evidence.write_started.wait()
    run_task.cancel()
    await asyncio.sleep(0)
    assert not run_task.done()
    assert not evidence.write_finished.is_set()
    evidence.allow_write.set()

    # Then
    with pytest.raises(asyncio.CancelledError) as raised:
        await run_task
    assert raised.value is not failure
    assert raised.value.__cause__ is failure
    assert "probe failed" in str(raised.value.__cause__)
    assert evidence.write_finished.is_set()
    assert evidence.probe_inputs == [probe]
    assert requests == [run.calls[0].request]
    assert evidence.final_records == []


async def test_dry_run_is_refused_before_dispatch_or_quota_effects() -> None:
    """Keep dry-run reporting outside coordinator execution and recovery."""
    # Given
    order: list[str] = []
    run = bound_run(config=configuration(quota=True, dry_run=True))
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    seen: list[_SettledAttempt | None] = []
    coordinator, _, _ = make_coordinator(
        run,
        evidence,
        quota,
        order,
        selector=selection_sequence([], seen),
    )

    # When
    with pytest.raises(ValueError, match="dry-run plans"):
        await coordinator.run()

    # Then
    assert seen == []
    assert quota.observations == 0 and quota.probes == 0
    assert evidence.events == []
