# SPDX-License-Identifier: Apache-2.0
"""Coordinator wiring order and monitor task ownership."""

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
from script.eval.runner.coordinator import Coordinator
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


def configuration(*, quota: bool = False, dry_run: bool = False) -> HarnessConfig:
    """Build the smallest valid execution configuration."""
    return HarnessConfig(
        ordered_options=(DirectoryOption(position=0, path=Path("context")),),
        models=("model-a",),
        efforts=("low",),
        concurrency=1,
        output_directory=None if dry_run else Path("output"),
        dry_run=dry_run,
        timeout_seconds=1.0,
        cleanup_timeout_seconds=1.0,
        grace_seconds=0.0,
        output_limit_bytes=0,
        quota_wait_enabled=quota,
        instructions_file_path=None,
    )


def bound_run() -> BoundRun:
    """Build one frozen call paired with a resolved binding."""
    config = configuration()
    planned = FrozenPlan.model_construct(
        run_id="run-1",
        configuration=config,
        repository_root=Path("/repo"),
        head_commit="head-1",
        snapshots=(),
        boundary_bytes=(),
        instructions_file=None,
        calls=(),
    )
    call = EffectiveCall(
        run_id="run-1",
        call_id="call-1",
        planned_call=PlannedCall(
            position=0,
            context_indices=(),
            model="model-a",
            effort="low",
            prompt_sha256="prompt-hash",
            prompt=b"prompt",
        ),
        request=AttemptRequest(
            argv=("codex", "exec"),
            cwd=Path("/repo"),
            timeout_seconds=1.0,
            cleanup_timeout_seconds=1.0,
            output_limit_bytes=0,
            stdin="devnull",
        ),
    )
    return BoundRun(
        plan=planned,
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
        calls=(call,),
    )


def run_record() -> RunRecord:
    """Return the scheduler's small complete accounting projection."""
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


async def forbidden_monitor(run: BoundRun, stop: DispatchStop, /) -> None:
    """Fail if dry-run creates monitor work."""
    del run, stop
    await asyncio.sleep(0)
    raise AssertionError("dry-run must not create monitor work")


async def forbidden_scheduler(
    run: BoundRun,
    evidence: EvidenceStore,
    execute: ExecuteAttempt,
    stop: DispatchStop,
    is_stopped: Callable[[], bool],
    /,
) -> RunRecord:
    """Fail if dry-run dispatches planned calls."""
    del run, evidence, execute, stop, is_stopped
    await asyncio.sleep(0)
    raise AssertionError("dry-run must not schedule calls")


class FixedRuntime(Runtime):
    """Return deterministic timestamps and reject unrelated policy effects."""

    def utc_now(self) -> str:
        return "2026-10-27T10:00:00Z"

    def monotonic(self) -> float:
        return 1.0

    async def sleep(self, seconds: float, /) -> None:
        await asyncio.sleep(seconds)

    def uniform(self, lower: float, upper: float, /) -> float:
        return lower


class FakeProgress(ProgressSink):
    """Retain snapshots if the coordinator publishes any."""

    def __init__(self) -> None:
        self.snapshots: list[ProgressSnapshot] = []

    def publish(self, snapshot: ProgressSnapshot, /) -> None:
        self.snapshots.append(snapshot)


class FakeEvidence(EvidenceStore):
    """Record the order and identity of attempt, telemetry, and final writes."""

    def __init__(self, order: list[str]) -> None:
        self.events: list[str] = []
        self.telemetry_events: list[QuotaTelemetryEvent] = []
        self.order = order

    async def create(self, output_directory: Path, plan: FrozenPlan, /):
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
        return AttemptRecord.model_construct(
            run_id=run_id,
            call_id=call_id,
            position=position,
            attempt_number=attempt_number,
            control_flow="returned",
            outcome_kind="completed",
            started_at_utc=evidence.started_at_utc,
            ended_at_utc=evidence.ended_at_utc,
            argv=evidence.request.argv,
            cwd=str(evidence.request.cwd),
            timeout_seconds=1.0,
            cleanup_timeout_seconds=1.0,
            grace_seconds=0.0,
            output_limit_bytes=0,
            elapsed_seconds=1.0,
            elapsed_basis="supervisor_observation",
            exit_status=0,
            termination_reason=None,
            cleanup=None,
            stdout_artifact=None,
            stderr_artifact=None,
            usage_telemetry=None,
            error_type=None,
            diagnostic=None,
            retry_assessment=retry_assessment,
        )

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


class FakeQuotaReader(QuotaStatusReader):
    """Return one typed passive observation and reject unexpected probes."""

    @property
    def expected_scope(self) -> QuotaScope | None:
        return None

    def __init__(self) -> None:
        self.observations = 0
        self.probes = 0

    async def observe_settled_attempt(self, evidence: AttemptEvidence, /):
        self.observations += 1
        return QuotaObservation(
            scope=None,
            read_at_utc="2026-10-27T10:00:00Z",
            source_coordinate=None,
            windows=(),
            diagnostic="unknown source",
        )

    async def poll(
        self, request: QuotaProbeRequest, stop_dispatch: DispatchStop, /
    ) -> QuotaProbeEvidence:
        self.probes += 1
        raise AssertionError("monitor fake owns polling lifecycle")


type ExecuteAttempt = Callable[
    [EffectiveCall, AttemptNumber, DispatchStop], Awaitable[AttemptRecord]
]


def make_attempt(
    order: list[str],
) -> AttemptCall:
    """Return a supervisor fake that records its effect."""

    async def attempt(request: AttemptRequest, stop: DispatchStop, /) -> AttemptResult:
        await asyncio.sleep(0)
        order.append("attempt")
        return Completed(
            observation=AttemptObservation(
                output=CapturedOutput(stdout=b"answer", stderr=b""),
                elapsed_seconds=0.5,
                cleanup=CleanupEvidence("owned", (), "reaped", None),
            ),
            exit_status=0,
        )

    return attempt


def make_coordinator(
    evidence_order: list[str],
    quota: FakeQuotaReader,
    *,
    monitor: Callable[[BoundRun, DispatchStop], Awaitable[None]],
    scheduler: Callable[..., Awaitable[RunRecord]],
) -> Coordinator:
    """Compose a coordinator from typed fakes and its real attempt path."""

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

    return Coordinator(
        attempt=make_attempt(evidence_order),
        classifier=FakeClassifier(evidence_order),
        quota_status=quota,
        runtime=FixedRuntime(),
        progress=FakeProgress(),
        schedule_calls=scheduler,
        monitor_quota=monitor,
        capture_returned_attempt=capture,
    )


class FakeClassifier(OutcomeClassifier):
    """Retain classification order and produce a typed non-retry assessment."""

    def __init__(self, order: list[str]) -> None:
        self.order = order

    def assess(self, evidence: AttemptEvidence, /) -> RetryAssessment:
        self.order.append("classify")
        return RetryAssessment(
            retry_class="unknown",
            classification_basis=None,
            no_result_basis="present_or_unknown",
            diagnostic="not assessed",
        )


async def test_public_run_persists_attempt_before_passive_quota_observation() -> None:
    """Verify the returned-attempt dataflow and durable evidence ordering."""
    # Given
    order: list[str] = []
    quota = FakeQuotaReader()
    store = FakeEvidence(order)
    monitor_started = asyncio.Event()

    async def monitor(run: BoundRun, stop: DispatchStop, /) -> None:
        monitor_started.set()
        try:
            await asyncio.Event().wait()
        finally:
            order.append("monitor_joined")

    async def scheduler(
        run: BoundRun,
        evidence: EvidenceStore,
        execute: ExecuteAttempt,
        stop: DispatchStop,
        is_stopped: Callable[[], bool],
    ) -> RunRecord:
        del is_stopped
        await monitor_started.wait()
        await execute(run.calls[0], 1, stop)
        order.append("scheduler_settled")
        return run_record()

    coordinator = make_coordinator(order, quota, monitor=monitor, scheduler=scheduler)

    # When
    result = await coordinator.run(
        bound_run(),
        store,
        configuration(quota=True),
    )

    # Then
    assert result.run_id == "run-1"
    assert order == [
        "attempt",
        "classify",
        "record_attempt",
        "record_telemetry",
        "scheduler_settled",
        "monitor_joined",
        "finalize",
    ]
    assert store.events == ["attempt", "telemetry", "final"]
    assert (store.telemetry_events[0].call_id, quota.observations, quota.probes) == (
        "call-1",
        1,
        0,
    )


@pytest.mark.parametrize(
    ("quota_enabled", "monitor_expected"),
    [(False, False), (True, True)],
    ids=["monitor-disabled", "monitor-opted-in"],
)
async def test_public_run_owns_one_enabled_monitor_through_dispatch_settlement(
    quota_enabled: bool, monitor_expected: bool
) -> None:
    """Join the single opted-in monitor after scheduler settlement."""
    # Given
    order: list[str] = []
    quota = FakeQuotaReader()
    store = FakeEvidence(order)
    monitor_started = asyncio.Event()
    monitor_stopped = asyncio.Event()
    monitor_calls = 0

    async def monitor(run: BoundRun, stop: DispatchStop, /) -> None:
        nonlocal monitor_calls
        monitor_calls += 1
        monitor_started.set()
        try:
            await asyncio.Event().wait()
        finally:
            monitor_stopped.set()

    async def scheduler(
        run: BoundRun,
        evidence: EvidenceStore,
        execute: ExecuteAttempt,
        stop: DispatchStop,
        is_stopped: Callable[[], bool],
    ) -> RunRecord:
        del is_stopped
        if monitor_expected:
            await monitor_started.wait()
        await execute(run.calls[0], 1, stop)
        return run_record()

    coordinator = make_coordinator(order, quota, monitor=monitor, scheduler=scheduler)

    # When
    await coordinator.run(bound_run(), store, configuration(quota=quota_enabled))

    # Then
    assert (
        monitor_calls == (1 if monitor_expected else 0)
        and monitor_stopped.is_set() is monitor_expected
    )
    assert quota.probes == 0 and len(store.telemetry_events) == (
        1 if quota_enabled else 0
    )


async def test_public_run_joins_monitor_when_scheduler_fails() -> None:
    """Propagate scheduler failure after cancelling and joining the monitor."""
    # Given
    order: list[str] = []
    quota = FakeQuotaReader()
    store = FakeEvidence(order)
    monitor_started = asyncio.Event()
    monitor_stopped = asyncio.Event()

    async def monitor(run: BoundRun, stop: DispatchStop, /) -> None:
        monitor_started.set()
        try:
            await asyncio.Event().wait()
        finally:
            monitor_stopped.set()

    async def scheduler(
        run: BoundRun,
        evidence: EvidenceStore,
        execute: ExecuteAttempt,
        stop: DispatchStop,
        is_stopped: Callable[[], bool],
    ) -> RunRecord:
        del is_stopped
        await monitor_started.wait()
        raise RuntimeError("dispatch failed")

    coordinator = make_coordinator(order, quota, monitor=monitor, scheduler=scheduler)

    # When
    with pytest.raises(RuntimeError, match="dispatch failed"):
        await coordinator.run(bound_run(), store, configuration(quota=True))

    # Then
    assert monitor_stopped.is_set()


async def test_public_run_joins_monitor_when_cancelled() -> None:
    """Propagate caller cancellation after monitor cleanup settles."""
    # Given
    order: list[str] = []
    quota = FakeQuotaReader()
    monitor_started = asyncio.Event()
    monitor_stopped = asyncio.Event()
    scheduler_started = asyncio.Event()

    async def monitor(run: BoundRun, stop: DispatchStop, /) -> None:
        monitor_started.set()
        try:
            await asyncio.Event().wait()
        finally:
            monitor_stopped.set()

    async def scheduler(
        run: BoundRun,
        evidence: EvidenceStore,
        execute: ExecuteAttempt,
        stop: DispatchStop,
        is_stopped: Callable[[], bool],
    ) -> RunRecord:
        del is_stopped
        await monitor_started.wait()
        scheduler_started.set()
        await asyncio.Event().wait()
        return run_record()

    coordinator = make_coordinator(order, quota, monitor=monitor, scheduler=scheduler)

    # When
    run_task = asyncio.create_task(
        coordinator.run(bound_run(), FakeEvidence(order), configuration(quota=True))
    )
    await scheduler_started.wait()
    run_task.cancel()

    # Then
    with pytest.raises(asyncio.CancelledError):
        await run_task
    assert monitor_stopped.is_set()


async def test_public_run_refuses_dry_run_before_quota_or_dispatch_effects() -> None:
    """Keep dry-run plans out of the execution and quota lifecycle."""
    # Given
    order: list[str] = []
    quota = FakeQuotaReader()
    store = FakeEvidence(order)

    coordinator = make_coordinator(
        order, quota, monitor=forbidden_monitor, scheduler=forbidden_scheduler
    )

    # When
    with pytest.raises(ValueError, match="dry-run plans"):
        await coordinator.run(
            bound_run(), store, configuration(quota=True, dry_run=True)
        )

    # Then
    assert quota.observations == 0
    assert quota.probes == 0
    assert not store.events
