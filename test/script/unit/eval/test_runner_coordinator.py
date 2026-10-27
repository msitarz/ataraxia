# SPDX-License-Identifier: Apache-2.0
"""Coordinator wiring order and owned-task lifecycle."""

import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path

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
    QuotaObservation,
    QuotaProbeEvidence,
    QuotaProbeLifecycleInput,
    QuotaProbeRequest,
    QuotaProbeSettled,
    QuotaScope,
    QuotaTelemetryEvent,
    RetryAssessment,
    RunRecord,
    WaitEvent,
)
from script.eval.runner.coordinator import (
    Coordinator,
    MonitorQuota,
    ScheduleCalls,
    _RunContext,
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
from script.process_supervisor import (
    AttemptObservation,
    AttemptRequest,
    AttemptResult,
    CapturedOutput,
    CleanupEvidence,
    Completed,
    DispatchStop,
)

type ExecuteAttempt = Callable[[EffectiveCall, AttemptNumber], Awaitable[AttemptRecord]]


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


def bound_run(*, calls_count: int = 1) -> BoundRun:
    """Build a fully validated plan and matching effective calls."""
    config = configuration()
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
        configuration=config,
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
    """Return a valid scheduler-produced run record for finalization checks."""
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
    """Record attempt evidence and all durable lifecycle writes."""

    def __init__(self, order: list[str]) -> None:
        self.events: list[str] = []
        self.attempt_inputs: list[
            tuple[str, str, int, AttemptNumber, AttemptEvidence, RetryAssessment | None]
        ] = []
        self.telemetry_events: list[QuotaTelemetryEvent] = []
        self.final_records: list[RunRecord] = []
        self.order = order

    async def create(
        self, output_directory: Path, plan: FrozenPlan, /
    ) -> PreparedEvidence:
        raise AssertionError("coordinator receives an already prepared store")

    async def record_attempt(
        self,
        run_id: str,
        call_id: str,
        position: int,
        attempt_number: int,
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
        return AttemptRecord.model_validate({
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

    async def record_wait_event(self, event: WaitEvent, /) -> None:
        self.events.append("wait")

    async def record_quota_probe_event(
        self, event: QuotaProbeLifecycleInput, /
    ) -> None:
        self.events.append("probe-event")

    async def record_quota_probe_settled(
        self, evidence: QuotaProbeEvidence, /
    ) -> QuotaProbeSettled:
        raise AssertionError("attempt composition does not settle quota probes")

    async def record_quota_telemetry(self, event: QuotaTelemetryEvent, /) -> None:
        self.order.append("record_telemetry")
        self.events.append("telemetry")
        self.telemetry_events.append(event)

    async def finalize(self, record: RunRecord, /) -> None:
        self.order.append("finalize")
        self.events.append("final")
        self.final_records.append(record)


class FakeQuotaReader(QuotaStatusReader):
    """Return an unknown but typed passive observation; reject active probes."""

    def __init__(self, order: list[str]) -> None:
        self.observations = 0
        self.probes = 0
        self.order = order
        self.observation = QuotaObservation(
            scope=None,
            read_at_utc="2026-10-27T10:00:00Z",
            source_coordinate=None,
            windows=(),
            diagnostic="source unavailable",
        )

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
        raise AssertionError("coordinator wiring does not issue active probes")


class FakeClassifier(OutcomeClassifier):
    """Retain evidence identity and return one fixed retry assessment."""

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


def make_attempt(
    order: list[str], outcomes: list[AttemptResult], requests: list[AttemptRequest]
) -> AttemptCall:
    """Return a supervisor fake that retains exact requests and outcomes."""

    async def attempt(request: AttemptRequest, stop: DispatchStop, /) -> AttemptResult:
        await asyncio.sleep(0)
        order.append("attempt")
        requests.append(request)
        return next(outcomes_iterator)

    outcomes_iterator = iter(outcomes)
    return attempt


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


def make_coordinator(
    order: list[str],
    quota: FakeQuotaReader,
    outcomes: list[AttemptResult] | None = None,
    requests: list[AttemptRequest] | None = None,
    *,
    monitor: MonitorQuota,
    scheduler: ScheduleCalls,
) -> tuple[Coordinator, FakeClassifier, list[AttemptRequest]]:
    """Compose exact collaborators and retain the supervisor requests."""
    actual_outcomes = [successful_outcome()] if outcomes is None else outcomes
    actual_requests = [] if requests is None else requests
    classifier = FakeClassifier(order)

    def capture(
        call: EffectiveCall,
        outcome: AttemptResult,
        started_at: str,
        ended_at: str,
        /,
    ) -> AttemptEvidence:
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

    coordinator = Coordinator(
        attempt=make_attempt(order, actual_outcomes, actual_requests),
        classifier=classifier,
        quota_status=quota,
        runtime=FixedRuntime(),
        progress=FakeProgress(),
        schedule_calls=scheduler,
        monitor_quota=monitor,
        capture_returned_attempt=capture,
    )
    return coordinator, classifier, actual_requests


def assert_context_matches(
    context: _RunContext,
    coordinator: Coordinator,
    run: BoundRun,
    evidence: EvidenceStore,
    config: HarnessConfig,
    quota: QuotaStatusReader,
) -> None:
    """Check that each collaborator receives the same original run values."""
    assert context.bound_run is run
    assert context.evidence is evidence
    assert context.config is config
    assert context.attempt is coordinator.attempt
    assert context.classifier is coordinator.classifier
    assert context.quota_status is quota
    assert context.runtime is coordinator.runtime
    assert context.progress is coordinator.progress


def cancellation_blocking_monitor(
    cleanup_started: asyncio.Event,
    allow_cleanup: asyncio.Event,
    cleanup_finished: asyncio.Event,
) -> MonitorQuota:
    """Build a monitor that waits for explicit cleanup release after cancel."""

    async def monitor(context: _RunContext, stop: DispatchStop, /) -> None:
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cleanup_started.set()
            while not allow_cleanup.is_set():
                try:
                    await allow_cleanup.wait()
                except asyncio.CancelledError:
                    continue
            cleanup_finished.set()
            raise

    return monitor


async def completed_scheduler(
    context: _RunContext,
    execute: ExecuteAttempt,
    stop: DispatchStop,
    is_stopped: Callable[[], bool],
    /,
) -> RunRecord:
    """Return a valid record asynchronously without dispatching calls."""
    await asyncio.sleep(0)
    return run_record()


def assert_attempt_flow(
    run: BoundRun,
    scheduler_record: RunRecord,
    result: RunRecord,
    store: FakeEvidence,
    quota: FakeQuotaReader,
    classifier: FakeClassifier,
    requests: list[AttemptRequest],
    outcome: AttemptResult,
    order: list[str],
) -> None:
    """Check exact attempt identity and the persisted-before-observed sequence."""
    record_input = store.attempt_inputs[0]
    attempt_evidence = record_input[4]
    assert result is scheduler_record
    assert store.final_records == [scheduler_record]
    assert requests == [run.calls[0].request]
    assert requests[0] is run.calls[0].request
    assert attempt_evidence.outcome is outcome
    assert attempt_evidence.request is requests[0]
    assert classifier.assessed == [attempt_evidence]
    assert record_input[:4] == ("run-1", "call-0", 0, 1)
    assert record_input[5] is classifier.assessment
    assert quota.observations == 1 and quota.probes == 0
    assert store.telemetry_events[0].observation is quota.observation
    assert order == [
        "attempt",
        "classify",
        "record_attempt",
        "observe_quota",
        "record_telemetry",
        "finalize",
    ]


async def test_context_forwards_exact_run_settings_and_collaborators() -> None:
    """Pass original collaborators and nondefault policy settings to both leaves."""
    # Given
    order: list[str] = []
    run = bound_run()
    config = configuration(quota=True, concurrency=3, quota_poll_interval=8.5)
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    contexts: list[_RunContext] = []
    monitor_started = asyncio.Event()

    async def monitor(context: _RunContext, stop: DispatchStop, /) -> None:
        contexts.append(context)
        monitor_started.set()
        await asyncio.Event().wait()

    async def scheduler(
        context: _RunContext,
        execute: ExecuteAttempt,
        stop: DispatchStop,
        is_stopped: Callable[[], bool],
        /,
    ) -> RunRecord:
        contexts.append(context)
        await monitor_started.wait()
        await execute(context.bound_run.calls[0], 1)
        return run_record()

    coordinator, _, _ = make_coordinator(
        order, quota, monitor=monitor, scheduler=scheduler
    )

    # When
    await coordinator.run(run, evidence, config)

    # Then
    assert len(contexts) == 2
    for context in contexts:
        assert_context_matches(context, coordinator, run, evidence, config, quota)
    assert contexts[0] is contexts[1]
    assert contexts[0].config.concurrency == 3
    assert contexts[0].config.quota_poll_interval_seconds == pytest.approx(8.5)


async def test_attempt_effects_preserve_identity_and_durable_order() -> None:
    """Persist the exact classified attempt before reading and recording quota."""
    # Given
    order: list[str] = []
    run = bound_run()
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    outcomes = [successful_outcome()]
    scheduler_record = run_record()

    async def monitor(context: _RunContext, stop: DispatchStop, /) -> None:
        await asyncio.Event().wait()

    async def scheduler(
        context: _RunContext,
        execute: ExecuteAttempt,
        stop: DispatchStop,
        is_stopped: Callable[[], bool],
        /,
    ) -> RunRecord:
        await execute(context.bound_run.calls[0], 1)
        return scheduler_record

    coordinator, classifier, requests = make_coordinator(
        order, quota, outcomes, monitor=monitor, scheduler=scheduler
    )

    # When
    result = await coordinator.run(run, evidence, configuration(quota=True))

    # Then
    assert_attempt_flow(
        run,
        scheduler_record,
        result,
        evidence,
        quota,
        classifier,
        requests,
        outcomes[0],
        order,
    )


async def test_monitor_failure_stops_active_scheduler() -> None:
    """Fail the run and stop an active scheduler when its monitor exits early."""
    # Given
    order: list[str] = []
    run = bound_run(calls_count=2)
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    scheduler_started = asyncio.Event()
    stopped_when_cancelled: list[bool] = []

    async def monitor(context: _RunContext, stop: DispatchStop, /) -> None:
        await scheduler_started.wait()
        raise RuntimeError("monitor failed")

    async def scheduler(
        context: _RunContext,
        execute: ExecuteAttempt,
        stop: DispatchStop,
        is_stopped: Callable[[], bool],
        /,
    ) -> RunRecord:
        await execute(context.bound_run.calls[0], 1)
        scheduler_started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            stopped_when_cancelled.append(is_stopped())
            raise
        return run_record()

    coordinator, _, _ = make_coordinator(
        order,
        quota,
        outcomes=[successful_outcome()],
        monitor=monitor,
        scheduler=scheduler,
    )

    # When
    with pytest.raises(RuntimeError, match="monitor failed"):
        await coordinator.run(run, evidence, configuration(quota=True))

    # Then
    assert len(evidence.attempt_inputs) == 1
    assert stopped_when_cancelled == [True]
    assert evidence.final_records == []


async def test_repeated_cancellation_waits_for_monitor_cleanup() -> None:
    """Retain monitor cleanup through repeated cancellation of the run owner."""
    # Given
    order: list[str] = []
    run = bound_run()
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    cleanup_started = asyncio.Event()
    allow_cleanup = asyncio.Event()
    cleanup_finished = asyncio.Event()

    coordinator, _, _ = make_coordinator(
        order,
        quota,
        monitor=cancellation_blocking_monitor(
            cleanup_started, allow_cleanup, cleanup_finished
        ),
        scheduler=completed_scheduler,
    )

    # When
    run_task = asyncio.create_task(
        coordinator.run(run, evidence, configuration(quota=True))
    )
    await cleanup_started.wait()
    run_task.cancel()
    await asyncio.sleep(0)
    run_task.cancel()
    await asyncio.sleep(0)
    allow_cleanup.set()

    # Then
    with pytest.raises(asyncio.CancelledError):
        await run_task
    assert cleanup_finished.is_set()
    assert evidence.final_records == []


async def test_default_scheduler_and_conversion_leaves_are_pending() -> None:
    """Keep unfinished default leaves visible through the public run boundary."""
    # Given
    order: list[str] = []
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    coordinator = Coordinator(
        attempt=make_attempt(order, [successful_outcome()], []),
        classifier=FakeClassifier(order),
        quota_status=quota,
        runtime=FixedRuntime(),
        progress=FakeProgress(),
    )

    # When
    with pytest.raises(NotImplementedError, match="scheduling policy"):
        await coordinator.run(bound_run(), evidence, configuration())

    # Then
    assert evidence.final_records == []
    assert quota.observations == 0 and quota.probes == 0


async def test_default_monitor_leaf_fails_closed_and_stops_scheduler() -> None:
    """Stop active scheduling when the default opted-in monitor is unavailable."""
    # Given
    order: list[str] = []
    quota = FakeQuotaReader(order)
    scheduler_started = asyncio.Event()
    stopped_when_cancelled: list[bool] = []

    async def scheduler(
        context: _RunContext,
        execute: ExecuteAttempt,
        stop: DispatchStop,
        is_stopped: Callable[[], bool],
        /,
    ) -> RunRecord:
        scheduler_started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            stopped_when_cancelled.append(is_stopped())
            raise
        return run_record()

    coordinator = Coordinator(
        attempt=make_attempt(order, [successful_outcome()], []),
        classifier=FakeClassifier(order),
        quota_status=quota,
        runtime=FixedRuntime(),
        progress=FakeProgress(),
        schedule_calls=scheduler,
    )

    # When
    with pytest.raises(NotImplementedError, match="quota monitor cadence"):
        await coordinator.run(
            bound_run(), FakeEvidence(order), configuration(quota=True)
        )

    # Then
    assert scheduler_started.is_set()
    assert stopped_when_cancelled == [True]
    assert quota.observations == 0 and quota.probes == 0


async def test_default_attempt_conversion_leaf_remains_explicitly_pending() -> None:
    """Surface the unfinished returned-result conversion through public run."""
    # Given
    order: list[str] = []
    quota = FakeQuotaReader(order)
    evidence = FakeEvidence(order)

    async def scheduler(
        context: _RunContext,
        execute: ExecuteAttempt,
        stop: DispatchStop,
        is_stopped: Callable[[], bool],
        /,
    ) -> RunRecord:
        await execute(context.bound_run.calls[0], 1)
        return run_record()

    coordinator = Coordinator(
        attempt=make_attempt(order, [successful_outcome()], []),
        classifier=FakeClassifier(order),
        quota_status=quota,
        runtime=FixedRuntime(),
        progress=FakeProgress(),
        schedule_calls=scheduler,
    )

    # When
    with pytest.raises(NotImplementedError, match="evidence conversion"):
        await coordinator.run(bound_run(), evidence, configuration())

    # Then
    assert order == ["attempt"]
    assert evidence.attempt_inputs == []
    assert evidence.final_records == []


async def test_monitor_disabled_run_does_not_read_or_probe_quota() -> None:
    """Keep quota effects absent when quota monitoring is disabled."""
    # Given
    order: list[str] = []
    run = bound_run()
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)

    async def scheduler(
        context: _RunContext,
        execute: ExecuteAttempt,
        stop: DispatchStop,
        is_stopped: Callable[[], bool],
        /,
    ) -> RunRecord:
        await execute(context.bound_run.calls[0], 1)
        return run_record()

    coordinator, _, _ = make_coordinator(
        order, quota, monitor=_monitor_that_must_not_start, scheduler=scheduler
    )

    # When
    await coordinator.run(run, evidence, configuration())

    # Then
    assert quota.observations == 0 and quota.probes == 0
    assert evidence.events == ["attempt", "final"]


async def test_dry_run_is_refused_before_any_coordinator_effects() -> None:
    """Keep dry-run reporting outside the execution coordinator."""
    # Given
    order: list[str] = []
    evidence = FakeEvidence(order)
    quota = FakeQuotaReader(order)
    coordinator, _, _ = make_coordinator(
        order,
        quota,
        monitor=_monitor_that_must_not_start,
        scheduler=_scheduler_that_must_not_start,
    )

    # When
    with pytest.raises(ValueError, match="dry-run plans"):
        await coordinator.run(
            bound_run(), evidence, configuration(quota=True, dry_run=True)
        )

    # Then
    assert quota.observations == 0 and quota.probes == 0
    assert evidence.events == []


async def _monitor_that_must_not_start(
    context: _RunContext, stop: DispatchStop, /
) -> None:
    """Fail if a disabled or dry-run monitor is launched."""
    await asyncio.sleep(0)
    raise AssertionError("quota monitor was unexpectedly started")


async def _scheduler_that_must_not_start(
    context: _RunContext,
    execute: ExecuteAttempt,
    stop: DispatchStop,
    is_stopped: Callable[[], bool],
    /,
) -> RunRecord:
    """Fail if a dry-run plan is scheduled."""
    await asyncio.sleep(0)
    raise AssertionError("dry-run calls were unexpectedly scheduled")
