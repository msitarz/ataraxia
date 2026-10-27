# SPDX-License-Identifier: Apache-2.0
"""Coordinator decision wiring, evidence order, and paused recovery."""

import asyncio
from collections.abc import Callable
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
    QuotaWindowId,
    QuotaWindowObservation,
    RetryAssessment,
    RunRecord,
    WaitEvent,
)
from script.eval.runner.coordinator import (
    Coordinator,
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
    AttemptCancelled,
    AttemptObservation,
    AttemptRequest,
    AttemptResult,
    CapturedOutput,
    CleanupEvidence,
    Completed,
    DispatchStop,
    InfrastructureFailure,
    OutputLimitExceeded,
    SignalAttempt,
    TimedOut,
)


def configuration(
    *,
    quota: bool = False,
    dry_run: bool = False,
    concurrency: int = 1,
    quota_poll_interval: float = 7.5,
    retry_limit: int = 0,
    retry_nonzero_exit: bool = False,
    capacity_retry_limit: int = 0,
    quota_wait_limit: float | None = None,
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
        quota_wait_limit_seconds=quota_wait_limit,
        quota_poll_interval_seconds=quota_poll_interval,
        retry_limit=retry_limit,
        retry_nonzero_exit=retry_nonzero_exit,
        capacity_retry_limit=capacity_retry_limit,
        capacity_backoff_base_seconds=1.0 if capacity_retry_limit else None,
        capacity_backoff_cap_seconds=4.0 if capacity_retry_limit else None,
        instructions_file_path=None,
    )


def bound_run(
    *,
    calls_count: int = 1,
    config: HarnessConfig | None = None,
    quota_scope: QuotaScope | None = None,
) -> BoundRun:
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
            quota_scope=quota_scope,
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

    def __init__(self) -> None:
        self.delays: list[float] = []

    def utc_now(self) -> str:
        return "2026-10-27T10:00:00Z"

    def monotonic(self) -> float:
        return 1.0

    async def sleep(self, seconds: float, /) -> None:
        self.delays.append(seconds)
        await asyncio.sleep(0)

    def uniform(self, lower: float, upper: float, /) -> float:
        return lower


class FakeProgress(ProgressSink):
    """Retain any coordinator snapshots."""

    def __init__(self) -> None:
        self.snapshots: list[ProgressSnapshot] = []

    def publish(self, snapshot: ProgressSnapshot, /) -> None:
        self.snapshots.append(snapshot)


def assert_progress_partitions(progress: FakeProgress, planned: int) -> None:
    """Check every published snapshot partitions each lifecycle inventory."""
    assert progress.snapshots
    for snapshot in progress.snapshots:
        c = snapshot.counts
        assert (
            sum((
                c.calls_queued,
                c.calls_stopped_not_started,
                c.calls_active,
                c.calls_retry_wait,
                c.calls_evidence_pending,
                c.calls_succeeded,
                c.calls_failed,
                c.calls_cancelled,
            ))
            == planned
        )
        assert (
            sum((
                c.attempts_active,
                c.attempts_evidence_pending,
                c.attempts_succeeded,
                c.attempts_failed,
                c.attempts_cancelled,
            ))
            == c.attempts_started
        )
        assert (
            sum((
                c.probes_active,
                c.probes_evidence_pending,
                c.probes_completed,
                c.probes_failed,
                c.probes_cancelled,
            ))
            == c.probes_started
        )


def fake_outcome_kind(evidence: AttemptEvidence) -> str:
    """Project the outcome kind needed by in-memory coordinator evidence."""
    outcome = evidence.outcome
    if evidence.control_flow == "cancelled":
        return "cancelled"
    if evidence.control_flow == "raised" and outcome is None:
        return "unexpected_exception"
    if outcome is None:
        return "no_observation"
    if isinstance(outcome, TimedOut):
        return "timed_out"
    if isinstance(outcome, OutputLimitExceeded):
        return "output_limit_exceeded"
    if isinstance(outcome, InfrastructureFailure):
        return "infrastructure_failure"
    return "completed"


def fake_cleanup_record(evidence: AttemptEvidence) -> dict[str, object] | None:
    """Project only observed cleanup facts into a test attempt record."""
    observation = getattr(evidence.outcome, "observation", None)
    if observation is None:
        return None
    cleanup = observation.cleanup
    return {
        "process": cleanup.process,
        "signals": tuple(
            {
                "signal": item.signal,
                "outcome": item.outcome,
                "diagnostic": item.diagnostic,
            }
            for item in cleanup.signals
        ),
        "direct_wait": cleanup.direct_wait,
        "wait_diagnostic": cleanup.wait_diagnostic,
    }


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
        outcome = evidence.outcome
        outcome_kind = fake_outcome_kind(evidence)
        exit_status = getattr(outcome, "exit_status", None)
        observation = getattr(outcome, "observation", None)
        cleanup = fake_cleanup_record(evidence)
        record = AttemptRecord.model_validate({
            "run_id": run_id,
            "call_id": call_id,
            "position": position,
            "attempt_number": attempt_number,
            "control_flow": evidence.control_flow,
            "outcome_kind": outcome_kind,
            "started_at_utc": evidence.started_at_utc,
            "ended_at_utc": evidence.ended_at_utc,
            "argv": evidence.request.argv,
            "cwd": str(evidence.request.cwd),
            "timeout_seconds": 1.0,
            "cleanup_timeout_seconds": 1.0,
            "grace_seconds": 0.0,
            "output_limit_bytes": 0,
            "elapsed_seconds": None
            if observation is None
            else observation.elapsed_seconds,
            "elapsed_basis": "supervisor_observation",
            "exit_status": exit_status,
            "termination_reason": None,
            "cleanup": cleanup,
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


class BlockingAttemptEvidence(FakeEvidence):
    """Retain the attempt append while owner cancellation is delivered."""

    def __init__(self, order: list[str]) -> None:
        super().__init__(order)
        self.write_started = asyncio.Event()
        self.allow_write = asyncio.Event()

    @override
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
        self.write_started.set()
        await self.allow_write.wait()
        return await super().record_attempt(
            run_id,
            call_id,
            position,
            attempt_number,
            evidence,
            retry_assessment,
        )


class FailingAttemptEvidence(FakeEvidence):
    """Fail one required attempt write to test pending-evidence accounting."""

    @override
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
        raise OSError("attempt evidence write failed")


class BlockingFinalEvidence(FakeEvidence):
    """Pause finalization to exercise cancellation-safe final writes."""

    def __init__(self, order: list[str]) -> None:
        super().__init__(order)
        self.write_started = asyncio.Event()
        self.allow_write = asyncio.Event()

    @override
    async def finalize(self, record: RunRecord, /) -> None:
        self.write_started.set()
        await self.allow_write.wait()
        await super().finalize(record)


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
        self.probe_builder: Callable[[QuotaProbeRequest], QuotaProbeEvidence] | None = (
            None
        )
        self.probe_error: BaseException | None = None
        self.probe_error_factory: (
            Callable[[QuotaProbeRequest], BaseException] | None
        ) = None
        self.stop_reason: AttemptResult | BaseException | None = None
        self._scope: QuotaScope | None = None

    @property
    def expected_scope(self) -> QuotaScope | None:
        return self._scope

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
        if self.probe_error_factory is not None:
            raise self.probe_error_factory(request)
        if self.probe_error is not None:
            raise self.probe_error
        if self.probe_builder is not None:
            return self.probe_builder(request)
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


def successful_outcome() -> AttemptResult:
    """Return a safe completed supervisor result with captured bytes."""
    return Completed(
        observation=AttemptObservation(
            output=CapturedOutput(stdout=b"answer", stderr=b""),
            elapsed_seconds=0.5,
            cleanup=CleanupEvidence(
                "owned", (SignalAttempt("SIGKILL", "sent", None),), "reaped", None
            ),
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
) -> tuple[Coordinator, FakeClassifier, list[AttemptRequest]]:
    """Compose a bound coordinator with exact fake collaborators."""
    requests: list[AttemptRequest] = []
    classifier = FakeClassifier(order)
    quota._scope = run.binding.quota_scope
    coordinator = Coordinator(
        bound_run=run,
        evidence=evidence,
        attempt=make_attempt(order, [successful_outcome()] * len(run.calls), requests),
        classifier=classifier,
        quota_status=quota,
        runtime=FixedRuntime(),
        progress=FakeProgress(),
        capture_returned_attempt=capture_attempt,
    )
    return coordinator, classifier, requests


def report_exhausted_quota(
    run: BoundRun,
    quota: FakeQuotaReader,
    classifier: FakeClassifier,
    /,
) -> None:
    """Supply verified scoped exhaustion through the public quota port."""
    scope = run.binding.quota_scope
    assert scope is not None
    quota._scope = scope
    quota.observation = QuotaObservation(
        scope=scope,
        read_at_utc="2026-10-27T10:00:00Z",
        source_coordinate="session:1",
        windows=(
            QuotaWindowObservation(
                window_id=QuotaWindowId("primary"),
                state="exhausted",
                usage_percent=100.0,
                reset_at_utc=None,
                source_observed_at_utc="2026-10-27T10:00:00Z",
                source_sequence=1,
                source="test",
                diagnostic=None,
            ),
        ),
        diagnostic=None,
    )
    classifier.assessment = RetryAssessment(
        retry_class="quota",
        classification_basis="scoped exhausted test observation",
        no_result_basis="confident_absence",
        diagnostic=None,
    )


async def test_run_persists_attempt_before_passive_observation() -> None:
    """Persist the attempt before passing captured output to passive telemetry."""
    # Given
    order: list[str] = []
    run = bound_run(
        config=configuration(quota=True, concurrency=3, quota_poll_interval=8.5)
    )
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    coordinator, classifier, requests = make_coordinator(run, evidence, quota, order)

    # When
    actual = await coordinator.run()

    # Then
    settled = coordinator._state.settled[0]
    assert actual is evidence.final_records[0]
    assert coordinator.config is run.plan.configuration
    assert coordinator.config.concurrency == 3
    assert coordinator.config.quota_poll_interval_seconds == pytest.approx(8.5)
    assert requests == [run.calls[0].request]
    assert requests[0] is run.calls[0].request
    assert settled.call is run.calls[0]
    assert settled.record is evidence.attempt_records[0]
    assert settled.evidence is classifier.assessed[0]
    assert settled.evidence.usage_telemetry == b"answer"
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


async def test_passive_quota_progress_requires_reader_and_binding_scope_match() -> None:
    """Persist telemetry but withhold mismatched scope from progress recovery."""
    order: list[str] = []
    binding_scope = QuotaScope(
        provider_id=QuotaProviderId("codex"), allowance_id=QuotaAllowanceId("bound")
    )
    reader_scope = QuotaScope(
        provider_id=QuotaProviderId("codex"), allowance_id=QuotaAllowanceId("reader")
    )
    run = bound_run(config=configuration(quota=True), quota_scope=binding_scope)
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    quota.observation = QuotaObservation(
        scope=binding_scope,
        read_at_utc="2026-10-27T10:00:00Z",
        source_coordinate="test",
        windows=(),
        diagnostic=None,
    )
    coordinator, _, _ = make_coordinator(run, evidence, quota, order)
    quota._scope = reader_scope
    progress = FakeProgress()
    coordinator = replace(coordinator, progress=progress)

    await coordinator.run()

    assert evidence.telemetry_events[0].observation.scope == binding_scope
    assert progress.snapshots[-1].quota_observation is None


async def test_default_dispatch_runs_and_finalizes_the_frozen_plan() -> None:
    """Run each frozen position and persist its complete call accounting."""
    # Given
    order: list[str] = []
    run = bound_run()
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    requests: list[AttemptRequest] = []
    progress = FakeProgress()
    coordinator = Coordinator(
        bound_run=run,
        evidence=evidence,
        attempt=make_attempt(order, [successful_outcome()], requests),
        classifier=FakeClassifier(order),
        quota_status=quota,
        runtime=FixedRuntime(),
        progress=progress,
        capture_returned_attempt=capture_attempt,
    )

    # When
    actual = await coordinator.run()

    # Then
    assert requests == [run.calls[0].request]
    assert actual.state == "complete"
    assert actual.calls[0].state == "complete"
    assert len(actual.calls[0].attempts) == 1
    assert evidence.final_records == [actual]
    assert quota.observations == 0 and quota.probes == 0
    assert_progress_partitions(progress, 1)


async def test_attempt_stop_hook_refuses_a_later_planned_attempt() -> None:
    """Latch the supervisor stop hook before the default scheduler refills."""
    # Given
    order: list[str] = []
    run = bound_run(calls_count=2, config=configuration(concurrency=1))
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    attempt_hooks: list[DispatchStop] = []
    requests: list[AttemptRequest] = []
    coordinator, _, _ = make_coordinator(run, evidence, quota, order)
    coordinator = replace(
        coordinator,
        attempt=stopping_attempt(attempt_hooks, requests, successful_outcome()),
    )

    # When
    record = await coordinator.run()

    # Then
    assert requests == [run.calls[0].request]
    assert len(attempt_hooks) == 1
    assert len(evidence.attempt_inputs) == 1
    assert record.state == "incomplete"
    assert record.calls[1].state == "not_started"
    assert evidence.final_records == [record]


async def test_default_scheduler_honors_the_configured_concurrency_bound() -> None:
    """Run a matrix in plan order without exceeding its active-call limit."""
    # Given
    order: list[str] = []
    run = bound_run(calls_count=4, config=configuration(concurrency=2))
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    coordinator, _, requests = make_coordinator(run, evidence, quota, order)
    rendezvous = asyncio.Barrier(2)
    active = 0
    maximum_active = 0

    async def concurrent_attempt(
        request: AttemptRequest, stop: DispatchStop, /
    ) -> AttemptResult:
        nonlocal active, maximum_active
        active += 1
        maximum_active = max(maximum_active, active)
        await rendezvous.wait()
        active -= 1
        requests.append(request)
        return successful_outcome()

    coordinator = replace(coordinator, attempt=concurrent_attempt)

    # When
    record = await coordinator.run()

    # Then
    assert maximum_active == 2
    assert len(requests) == 4
    assert tuple(call.position for call in record.calls) == (0, 1, 2, 3)
    assert all(call.state == "complete" for call in record.calls)


async def test_unsafe_cleanup_stops_dispatch_and_accounts_for_unstarted_calls() -> None:
    """Stop after output overflow and retain every call's launch status."""
    # Given
    order: list[str] = []
    run = bound_run(calls_count=2)
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    coordinator, _, requests = make_coordinator(run, evidence, quota, order)
    overflow = OutputLimitExceeded(
        observation=AttemptObservation(
            None,
            0.1,
            CleanupEvidence(
                "owned", (SignalAttempt("SIGKILL", "sent", None),), "reaped", None
            ),
        ),
        exit_status=None,
    )

    async def overflowing_attempt(
        request: AttemptRequest, stop: DispatchStop, /
    ) -> AttemptResult:
        requests.append(request)
        await asyncio.sleep(0)
        return overflow

    progress = FakeProgress()
    coordinator = replace(coordinator, attempt=overflowing_attempt, progress=progress)

    # When
    record = await coordinator.run()

    # Then
    assert requests == [run.calls[0].request]
    assert record.state == "incomplete"
    assert tuple(call.state for call in record.calls) == ("failed", "not_started")
    assert progress.snapshots[-1].counts.calls_stopped_not_started == 1


async def test_attempt_cancellation_is_durable_then_propagated() -> None:
    """Persist cancellation accounting before re-raising supervisor cancellation."""
    # Given
    order: list[str] = []
    run = bound_run(calls_count=2)
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    coordinator, _, requests = make_coordinator(run, evidence, quota, order)
    cancellation = AttemptCancelled(
        AttemptObservation(
            None,
            0.1,
            CleanupEvidence(
                "owned", (SignalAttempt("SIGKILL", "sent", None),), "reaped", None
            ),
        )
    )

    async def cancelled_attempt(
        request: AttemptRequest, stop: DispatchStop, /
    ) -> AttemptResult:
        requests.append(request)
        await asyncio.sleep(0)
        raise cancellation

    progress = FakeProgress()
    coordinator = replace(coordinator, attempt=cancelled_attempt, progress=progress)

    # When
    with pytest.raises(asyncio.CancelledError) as raised:
        await coordinator.run()

    # Then
    assert raised.value is cancellation
    assert requests == [run.calls[0].request]
    assert evidence.final_records[0].state == "incomplete"
    assert evidence.final_records[0].calls[0].attempts[0].outcome_kind == "cancelled"
    assert progress.snapshots[-1].final_status == "cancelled"


async def test_unobserved_attempt_error_is_persisted_before_raising() -> None:
    """Retain no-observation evidence and classify the run as incomplete."""
    order: list[str] = []
    run = bound_run()
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    coordinator, _, requests = make_coordinator(run, evidence, quota, order)
    progress = FakeProgress()
    failure = RuntimeError("attempt escaped before observation")

    async def attempt(request: AttemptRequest, stop: DispatchStop, /) -> AttemptResult:
        await asyncio.sleep(0)
        requests.append(request)
        raise failure

    coordinator = replace(coordinator, attempt=attempt, progress=progress)
    with pytest.raises(
        RuntimeError, match="attempt escaped before observation"
    ) as raised:
        await coordinator.run()

    assert raised.value is failure
    stored = evidence.final_records[0]
    assert stored.state == "incomplete"
    assert stored.calls[0].attempts[0].control_flow == "raised"
    assert stored.calls[0].attempts[0].outcome_kind == "unexpected_exception"
    assert progress.snapshots[-1].final_status == "incomplete_evidence"


async def test_attempt_recording_failure_stays_evidence_pending() -> None:
    """Do not count an unpersisted attempt as a terminal failure."""
    order: list[str] = []
    run = bound_run()
    evidence = FailingAttemptEvidence(order)
    quota = FakeQuotaReader(order)
    coordinator, _, requests = make_coordinator(run, evidence, quota, order)
    progress = FakeProgress()

    async def attempt(request: AttemptRequest, stop: DispatchStop, /) -> AttemptResult:
        await asyncio.sleep(0)
        requests.append(request)
        return successful_outcome()

    coordinator = replace(coordinator, attempt=attempt, progress=progress)
    with pytest.raises(OSError, match="attempt evidence write failed"):
        await coordinator.run()

    assert requests == [run.calls[0].request]
    assert evidence.final_records[0].state == "incomplete"
    counts = progress.snapshots[-1].counts
    assert progress.snapshots[-1].final_status == "incomplete_evidence"
    assert counts.calls_evidence_pending == 1
    assert counts.attempts_evidence_pending == 1
    assert counts.attempts_failed == 0


async def test_repeated_cancellation_waits_for_attempt_evidence_write() -> None:
    """Retain the attempt write and finalize before propagating repeated cancel."""
    order: list[str] = []
    run = bound_run()
    evidence = BlockingAttemptEvidence(order)
    quota = FakeQuotaReader(order)
    coordinator, _, _ = make_coordinator(run, evidence, quota, order)
    progress = FakeProgress()
    coordinator = replace(coordinator, progress=progress)
    task = asyncio.create_task(coordinator.run())
    await evidence.write_started.wait()

    task.cancel()
    task.cancel()
    await asyncio.sleep(0)
    evidence.allow_write.set()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert len(evidence.attempt_records) == 1
    assert len(evidence.final_records) == 1
    assert evidence.final_records[0].state == "incomplete"
    assert evidence.final_records[0].calls[0].attempts[0].outcome_kind == "completed"
    assert progress.snapshots[-1].final_status == "cancelled"


async def test_repeated_cancellation_waits_for_finalization_write() -> None:
    """Settle final persistence exactly once before returning owner cancellation."""
    order: list[str] = []
    run = bound_run()
    evidence = BlockingFinalEvidence(order)
    quota = FakeQuotaReader(order)
    coordinator, _, _ = make_coordinator(run, evidence, quota, order)
    progress = FakeProgress()
    coordinator = replace(coordinator, progress=progress)
    task = asyncio.create_task(coordinator.run())
    await evidence.write_started.wait()

    task.cancel()
    task.cancel()
    await asyncio.sleep(0)
    evidence.allow_write.set()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert len(evidence.final_records) == 1
    assert evidence.final_records[0].state == "complete"
    assert progress.snapshots[-1].final_status == "cancelled"


async def test_infrastructure_retry_uses_its_finite_allowance() -> None:
    """Retry one confidently absent result and retain both attempt records."""
    # Given
    order: list[str] = []
    run = bound_run(config=configuration(retry_limit=1))
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    coordinator, classifier, requests = make_coordinator(run, evidence, quota, order)
    classifier.assessment = RetryAssessment(
        retry_class="infrastructure",
        classification_basis="supervisor no-launch evidence",
        no_result_basis="confident_absence",
        diagnostic=None,
    )
    cleanup = CleanupEvidence("not_started", (), "not_started", None)
    absent = InfrastructureFailure(
        observation=AttemptObservation(None, 0.1, cleanup),
        exit_status=None,
        error_type="launch_error",
        diagnostic="no process was launched",
    )
    outcomes = iter((absent, successful_outcome()))

    async def retrying_attempt(
        request: AttemptRequest, stop: DispatchStop, /
    ) -> AttemptResult:
        await asyncio.sleep(0)
        requests.append(request)
        return next(outcomes)

    coordinator = replace(coordinator, attempt=retrying_attempt)

    # When
    record = await coordinator.run()

    # Then
    assert len(requests) == 2
    assert [item.attempt_number for item in record.calls[0].attempts] == [1, 2]
    assert record.calls[0].state == "complete"
    assert record.calls[0].attempts[0].retry_assessment == classifier.assessment


async def test_infrastructure_and_capacity_allowances_are_independent() -> None:
    """A previous infrastructure retry does not spend capacity allowance."""
    order: list[str] = []
    run = bound_run(config=configuration(retry_limit=1, capacity_retry_limit=1))
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    coordinator, _, requests = make_coordinator(run, evidence, quota, order)
    absent = CleanupEvidence("not_started", (), "not_started", None)
    outcomes = iter((
        InfrastructureFailure(
            observation=AttemptObservation(None, 0.1, absent),
            exit_status=None,
            error_type="launch_error",
            diagnostic="launch failed",
        ),
        InfrastructureFailure(
            observation=AttemptObservation(None, 0.1, absent),
            exit_status=None,
            error_type="capacity",
            diagnostic="capacity exhausted",
        ),
        successful_outcome(),
    ))

    class AlternatingClassifier(FakeClassifier):
        """Classify each supervisor result as its independent failure category."""

        def __init__(self, order: list[str]) -> None:
            super().__init__(order)
            self.assessments = iter((
                RetryAssessment(
                    retry_class="infrastructure",
                    classification_basis="launch failure",
                    no_result_basis="confident_absence",
                    diagnostic=None,
                ),
                RetryAssessment(
                    retry_class="capacity",
                    classification_basis="capacity signal",
                    no_result_basis="confident_absence",
                    diagnostic=None,
                ),
                RetryAssessment(
                    retry_class="unknown",
                    classification_basis=None,
                    no_result_basis="present_or_unknown",
                    diagnostic=None,
                ),
            ))

        @override
        def assess(self, evidence: AttemptEvidence, /) -> RetryAssessment:
            self.order.append("classify")
            self.assessed.append(evidence)
            return next(self.assessments)

    classifier = AlternatingClassifier(order)

    async def attempt(request: AttemptRequest, stop: DispatchStop, /) -> AttemptResult:
        await asyncio.sleep(0)
        requests.append(request)
        return next(outcomes)

    coordinator = replace(coordinator, classifier=classifier, attempt=attempt)
    record = await coordinator.run()

    assert len(record.calls[0].attempts) == 3
    assert len(requests) == 3
    assert tuple(wait.context.kind for wait in record.waits) == ("capacity",)


async def test_nonzero_completed_result_requires_explicit_retry_opt_in() -> None:  # ruff: ignore[too-many-statements]
    """Never retry a completed nonzero exit unless the plan opts in."""
    order: list[str] = []
    run = bound_run(config=configuration(retry_limit=1))
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    coordinator, classifier, requests = make_coordinator(run, evidence, quota, order)
    classifier.assessment = RetryAssessment(
        retry_class="infrastructure",
        classification_basis="supervisor nonzero exit",
        no_result_basis="confident_absence",
        diagnostic=None,
    )
    failed = Completed(
        AttemptObservation(
            CapturedOutput(b"", b""),
            0.1,
            CleanupEvidence(
                "owned", (SignalAttempt("SIGKILL", "sent", None),), "reaped", None
            ),
        ),
        exit_status=17,
    )

    async def attempt(request: AttemptRequest, stop: DispatchStop, /) -> AttemptResult:
        await asyncio.sleep(0)
        requests.append(request)
        return failed

    coordinator = replace(coordinator, attempt=attempt)
    record = await coordinator.run()
    assert len(requests) == 1
    assert record.calls[0].state == "failed"

    opted_run = bound_run(config=configuration(retry_limit=1, retry_nonzero_exit=True))
    opted_evidence = FakeEvidence([])
    opted_quota = FakeQuotaReader([])
    opted, opted_classifier, opted_requests = make_coordinator(
        opted_run, opted_evidence, opted_quota, []
    )
    opted_classifier.assessment = classifier.assessment
    assert opted.config.retry_nonzero_exit
    assert opted_classifier.assessment.retry_class == "infrastructure"
    outcomes = iter((failed, successful_outcome()))

    async def opted_attempt(
        request: AttemptRequest, stop: DispatchStop, /
    ) -> AttemptResult:
        await asyncio.sleep(0)
        opted_requests.append(request)
        return next(outcomes)

    opted = replace(opted, attempt=opted_attempt)
    opted_record = await opted.run()
    assert len(opted_requests) == 2
    assert opted_record.calls[0].state == "complete"


async def test_capacity_retry_persists_its_zero_jitter_wait() -> None:
    """Record capacity backoff before an independent retry invocation."""
    # Given
    order: list[str] = []
    run = bound_run(config=configuration(capacity_retry_limit=1))
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    coordinator, classifier, requests = make_coordinator(run, evidence, quota, order)
    runtime = FixedRuntime()
    progress = FakeProgress()
    coordinator = replace(coordinator, runtime=runtime, progress=progress)
    classifier.assessment = RetryAssessment(
        retry_class="capacity",
        classification_basis="typed transient-capacity signal",
        no_result_basis="confident_absence",
        diagnostic=None,
    )
    absent = InfrastructureFailure(
        observation=AttemptObservation(
            None, 0.1, CleanupEvidence("not_started", (), "not_started", None)
        ),
        exit_status=None,
        error_type="capacity",
        diagnostic="no result was produced",
    )
    outcomes = iter((absent, successful_outcome()))

    async def attempt(request: AttemptRequest, stop: DispatchStop, /) -> AttemptResult:
        requests.append(request)
        await asyncio.sleep(0)
        return next(outcomes)

    coordinator = replace(coordinator, attempt=attempt)

    # When
    record = await coordinator.run()

    # Then
    assert len(requests) == 2
    assert runtime.delays == [0.0]
    assert [attempt.attempt_number for attempt in record.calls[0].attempts] == [1, 2]
    assert len(record.waits) == 1
    assert record.waits[0].end == "delay_elapsed"
    assert record.waits[0].context.kind == "capacity"
    assert_progress_partitions(progress, 1)


async def test_cancellation_during_capacity_wait_is_reported_as_cancelled() -> None:  # ruff: ignore[too-many-statements]
    """Keep run cancellation distinct when no retry process is active."""
    order: list[str] = []
    run = bound_run(calls_count=2, config=configuration(capacity_retry_limit=1))
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    coordinator, classifier, _ = make_coordinator(run, evidence, quota, order)
    waiting = asyncio.Event()

    class WaitingRuntime(FixedRuntime):
        @override
        async def sleep(self, seconds: float, /) -> None:
            self.delays.append(seconds)
            waiting.set()
            await asyncio.Event().wait()

    coordinator = replace(coordinator, runtime=WaitingRuntime())
    classifier.assessment = RetryAssessment(
        retry_class="capacity",
        classification_basis="typed transient-capacity signal",
        no_result_basis="confident_absence",
        diagnostic=None,
    )
    absent = InfrastructureFailure(
        observation=AttemptObservation(
            None, 0.1, CleanupEvidence("not_started", (), "not_started", None)
        ),
        exit_status=None,
        error_type="capacity",
        diagnostic="no result was produced",
    )
    progress = FakeProgress()

    async def attempt(request: AttemptRequest, stop: DispatchStop, /) -> AttemptResult:
        await asyncio.sleep(0)
        return absent

    coordinator = replace(
        coordinator,
        attempt=attempt,
        progress=progress,
    )
    task = asyncio.create_task(coordinator.run())
    await waiting.wait()
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    assert evidence.final_records[0].state == "incomplete"
    assert tuple(call.state for call in evidence.final_records[0].calls) == (
        "failed",
        "failed",
    )
    final = progress.snapshots[-1]
    assert final.final_status == "cancelled"
    assert final.counts.calls_cancelled == 2
    assert final.counts.calls_stopped_not_started == 0


async def test_default_attempt_conversion_preserves_supervisor_observations() -> None:
    """Persist the returned supervisor outcome with its original request."""
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
    )

    # When
    actual = await coordinator.run()

    # Then
    assert requests == [run.calls[0].request]
    assert evidence.attempt_inputs[0][4].outcome == successful_outcome()
    assert actual.calls[0].attempts[0].exit_status == 0
    assert evidence.final_records == [actual]


async def test_quota_pause_waits_for_one_fresh_scoped_available_probe() -> None:  # ruff: ignore[too-many-statements]
    """Gate later calls until fresh, matching quota evidence is persisted."""
    # Given
    order: list[str] = []
    scope = QuotaScope(
        provider_id=QuotaProviderId("codex"),
        allowance_id=QuotaAllowanceId("allowance-a"),
    )
    run = bound_run(
        calls_count=2,
        config=configuration(quota=True, retry_limit=0),
        quota_scope=scope,
    )
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    quota.observation = QuotaObservation(
        scope=scope,
        read_at_utc="2026-10-27T10:00:00Z",
        source_coordinate="session:1",
        windows=(
            QuotaWindowObservation(
                window_id=QuotaWindowId("primary"),
                state="exhausted",
                usage_percent=100.0,
                reset_at_utc=None,
                source_observed_at_utc="2026-10-27T10:00:00Z",
                source_sequence=1,
                source="test",
                diagnostic=None,
            ),
        ),
        diagnostic=None,
    )
    coordinator, classifier, requests = make_coordinator(run, evidence, quota, order)
    runtime = FixedRuntime()
    progress = FakeProgress()
    coordinator = replace(coordinator, runtime=runtime, progress=progress)
    classifier.assessment = RetryAssessment(
        retry_class="quota",
        classification_basis="scoped exhausted observation",
        no_result_basis="confident_absence",
        diagnostic=None,
    )
    absent = InfrastructureFailure(
        observation=AttemptObservation(
            None, 0.1, CleanupEvidence("not_started", (), "not_started", None)
        ),
        exit_status=None,
        error_type="quota",
        diagnostic="quota exhausted before a result",
    )

    attempt_counts: dict[str, int] = {}

    async def attempt(request: AttemptRequest, stop: DispatchStop, /) -> AttemptResult:
        position = request.argv[-1]
        requests.append(request)
        attempt_counts[position] = attempt_counts.get(position, 0) + 1
        await asyncio.sleep(0)
        if position == "0" and attempt_counts[position] == 1:
            classifier.assessment = RetryAssessment(
                retry_class="quota",
                classification_basis="scoped exhausted observation",
                no_result_basis="confident_absence",
                diagnostic=None,
            )
            return absent
        classifier.assessment = RetryAssessment(
            retry_class="unknown",
            classification_basis=None,
            no_result_basis="present_or_unknown",
            diagnostic=None,
        )
        return successful_outcome()

    def build_probe(request: QuotaProbeRequest) -> QuotaProbeEvidence:
        base = make_probe_evidence(request, run.calls[0])
        available = QuotaObservation(
            scope=scope,
            read_at_utc="2026-10-27T10:00:00Z",
            source_coordinate="session:2",
            windows=(
                QuotaWindowObservation(
                    window_id=QuotaWindowId("primary"),
                    state="available",
                    usage_percent=10.0,
                    reset_at_utc=None,
                    source_observed_at_utc=request.poll_started_at_utc,
                    source_sequence=2,
                    source="test",
                    diagnostic=None,
                ),
            ),
            diagnostic=None,
        )
        return replace(base, observation=available)

    quota.probe_builder = build_probe
    coordinator = replace(coordinator, attempt=attempt)

    # When
    record = await coordinator.run()

    # Then
    assert quota.probes == 1
    assert runtime.delays == [7.5]
    assert record.waits[0].end == "quota_available"
    assert [attempt.outcome_kind for attempt in record.calls[0].attempts] == [
        "infrastructure_failure",
        "completed",
    ]
    assert record.calls[0].state == "complete"
    assert record.calls[1].state == "complete"
    assert record.calls[0].attempts[1].attempt_number == 2
    assert_progress_partitions(progress, 2)
    assert any(
        snapshot.counts.probes_completed == 1
        and snapshot.quota_observation is not None
        and snapshot.quota_observation.source_coordinate == "session:2"
        for snapshot in progress.snapshots
    )
    assert any(
        snapshot.phase == "quota_paused" and snapshot.counts.probes_started == 0
        for snapshot in progress.snapshots
    )
    assert any(
        snapshot.phase == "quota_paused" and snapshot.counts.probes_started == 1
        for snapshot in progress.snapshots
    )


async def test_quota_recovery_never_repeats_a_completed_semantic_call() -> None:
    """Exhaustion pauses dispatch but only confident absence permits a retry."""
    order: list[str] = []
    scope = QuotaScope(
        provider_id=QuotaProviderId("codex"), allowance_id=QuotaAllowanceId("a")
    )
    run = bound_run(config=configuration(quota=True), quota_scope=scope)
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    coordinator, classifier, requests = make_coordinator(run, evidence, quota, order)
    report_exhausted_quota(run, quota, classifier)
    classifier.assessment = classifier.assessment.model_copy(
        update={"no_result_basis": "present_or_unknown"}
    )

    def available_probe(request: QuotaProbeRequest) -> QuotaProbeEvidence:
        base = make_probe_evidence(request, run.calls[0])
        available = QuotaObservation(
            scope=scope,
            read_at_utc="2026-10-27T10:00:00Z",
            source_coordinate="session:2",
            windows=(
                QuotaWindowObservation(
                    window_id=QuotaWindowId("primary"),
                    state="available",
                    usage_percent=5.0,
                    reset_at_utc=None,
                    source_observed_at_utc=request.poll_started_at_utc,
                    source_sequence=2,
                    source="test",
                    diagnostic=None,
                ),
            ),
            diagnostic=None,
        )
        return replace(base, observation=available)

    quota.probe_builder = available_probe
    record = await coordinator.run()

    assert quota.probes == 1
    assert requests == [run.calls[0].request]
    assert len(record.calls[0].attempts) == 1
    assert record.calls[0].state == "complete"


async def test_probe_failure_persists_attached_evidence_and_finalizes() -> None:
    """Persist attached probe facts and retain the adapter failure as primary."""
    order: list[str] = []
    scope = QuotaScope(
        provider_id=QuotaProviderId("codex"), allowance_id=QuotaAllowanceId("a")
    )
    run = bound_run(config=configuration(quota=True), quota_scope=scope)
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    coordinator, classifier, attempts = make_coordinator(run, evidence, quota, order)
    report_exhausted_quota(run, quota, classifier)
    error = RuntimeError("probe failed")
    probes: list[QuotaProbeEvidence] = []

    def make_error(request: QuotaProbeRequest) -> BaseException:
        probe = make_probe_evidence(
            request, run.calls[0], state="unknown", control_flow="raised"
        )
        probes.append(probe)
        attach_quota_probe_evidence(error, probe)
        return error

    quota.probe_error_factory = make_error

    with pytest.raises(RuntimeError, match="probe failed") as raised:
        await coordinator.run()

    assert raised.value is error
    assert evidence.probe_inputs == probes
    assert evidence.probe_inputs[0].request is quota.requests[0]
    assert attempts == [run.calls[0].request]
    assert evidence.final_records[0].state == "incomplete"
    assert evidence.events[-1] == "final"


async def test_stop_during_probe_start_does_not_poll_or_resume() -> None:
    """A stop racing durable start prevents polling and leaves an incomplete run."""
    order: list[str] = []
    scope = QuotaScope(
        provider_id=QuotaProviderId("codex"), allowance_id=QuotaAllowanceId("a")
    )
    run = bound_run(calls_count=2, config=configuration(quota=True), quota_scope=scope)

    class StopOnStartedEvidence(FakeEvidence):
        """Latch a concurrent stop while the started event is being appended."""

        stop: DispatchStop | None = None

        @override
        async def record_quota_probe_event(
            self, event: QuotaProbeLifecycleInput, /
        ) -> None:
            await super().record_quota_probe_event(event)
            if isinstance(event, QuotaProbeStarted):
                assert self.stop is not None
                self.stop(RuntimeError("stop during started append"))

    evidence = StopOnStartedEvidence(order)
    quota = FakeQuotaReader(order)
    coordinator, classifier, requests = make_coordinator(run, evidence, quota, order)
    report_exhausted_quota(run, quota, classifier)

    async def attempt(request: AttemptRequest, stop: DispatchStop, /) -> AttemptResult:
        await asyncio.sleep(0)
        return InfrastructureFailure(
            observation=AttemptObservation(
                None, 0.1, CleanupEvidence("not_started", (), "not_started", None)
            ),
            exit_status=None,
            error_type="quota",
            diagnostic="quota exhausted before result",
        )

    async def stopping_attempt(
        request: AttemptRequest, stop: DispatchStop, /
    ) -> AttemptResult:
        requests.append(request)
        evidence.stop = stop
        return await attempt(request, stop)

    coordinator = replace(coordinator, attempt=stopping_attempt)
    evidence.stop = None
    record = await coordinator.run()

    assert quota.probes == 0
    assert len(requests) == 1
    assert record.state == "incomplete"
    assert len(record.calls) == 2
    assert record.calls[1].state == "not_started"
    assert any(isinstance(event, QuotaProbeStarted) for event in evidence.probe_events)
    assert evidence.probe_inputs == []


async def test_probe_failure_without_evidence_finalizes_incomplete_run() -> None:
    """Stop on missing probe facts and preserve a truthful partial run record."""
    order: list[str] = []
    scope = QuotaScope(
        provider_id=QuotaProviderId("codex"), allowance_id=QuotaAllowanceId("a")
    )
    run = bound_run(config=configuration(quota=True), quota_scope=scope)
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    coordinator, classifier, requests = make_coordinator(run, evidence, quota, order)
    report_exhausted_quota(run, quota, classifier)
    error = RuntimeError("probe evidence unavailable")
    quota.probe_error = error

    with pytest.raises(RuntimeError, match="probe evidence unavailable"):
        await coordinator.run()

    record = evidence.final_records[0]
    assert requests == [run.calls[0].request]
    assert evidence.probe_inputs == []
    assert record.state == "incomplete"
    assert tuple(call.state for call in record.calls) == ("complete",)


async def test_cumulative_quota_bound_interrupts_a_slow_probe() -> None:
    """Enforce the finite pause limit while the quota port is polling."""
    from time import monotonic

    order: list[str] = []
    scope = QuotaScope(
        provider_id=QuotaProviderId("codex"), allowance_id=QuotaAllowanceId("a")
    )
    run = bound_run(
        config=configuration(
            quota=True, quota_poll_interval=0.001, quota_wait_limit=0.02
        ),
        quota_scope=scope,
    )
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    coordinator, classifier, requests = make_coordinator(run, evidence, quota, order)
    report_exhausted_quota(run, quota, classifier)

    class RealRuntime(FixedRuntime):
        """Advance only the monotonic clock used for bounded wait accounting."""

        @override
        def monotonic(self) -> float:
            return monotonic()

    class SlowQuotaReader(FakeQuotaReader):
        """Hold the active poll until the coordinator's cumulative bound fires."""

        @override
        async def poll(
            self, request: QuotaProbeRequest, stop_dispatch: DispatchStop, /
        ) -> QuotaProbeEvidence:
            self.probes += 1
            self.requests.append(request)
            await asyncio.Event().wait()
            raise AssertionError("the finite quota timeout must cancel this poll")

    slow_quota = SlowQuotaReader(order)
    slow_quota._scope = scope
    slow_quota.observation = quota.observation
    coordinator = replace(coordinator, runtime=RealRuntime(), quota_status=slow_quota)

    async def attempt(request: AttemptRequest, stop: DispatchStop, /) -> AttemptResult:
        await asyncio.sleep(0)
        requests.append(request)
        return InfrastructureFailure(
            observation=AttemptObservation(
                None, 0.1, CleanupEvidence("not_started", (), "not_started", None)
            ),
            exit_status=None,
            error_type="quota",
            diagnostic="quota exhausted before result",
        )

    coordinator = replace(coordinator, attempt=attempt)
    record = await coordinator.run()

    assert slow_quota.probes == 1
    assert record.state == "incomplete"
    assert record.waits[0].end == "bound"
    assert coordinator._state.pending_probes == 1
    assert len(requests) == 1


async def test_cancelled_probe_evidence_finalizes_before_propagating() -> None:
    """Persist probe cancellation evidence and the incomplete run before raising."""
    order: list[str] = []
    scope = QuotaScope(
        provider_id=QuotaProviderId("codex"), allowance_id=QuotaAllowanceId("a")
    )
    run = bound_run(config=configuration(quota=True), quota_scope=scope)
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    coordinator, classifier, requests = make_coordinator(run, evidence, quota, order)
    report_exhausted_quota(run, quota, classifier)
    cancellation = asyncio.CancelledError("probe cancelled")
    probes: list[QuotaProbeEvidence] = []

    def make_error(request: QuotaProbeRequest) -> BaseException:
        probe = make_probe_evidence(
            request, run.calls[0], state="unknown", control_flow="cancelled"
        )
        probes.append(probe)
        attach_quota_probe_evidence(cancellation, probe)
        return cancellation

    quota.probe_error_factory = make_error
    with pytest.raises(asyncio.CancelledError) as raised:
        await coordinator.run()

    assert raised.value is cancellation
    assert evidence.probe_inputs == probes
    assert evidence.final_records[0].state == "incomplete"
    assert requests == [run.calls[0].request]


def start_probe_with_attached_failure(
    run: BoundRun,
    evidence: BlockingProbeEvidence,
    quota: FakeQuotaReader,
    error: BaseException,
    order: list[str],
    /,
) -> tuple[asyncio.Task[RunRecord], list[QuotaProbeEvidence], list[AttemptRequest]]:
    """Start the default recovery flow with failure facts tied to its request."""
    coordinator, classifier, requests = make_coordinator(run, evidence, quota, order)
    report_exhausted_quota(run, quota, classifier)
    probes: list[QuotaProbeEvidence] = []
    control_flow: Literal["cancelled", "raised"] = (
        "cancelled" if isinstance(error, asyncio.CancelledError) else "raised"
    )

    def make_error(request: QuotaProbeRequest) -> BaseException:
        probe = make_probe_evidence(
            request, run.calls[0], state="unknown", control_flow=control_flow
        )
        probes.append(probe)
        attach_quota_probe_evidence(error, probe)
        return error

    quota.probe_error_factory = make_error
    return asyncio.create_task(coordinator.run()), probes, requests


async def test_probe_stop_latch_blocks_resumption_and_queued_call() -> None:
    """Do not resume or dispatch after the probe port latches a stop reason."""
    order: list[str] = []
    scope = QuotaScope(
        provider_id=QuotaProviderId("codex"), allowance_id=QuotaAllowanceId("a")
    )
    run = bound_run(
        calls_count=3,
        config=configuration(quota=True, concurrency=2),
        quota_scope=scope,
    )
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    coordinator, classifier, requests = make_coordinator(run, evidence, quota, order)
    report_exhausted_quota(run, quota, classifier)
    quota.stop_reason = RuntimeError("probe cleanup unsafe")
    quota.probe_builder = lambda request: make_probe_evidence(
        request, run.calls[0], state="available"
    )

    record = await coordinator.run()

    assert requests == [run.calls[0].request, run.calls[1].request]
    assert quota.probes == 1
    assert record.state == "incomplete"
    assert record.calls[2].state == "not_started"
    assert evidence.final_records == [record]


async def test_repeated_cancellation_waits_for_attached_probe_evidence() -> None:
    """Finish durable probe evidence and finalization despite repeated cancellation."""
    order: list[str] = []
    scope = QuotaScope(
        provider_id=QuotaProviderId("codex"), allowance_id=QuotaAllowanceId("a")
    )
    run = bound_run(config=configuration(quota=True), quota_scope=scope)
    evidence = BlockingProbeEvidence(order)
    quota = FakeQuotaReader(order)
    cancellation = asyncio.CancelledError()
    run_task, probes, requests = start_probe_with_attached_failure(
        run, evidence, quota, cancellation, order
    )

    await evidence.write_started.wait()
    run_task.cancel()
    await asyncio.sleep(0)
    assert not run_task.done()
    assert not evidence.write_finished.is_set()
    run_task.cancel()
    await asyncio.sleep(0)
    assert not run_task.done()
    evidence.allow_write.set()

    with pytest.raises(asyncio.CancelledError) as raised:
        await run_task
    assert raised.value is cancellation
    assert evidence.write_finished.is_set()
    assert evidence.probe_inputs == probes
    assert requests == [run.calls[0].request]
    assert evidence.final_records[0].state == "incomplete"


async def test_owner_cancellation_wins_during_probe_failure_settlement() -> None:
    """Keep owner cancellation primary after preserving attached probe failure."""
    order: list[str] = []
    scope = QuotaScope(
        provider_id=QuotaProviderId("codex"), allowance_id=QuotaAllowanceId("a")
    )
    run = bound_run(config=configuration(quota=True), quota_scope=scope)
    evidence = BlockingProbeEvidence(order)
    quota = FakeQuotaReader(order)
    failure = RuntimeError("probe failed")
    run_task, probes, requests = start_probe_with_attached_failure(
        run, evidence, quota, failure, order
    )

    await evidence.write_started.wait()
    run_task.cancel()
    await asyncio.sleep(0)
    assert not run_task.done()
    evidence.allow_write.set()

    with pytest.raises(asyncio.CancelledError) as raised:
        await run_task
    assert raised.value is not failure
    assert raised.value.__cause__ is failure
    assert "probe failed" in str(raised.value.__cause__)
    assert evidence.write_finished.is_set()
    assert evidence.probe_inputs == probes
    assert requests == [run.calls[0].request]
    assert evidence.final_records[0].state == "incomplete"


async def test_dry_run_is_refused_before_dispatch_or_quota_effects() -> None:
    """Keep dry-run reporting outside coordinator execution and recovery."""
    # Given
    order: list[str] = []
    run = bound_run(config=configuration(quota=True, dry_run=True))
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    coordinator, _, _ = make_coordinator(run, evidence, quota, order)

    # When
    with pytest.raises(ValueError, match="dry-run plans"):
        await coordinator.run()

    # Then
    assert quota.observations == 0 and quota.probes == 0
    assert evidence.events == []


@pytest.mark.parametrize(
    ("category", "limit", "expected"),
    [
        ("infrastructure", 0, 1),
        ("infrastructure", 1, 2),
        ("capacity", 0, 1),
        ("capacity", 1, 2),
    ],
)
async def test_retry_limits_bound_repeated_failures(
    category: Literal["infrastructure", "capacity"], limit: int, expected: int
) -> None:
    # Given
    order: list[str] = []
    run = bound_run(
        config=configuration(
            retry_limit=limit if category == "infrastructure" else 0,
            capacity_retry_limit=limit if category == "capacity" else 0,
        )
    )
    evidence = FakeEvidence(order)
    coordinator, classifier, requests = make_coordinator(
        run, evidence, FakeQuotaReader(order), order
    )
    classifier.assessment = RetryAssessment(
        retry_class=category,
        classification_basis="failure",
        no_result_basis="confident_absence",
        diagnostic=None,
    )
    absent = InfrastructureFailure(
        AttemptObservation(
            None, 0.1, CleanupEvidence("not_started", (), "not_started", None)
        ),
        None,
        "failure",
        "no process launched",
    )
    coordinator = replace(
        coordinator, attempt=make_attempt(order, [absent] * 4, requests)
    )

    # When
    record = await coordinator.run()

    # Then
    assert len(requests) == expected
    assert len(record.calls[0].attempts) == expected
    assert record.calls[0].state == "failed"


class FailingFinalEvidence(BlockingFinalEvidence):
    """Fail after the owner has been cancelled while the write is shielded."""

    @override
    async def finalize(self, record: RunRecord, /) -> None:
        self.write_started.set()
        await self.allow_write.wait()
        raise OSError("final write failed")


async def test_cancellation_remains_primary_when_final_write_fails() -> None:
    # Given
    order: list[str] = []
    evidence = FailingFinalEvidence(order)
    coordinator, _, _ = make_coordinator(
        bound_run(), evidence, FakeQuotaReader(order), order
    )
    task = asyncio.create_task(coordinator.run())
    await evidence.write_started.wait()

    # When
    task.cancel("original cancellation")
    await asyncio.sleep(0)
    task.cancel("repeated cancellation")
    evidence.allow_write.set()
    with pytest.raises(asyncio.CancelledError, match="original cancellation") as raised:
        await task

    # Then
    assert isinstance(raised.value.__cause__, OSError)
    assert str(raised.value.__cause__) == "final write failed"
    assert not any(
        t.get_name().startswith("eval-evidence-") for t in asyncio.all_tasks()
    )


async def test_quota_recovery_retries_nonzero_without_ordinary_retry_opt_in() -> None:
    # Given
    order: list[str] = []
    scope = QuotaScope(
        provider_id=QuotaProviderId("codex"), allowance_id=QuotaAllowanceId("account-a")
    )
    run = bound_run(config=configuration(quota=True), quota_scope=scope)
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    coordinator, classifier, requests = make_coordinator(run, evidence, quota, order)
    report_exhausted_quota(run, quota, classifier)
    failed = Completed(
        AttemptObservation(
            CapturedOutput(b"", b"quota exhausted"),
            0.1,
            CleanupEvidence(
                "owned", (SignalAttempt("SIGKILL", "sent", None),), "reaped", None
            ),
        ),
        1,
    )

    def available_probe(request: QuotaProbeRequest) -> QuotaProbeEvidence:
        probe = make_probe_evidence(request, run.calls[0])
        window = QuotaWindowObservation(
            window_id=QuotaWindowId("primary"),
            state="available",
            usage_percent=10.0,
            reset_at_utc=None,
            source_observed_at_utc=request.poll_started_at_utc,
            source_sequence=2,
            source="test",
            diagnostic=None,
        )
        return replace(
            probe,
            observation=QuotaObservation(
                scope=scope,
                read_at_utc="2026-10-27T10:00:00Z",
                source_coordinate="session:2",
                windows=(window,),
                diagnostic=None,
            ),
        )

    quota.probe_builder = available_probe

    async def attempt(request: AttemptRequest, stop: DispatchStop, /) -> AttemptResult:
        await asyncio.sleep(0)
        requests.append(request)
        if len(requests) == 1:
            return failed
        classifier.assessment = RetryAssessment(
            retry_class="unknown",
            classification_basis=None,
            no_result_basis="present_or_unknown",
            diagnostic=None,
        )
        return successful_outcome()

    coordinator = replace(coordinator, attempt=attempt)

    # When
    record = await coordinator.run()

    # Then
    assert quota.probes == 1
    assert len(requests) == 2
    assert requests[0] == requests[1]
    assert record.calls[0].state == "complete"


class BlockingFailingAttemptEvidence(BlockingAttemptEvidence):
    """Fail the blocked attempt write after cancellation."""

    @override
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
        self.write_started.set()
        await self.allow_write.wait()
        raise OSError("attempt write failed")


async def test_cancellation_retains_failure_of_blocked_attempt_write() -> None:
    # Given
    order: list[str] = []
    evidence = BlockingFailingAttemptEvidence(order)
    coordinator, _, _ = make_coordinator(
        bound_run(), evidence, FakeQuotaReader(order), order
    )
    task = asyncio.create_task(coordinator.run())
    await evidence.write_started.wait()

    # When
    task.cancel("owner cancellation")
    await asyncio.sleep(0)
    evidence.allow_write.set()
    with pytest.raises(asyncio.CancelledError) as raised:
        await task

    # Then
    assert "attempt write failed" in str(raised.value.__cause__) or any(
        "attempt write failed" in note
        for note in getattr(raised.value, "__notes__", ())
    )
    assert len(evidence.final_records) == 1
    assert not any(
        t.get_name().startswith("eval-evidence-") for t in asyncio.all_tasks()
    )


@pytest.mark.parametrize(
    "outcome",
    [
        OutputLimitExceeded(
            AttemptObservation(
                None,
                0.1,
                CleanupEvidence(
                    "owned", (SignalAttempt("SIGKILL", "sent", None),), "reaped", None
                ),
            ),
            None,
        ),
        Completed(
            AttemptObservation(
                None, 0.1, CleanupEvidence("owned", (), "failed", "wait failed")
            ),
            0,
        ),
    ],
    ids=["output-limit", "unsafe-cleanup"],
)
async def test_final_call_unsafe_stop_leaves_run_incomplete(
    outcome: AttemptResult,
) -> None:
    # Given
    order: list[str] = []
    run = bound_run()
    evidence = FakeEvidence(order)
    coordinator, _, requests = make_coordinator(
        run, evidence, FakeQuotaReader(order), order
    )
    progress = FakeProgress()
    coordinator = replace(
        coordinator, attempt=make_attempt(order, [outcome], requests), progress=progress
    )

    # When
    record = await coordinator.run()

    # Then
    assert record.state == "incomplete"
    assert record.calls[0].state == "failed"
    assert evidence.final_records == [record]
    assert progress.snapshots[-1].final_status == "incomplete_evidence"
    assert_progress_partitions(progress, 1)


class BlockingPassiveQuota(FakeQuotaReader):
    """Pause optional observation after the attempt is durably recorded."""

    def __init__(self, order: list[str]) -> None:
        super().__init__(order)
        self.started = asyncio.Event()

    @override
    async def observe_settled_attempt(
        self, evidence: AttemptEvidence, /
    ) -> QuotaObservation:
        self.started.set()
        await asyncio.Event().wait()
        return self.observation


async def test_progress_partitions_calls_when_passive_observation_is_cancelled() -> (
    None
):
    # Given
    order: list[str] = []
    run = bound_run(config=configuration(quota=True))
    evidence = FakeEvidence(order)
    quota = BlockingPassiveQuota(order)
    coordinator, _, _ = make_coordinator(run, evidence, quota, order)
    progress = FakeProgress()
    coordinator = replace(coordinator, progress=progress)
    task = asyncio.create_task(coordinator.run())
    await quota.started.wait()

    # When
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    # Then
    assert len(evidence.attempt_records) == 1
    assert progress.snapshots[-1].counts.attempts_succeeded == 1
    assert_progress_partitions(progress, 1)
