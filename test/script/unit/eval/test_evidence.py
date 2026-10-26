# SPDX-License-Identifier: Apache-2.0
"""Typed evidence adapter ordering and identity forwarding."""

import asyncio
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
import threading
from typing import Literal

import pytest

from script.eval.evidence import EvidenceStoreAdapter, create_evidence_store
from script.eval.model import (
    AttemptEvidence,
    AttemptNumber,
    AttemptRecord,
    CallId,
    DirectoryOption,
    FrozenPlan,
    HarnessConfig,
    PreparedEvidence,
    QuotaAllowanceId,
    QuotaObservation,
    QuotaProbeEvidence,
    QuotaProbeId,
    QuotaProbeLifecycleInput,
    QuotaProbeRecord,
    QuotaProbeRequest,
    QuotaProbeSchedule,
    QuotaProbeScheduled,
    QuotaProbeSettled,
    QuotaProviderId,
    QuotaScope,
    QuotaTelemetryEvent,
    QuotaWaitContext,
    RetryAssessment,
    RunId,
    RunRecord,
    WaitEvent,
)
from script.process_supervisor import (
    AttemptObservation,
    AttemptRequest,
    CapturedOutput,
    CleanupEvidence,
    Completed,
)


def projected_attempt(
    _context: PreparedEvidence,
    run_id: RunId,
    call_id: CallId,
    position: int,
    attempt_number: AttemptNumber,
    _evidence: AttemptEvidence,
    _retry_assessment: RetryAssessment | None,
) -> AttemptRecord:
    """Return a scalar attempt record retaining the supplied identity."""
    return AttemptRecord.model_validate(
        attempt_record().model_dump()
        | {
            "run_id": run_id,
            "call_id": call_id,
            "position": position,
            "attempt_number": attempt_number,
        }
    )


def append_telemetry(
    calls: list[str], _context: PreparedEvidence, _event: QuotaTelemetryEvent
) -> None:
    """Record whether a queued telemetry leaf ran."""
    calls.append("telemetry")


def blocked_append_store() -> tuple[
    EvidenceStoreAdapter, threading.Event, threading.Event, list[str]
]:
    """Provide a store with a barrier-controlled attempt append and finalizer."""
    started = threading.Event()
    release = threading.Event()
    order: list[str] = []
    prepared = prepared_evidence()

    def append(_context: PreparedEvidence, _record: AttemptRecord) -> None:
        started.set()
        assert release.wait(5)
        order.append("append")

    store = create_evidence_store(
        create_evidence=lambda _directory, _plan: prepared,
        project_attempt=projected_attempt,
        append_attempt=append,
        finalize_evidence=lambda _context, _record: order.append("finalize"),
    )
    return store, started, release, order


async def wait_for_leaf_start(
    started: threading.Event, release: threading.Event
) -> None:
    """Wait for a blocking leaf, releasing it if the bounded wait fails."""
    did_start = await asyncio.to_thread(started.wait, 5)
    if not did_start:
        release.set()
    assert did_start


def attempt_evidence() -> AttemptEvidence:
    """Return live supervisor evidence with independently captured streams."""
    request = AttemptRequest(
        argv=("codex", "exec"),
        cwd=Path("/work"),
        timeout_seconds=5.0,
        cleanup_timeout_seconds=2.0,
        output_limit_bytes=0,
        stdin="devnull",
    )
    return AttemptEvidence(
        control_flow="returned",
        outcome=Completed(
            observation=AttemptObservation(
                output=CapturedOutput(stdout=b"out", stderr=b"err"),
                elapsed_seconds=1.0,
                cleanup=CleanupEvidence("owned", (), "reaped", None),
            ),
            exit_status=0,
        ),
        error_type=None,
        diagnostic=None,
        request=request,
        started_at_utc="2026-10-26T00:00:00Z",
        ended_at_utc="2026-10-26T00:00:01Z",
        usage_telemetry=None,
    )


def attempt_record() -> AttemptRecord:
    """Return one scalar record for projection and append ordering checks."""
    return AttemptRecord.model_validate({
        "run_id": "run-1",
        "call_id": "call-2",
        "position": 3,
        "attempt_number": 2,
        "control_flow": "returned",
        "outcome_kind": "completed",
        "started_at_utc": "2026-10-26T00:00:00Z",
        "ended_at_utc": "2026-10-26T00:00:01Z",
        "argv": ("codex", "exec"),
        "cwd": "/work",
        "timeout_seconds": 5.0,
        "cleanup_timeout_seconds": 2.0,
        "grace_seconds": 0.0,
        "output_limit_bytes": 0,
        "elapsed_seconds": 1.0,
        "elapsed_basis": "supervisor_observation",
        "exit_status": 0,
        "termination_reason": None,
        "cleanup": None,
        "stdout_artifact": None,
        "stderr_artifact": None,
        "usage_telemetry": None,
        "error_type": None,
        "diagnostic": None,
        "retry_assessment": None,
    })


def assessment() -> RetryAssessment:
    """Return the runner's already-computed retry decision."""
    return RetryAssessment(
        retry_class="unknown",
        classification_basis=None,
        no_result_basis="present_or_unknown",
        diagnostic="insufficient evidence",
    )


def frozen_plan() -> FrozenPlan:
    """Build the smallest valid frozen plan for pre-dispatch setup tests."""
    config = HarnessConfig(
        ordered_options=(DirectoryOption(position=0, path=Path("context")),),
        models=("model-a",),
        efforts=("low",),
        concurrency=1,
        output_directory=Path("results"),
        dry_run=False,
        timeout_seconds=5.0,
        cleanup_timeout_seconds=2.0,
        grace_seconds=0.0,
        output_limit_bytes=0,
        instructions_file_path=None,
    )
    return FrozenPlan(
        run_id="run-1",
        configuration=config,
        repository_root=Path("/work"),
        head_commit="commit-1",
        snapshots=(),
        boundary_bytes=(),
        instructions_file=None,
        calls=(),
    )


def prepared_evidence() -> PreparedEvidence:
    """Return the exact bound output context passed to every evidence leaf."""
    return PreparedEvidence(Path("results"), Path("results/plan.json"), None)


def quota_probe_request() -> QuotaProbeRequest:
    """Return a scheduled probe bound to an opaque quota allowance."""
    return QuotaProbeRequest(
        schedule=QuotaProbeSchedule(
            run_id="run-1",
            probe_id=QuotaProbeId("probe-1"),
            scope=QuotaScope(
                provider_id=QuotaProviderId("codex"),
                allowance_id=QuotaAllowanceId("a1"),
            ),
            reason="periodic",
            created_at_utc="2026-10-26T00:00:00Z",
            due_at_utc="2026-10-26T00:00:01Z",
            interval_seconds=1.0,
            reset_hint_at_utc=None,
        ),
        pause_wait_id=None,
        poll_started_at_utc="2026-10-26T00:00:01Z",
        scheduled_wait_seconds=1.0,
        scheduled_wait_elapsed_basis="monotonic",
    )


def settled_probe_record(
    observation: QuotaObservation | None,
    usage_telemetry: bytes | None,
    stdout_artifact: str | None,
    stderr_artifact: str | None,
) -> QuotaProbeSettled:
    """Build a scalar probe record while retaining supplied unknown values."""
    return QuotaProbeSettled(
        kind="settled",
        record=QuotaProbeRecord(
            control_flow="returned",
            outcome_kind="completed",
            started_at_utc="2026-10-26T00:00:00Z",
            ended_at_utc="2026-10-26T00:00:01Z",
            argv=("codex", "exec"),
            cwd="/work",
            timeout_seconds=5.0,
            cleanup_timeout_seconds=2.0,
            grace_seconds=0.0,
            output_limit_bytes=0,
            elapsed_seconds=1.0,
            elapsed_basis="supervisor_observation",
            exit_status=0,
            termination_reason=None,
            cleanup=None,
            stdout_artifact=stdout_artifact,
            stderr_artifact=stderr_artifact,
            usage_telemetry=usage_telemetry,
            error_type=None,
            diagnostic=None,
            request=quota_probe_request(),
            quota_state="unknown",
            observation=observation,
            classification_basis="source unavailable",
        ),
    )


def empty_quota_observation() -> QuotaObservation:
    """Return a real observation with known scope and no reported windows."""
    return QuotaObservation(
        scope=quota_probe_request().schedule.scope,
        read_at_utc="2026-10-26T00:00:02Z",
        source_coordinate="session:1",
        windows=(),
        diagnostic=None,
    )


def quota_wait_event(observation: QuotaObservation) -> WaitEvent:
    """Return one wait event retaining its supplied empty or unknown windows."""
    context = QuotaWaitContext(
        kind="quota",
        trigger_call_id="call-1",
        trigger_attempt_number=1,
        cumulative_waited_before_seconds=0.0,
        wait_limit_seconds=None,
        quota_observation=observation,
        selected_reset_at_utc=None,
    )
    return WaitEvent(
        run_id="run-1",
        wait_id="wait-1",
        context=context,
        kind="started",
        observed_at_utc="2026-10-26T00:00:00Z",
        elapsed_seconds=0.0,
        quota_observation=observation,
        end=None,
        diagnostic=None,
    )


def run_record() -> RunRecord:
    """Return final accounting with empty call and wait collections."""
    return RunRecord(
        run_id="run-1",
        repository_root="/work",
        head_commit="commit-1",
        state="complete",
        runner_version="runner-1",
        codex_path=None,
        cli_version=None,
        effective_settings=(),
        calls=(),
        waits=(),
    )


@dataclass
class EvidenceWrites:
    """Typed in-memory sink that records distinct evidence effects."""

    prepared: PreparedEvidence
    order: list[Literal["wait", "probe", "telemetry", "final"]] = field(
        default_factory=list
    )
    waits: list[WaitEvent] = field(default_factory=list)
    probes: list[QuotaProbeLifecycleInput] = field(default_factory=list)
    telemetry: list[QuotaTelemetryEvent] = field(default_factory=list)
    runs: list[RunRecord] = field(default_factory=list)

    def append_wait(self, context: PreparedEvidence, value: WaitEvent) -> None:
        assert context is self.prepared
        self.order.append("wait")
        self.waits.append(value)

    def append_probe(
        self, context: PreparedEvidence, value: QuotaProbeLifecycleInput
    ) -> None:
        assert context is self.prepared
        self.order.append("probe")
        self.probes.append(value)

    def append_telemetry(
        self, context: PreparedEvidence, value: QuotaTelemetryEvent
    ) -> None:
        assert context is self.prepared
        self.order.append("telemetry")
        self.telemetry.append(value)

    def finalize(self, context: PreparedEvidence, value: RunRecord) -> None:
        assert context is self.prepared
        self.order.append("final")
        self.runs.append(value)


async def test_create_forwards_plan_and_returns_prepared_paths() -> None:
    """Pre-dispatch setup uses the exact caller destination and frozen plan."""
    # Given
    plan = frozen_plan()
    prepared = prepared_evidence()
    observed: list[tuple[Path, FrozenPlan]] = []

    def create(output_directory: Path, value: FrozenPlan) -> PreparedEvidence:
        observed.append((output_directory, value))
        return prepared

    store = create_evidence_store(create_evidence=create)

    # When
    result = await store.create(Path("results"), plan)

    # Then
    assert result is prepared
    assert observed == [(Path("results"), plan)]


async def test_record_attempt_projects_then_appends_with_supplied_identity() -> None:
    """Forward runner-owned classification and persist before returning."""
    # Given
    order: list[str] = []
    observed: list[
        tuple[RunId, CallId, int, int, AttemptEvidence, RetryAssessment | None]
    ] = []
    evidence = attempt_evidence()
    classification = assessment()
    prepared = prepared_evidence()
    record = AttemptRecord.model_validate(
        attempt_record().model_dump() | {"retry_assessment": classification}
    )

    def project(
        context: PreparedEvidence,
        run_id: RunId,
        call_id: CallId,
        position: int,
        attempt_number: int,
        value: AttemptEvidence,
        retry_assessment: RetryAssessment | None,
    ) -> AttemptRecord:
        order.append("project")
        assert context is prepared
        observed.append((
            run_id,
            call_id,
            position,
            attempt_number,
            value,
            retry_assessment,
        ))
        return record

    def append(context: PreparedEvidence, value: AttemptRecord) -> None:
        order.append("append")
        assert context is prepared
        assert value is record

    store = create_evidence_store(
        create_evidence=lambda _directory, _plan: prepared,
        project_attempt=project,
        append_attempt=append,
    )
    await store.create(Path("results"), frozen_plan())

    # When
    result = await store.record_attempt(
        "run-1", "call-2", 3, 2, evidence, classification
    )

    # Then
    assert result is record
    assert result.retry_assessment == classification
    assert order == ["project", "append"]
    assert observed == [("run-1", "call-2", 3, 2, evidence, classification)]


async def test_attempt_append_failure_propagates_after_projection() -> None:
    """A failed required evidence write reaches the coordinator unchanged."""
    # Given
    failure = OSError("ledger unavailable")
    order: list[str] = []
    prepared = prepared_evidence()

    def project(
        _context: PreparedEvidence,
        _run_id: RunId,
        _call_id: CallId,
        _position: int,
        _attempt_number: int,
        _evidence: AttemptEvidence,
        _assessment: RetryAssessment | None,
    ) -> AttemptRecord:
        order.append("project")
        return attempt_record()

    def append(context: PreparedEvidence, _record: AttemptRecord) -> None:
        assert context is prepared
        order.append("append")
        raise failure

    store = create_evidence_store(
        create_evidence=lambda _directory, _plan: prepared,
        project_attempt=project,
        append_attempt=append,
    )
    await store.create(Path("results"), frozen_plan())

    # When
    with pytest.raises(OSError) as captured:
        await store.record_attempt("run-1", "call-2", 3, 2, attempt_evidence(), None)

    # Then
    assert captured.value is failure
    assert order == ["project", "append"]


async def test_attempt_projection_failure_prevents_append() -> None:
    """A failed projection cannot write a contradictory or partial record."""
    # Given
    failure = ValueError("projection failed")
    appended: list[AttemptRecord] = []

    def project(
        _context: PreparedEvidence,
        _run_id: RunId,
        _call_id: CallId,
        _position: int,
        _attempt_number: int,
        _evidence: AttemptEvidence,
        _assessment: RetryAssessment | None,
    ) -> AttemptRecord:
        raise failure

    prepared = prepared_evidence()
    store = create_evidence_store(
        create_evidence=lambda _directory, _plan: prepared,
        project_attempt=project,
        append_attempt=lambda _context, record: appended.append(record),
    )
    await store.create(Path("results"), frozen_plan())

    # When
    with pytest.raises(ValueError) as captured:
        await store.record_attempt("run-1", "call-2", 3, 2, attempt_evidence(), None)

    # Then
    assert captured.value is failure
    assert appended == []


async def test_failed_creation_does_not_enable_recording() -> None:
    """A failed create leaves no context and blocks writes before projection."""
    # Given
    failure = OSError("exclusive creation failed")
    projected: list[AttemptRecord] = []

    def project(
        _context: PreparedEvidence,
        _run_id: RunId,
        _call_id: CallId,
        _position: int,
        _attempt_number: int,
        _evidence: AttemptEvidence,
        _assessment: RetryAssessment | None,
    ) -> AttemptRecord:
        record = attempt_record()
        projected.append(record)
        return record

    def create(_directory: Path, _plan: FrozenPlan) -> PreparedEvidence:
        raise failure

    store = create_evidence_store(create_evidence=create, project_attempt=project)

    # When
    with pytest.raises(OSError) as create_error:
        await store.create(Path("results"), frozen_plan())
    with pytest.raises(RuntimeError, match="must be prepared"):
        await store.record_attempt("run-1", "call-2", 3, 2, attempt_evidence(), None)

    # Then
    assert create_error.value is failure
    assert projected == []


async def test_successful_creation_can_bind_only_once() -> None:
    """A second destination cannot replace the context for this run."""
    # Given
    attempts = 0
    prepared = prepared_evidence()

    def create(_directory: Path, _plan: FrozenPlan) -> PreparedEvidence:
        nonlocal attempts
        attempts += 1
        return prepared

    store = create_evidence_store(create_evidence=create)

    # When
    assert await store.create(Path("results"), frozen_plan()) is prepared
    with pytest.raises(RuntimeError, match="already prepared"):
        await store.create(Path("other"), frozen_plan())

    # Then
    assert attempts == 1


async def test_settled_probe_is_projected_then_appended_and_returned() -> None:
    """Probe assessment and process projection settle before caller resumes."""
    # Given
    prepared = prepared_evidence()
    evidence = QuotaProbeEvidence(
        request=quota_probe_request(),
        process=attempt_evidence(),
        quota_state="unknown",
        observation=None,
        classification_basis="source unavailable",
    )
    settled = settled_probe_record(None, None, None, None)
    order: list[str] = []

    def project(
        context: PreparedEvidence, value: QuotaProbeEvidence
    ) -> QuotaProbeSettled:
        order.append("project")
        assert context is prepared
        assert value is evidence
        return settled

    def append(context: PreparedEvidence, value: QuotaProbeSettled) -> None:
        order.append("append")
        assert context is prepared
        assert value is settled

    store = create_evidence_store(
        create_evidence=lambda _directory, _plan: prepared,
        project_settled_probe=project,
        append_settled_probe=append,
    )
    await store.create(Path("results"), frozen_plan())

    # When
    result = await store.record_quota_probe_settled(evidence)

    # Then
    assert result is settled
    assert order == ["project", "append"]


async def test_probe_projection_failure_prevents_settled_append() -> None:
    """No settled record is appended when process projection fails."""
    # Given
    failure = ValueError("probe projection failed")
    appended: list[QuotaProbeSettled] = []

    def project(
        _context: PreparedEvidence,
        _evidence: QuotaProbeEvidence,
    ) -> QuotaProbeSettled:
        raise failure

    prepared = prepared_evidence()
    store = create_evidence_store(
        create_evidence=lambda _directory, _plan: prepared,
        project_settled_probe=project,
        append_settled_probe=lambda _context, event: appended.append(event),
    )
    await store.create(Path("results"), frozen_plan())

    # When
    evidence = QuotaProbeEvidence(
        request=quota_probe_request(),
        process=attempt_evidence(),
        quota_state="unknown",
        observation=None,
        classification_basis="source unavailable",
    )
    with pytest.raises(ValueError) as captured:
        await store.record_quota_probe_settled(evidence)

    # Then
    assert captured.value is failure
    assert appended == []


async def test_probe_append_failure_propagates_without_returning_settled_record() -> (
    None
):
    """A failed settled write reaches the caller with the original exception."""
    # Given
    failure = OSError("probe ledger unavailable")
    settled = settled_probe_record(None, None, None, None)

    def project(
        _context: PreparedEvidence, _evidence: QuotaProbeEvidence
    ) -> QuotaProbeSettled:
        return settled

    def append(_context: PreparedEvidence, _event: QuotaProbeSettled) -> None:
        raise failure

    prepared = prepared_evidence()
    store = create_evidence_store(
        create_evidence=lambda _directory, _plan: prepared,
        project_settled_probe=project,
        append_settled_probe=append,
    )
    await store.create(Path("results"), frozen_plan())
    evidence = QuotaProbeEvidence(
        request=quota_probe_request(),
        process=attempt_evidence(),
        quota_state="unknown",
        observation=None,
        classification_basis="source unavailable",
    )

    # When
    with pytest.raises(OSError) as captured:
        await store.record_quota_probe_settled(evidence)

    # Then
    assert captured.value is failure


async def test_lifecycle_telemetry_and_final_records_use_separate_ports() -> None:
    """Forward append-only values intact through their distinct store ports."""
    # Given
    observation = empty_quota_observation()
    schedule = quota_probe_request().schedule
    wait = quota_wait_event(observation)
    probe = QuotaProbeScheduled(kind="scheduled", schedule=schedule)
    telemetry = QuotaTelemetryEvent(
        run_id="run-1",
        call_id="call-1",
        attempt_number=1,
        observation=observation,
    )
    run = run_record()
    prepared = prepared_evidence()
    writes = EvidenceWrites(prepared)
    store = create_evidence_store(
        create_evidence=lambda _directory, _plan: prepared,
        append_wait_event=writes.append_wait,
        append_probe_event=writes.append_probe,
        append_quota_telemetry=writes.append_telemetry,
        finalize_evidence=writes.finalize,
    )
    await store.create(Path("results"), frozen_plan())

    # When
    await store.record_wait_event(wait)
    await store.record_quota_probe_event(probe)
    await store.record_quota_telemetry(telemetry)
    await store.finalize(run)

    # Then
    assert writes.order == ["wait", "probe", "telemetry", "final"]
    assert writes.waits == [wait]
    assert writes.probes == [probe]
    assert writes.telemetry == [telemetry]
    assert writes.runs == [run]


def quota_evidence_examples() -> tuple[
    QuotaObservation,
    QuotaProbeSettled,
    QuotaProbeSettled,
    QuotaProbeSettled,
    WaitEvent,
]:
    """Build unknown, empty, non-UTF8, and nested wait evidence examples."""
    empty_observation = empty_quota_observation()
    observed = settled_probe_record(
        empty_observation,
        b"",
        "artifacts/probe-stdout-empty",
        None,
    )
    unknown = settled_probe_record(None, None, None, None)
    non_utf8 = settled_probe_record(
        empty_observation,
        b"\xff\x00usage",
        None,
        "artifacts/probe-stderr",
    )
    context = QuotaWaitContext(
        kind="quota",
        trigger_call_id="call-1",
        trigger_attempt_number=1,
        cumulative_waited_before_seconds=0.0,
        wait_limit_seconds=None,
        quota_observation=empty_observation,
        selected_reset_at_utc=None,
    )
    wait = WaitEvent(
        run_id="run-1",
        wait_id="wait-1",
        context=context,
        kind="started",
        observed_at_utc="2026-10-26T00:00:02Z",
        elapsed_seconds=0.0,
        quota_observation=empty_observation,
        end=None,
        diagnostic=None,
    )

    return empty_observation, observed, unknown, non_utf8, wait


def assert_serialized_evidence(
    empty_observation: QuotaObservation,
    observed: QuotaProbeSettled,
    unknown: QuotaProbeSettled,
    non_utf8: QuotaProbeSettled,
    wait: WaitEvent,
) -> None:
    """Assert nested values and unavailable evidence survive serialization."""
    observed_record = observed.record
    assert observed_record.observation is not None
    assert observed_record.observation.windows == ()
    assert observed_record.usage_telemetry == b""
    assert observed_record.stdout_artifact == "artifacts/probe-stdout-empty"
    assert observed_record.stderr_artifact is None
    unknown_record = unknown.record
    assert unknown_record.observation is None
    assert unknown_record.usage_telemetry is None
    assert unknown_record.stdout_artifact is None
    assert unknown_record.stderr_artifact is None
    assert non_utf8.record.usage_telemetry == b"\xff\x00usage"
    assert non_utf8.record.request.schedule.scope == (
        quota_probe_request().schedule.scope
    )
    flattened = observed_record.model_dump()
    assert "control_flow" in flattened
    assert "argv" in flattened
    assert "process" not in flattened
    assert wait.quota_observation == empty_observation
    assert isinstance(wait.context, QuotaWaitContext)
    assert wait.context.quota_observation.windows == ()


def test_probe_and_wait_records_round_trip_without_filling_unknowns() -> None:
    """Keep nested quota data, bytes, and absent versus empty observations."""
    # Given
    empty_observation, observed, unknown, non_utf8, wait = quota_evidence_examples()

    # When
    observed_round_trip = QuotaProbeSettled.model_validate_json(
        observed.model_dump_json()
    )
    unknown_round_trip = QuotaProbeSettled.model_validate_json(
        unknown.model_dump_json()
    )
    non_utf8_round_trip = QuotaProbeSettled.model_validate_json(
        non_utf8.model_dump_json()
    )
    wait_round_trip = WaitEvent.model_validate_json(wait.model_dump_json())

    # Then
    assert_serialized_evidence(
        empty_observation,
        observed_round_trip,
        unknown_round_trip,
        non_utf8_round_trip,
        wait_round_trip,
    )


async def test_unfinished_default_storage_leaf_fails_visibly() -> None:
    """Default composition never implies persistence before leaf implementation."""
    # Given
    store = create_evidence_store()

    # When
    with pytest.raises(NotImplementedError) as captured:
        await store.create(Path("results"), frozen_plan())

    # Then
    assert "exclusive evidence creation" in str(captured.value)


async def test_blocked_leaf_does_not_block_loop_and_serializes_following_write() -> (
    None
):
    """Given a blocked append, keep the loop responsive and finalization queued."""
    # Given
    store, started, release, order = blocked_append_store()
    await store.create(Path("results"), frozen_plan())

    async def exercise() -> None:
        # When
        attempt = asyncio.create_task(
            store.record_attempt("run-1", "call-1", 0, 1, attempt_evidence(), None)
        )
        await wait_for_leaf_start(started, release)
        finalize = asyncio.create_task(store.finalize(run_record()))
        await asyncio.sleep(0)
        try:
            assert order == []
        finally:
            release.set()
        await asyncio.gather(attempt, finalize)

    await asyncio.wait_for(exercise(), timeout=5)
    # Then
    assert order == ["append", "finalize"]


async def test_owner_cancellation_waits_for_leaf_even_after_repeated_cancel() -> None:
    """Hold the lock through worker settlement after owner cancellation."""
    # Given
    store, started, release, order = blocked_append_store()
    await store.create(Path("results"), frozen_plan())
    attempt = asyncio.create_task(
        store.record_attempt("run-1", "call-1", 0, 1, attempt_evidence(), None)
    )
    await wait_for_leaf_start(started, release)
    finalize = asyncio.create_task(store.finalize(run_record()))
    await asyncio.sleep(0)

    # When
    try:
        attempt.cancel()
        await asyncio.sleep(0)
        attempt.cancel()
        await asyncio.sleep(0)
        assert not attempt.done()
        assert not finalize.done()
    finally:
        release.set()
    with pytest.raises(asyncio.CancelledError):
        await attempt
    await finalize

    # Then
    assert order == ["append", "finalize"]


async def test_cancelled_successful_create_binds_context_before_next_create() -> None:
    """Bind a create that succeeds during cancellation before releasing the lock."""
    # Given
    started = threading.Event()
    release = threading.Event()
    prepared = prepared_evidence()
    destinations: list[Path] = []

    def create(directory: Path, _plan: FrozenPlan) -> PreparedEvidence:
        destinations.append(directory)
        started.set()
        assert release.wait(5)
        return prepared

    store = create_evidence_store(create_evidence=create)
    owner = asyncio.create_task(store.create(Path("results"), frozen_plan()))
    await wait_for_leaf_start(started, release)
    # When
    try:
        owner.cancel()
        await asyncio.sleep(0)
    finally:
        release.set()
    with pytest.raises(asyncio.CancelledError):
        await owner
    with pytest.raises(RuntimeError, match="already prepared"):
        await store.create(Path("other"), frozen_plan())
    # Then
    assert destinations == [Path("results")]


async def test_cancellation_during_projection_waits_for_append() -> None:
    """Keep a projected record's required append inside cancellation ownership."""
    # Given
    started = threading.Event()
    release = threading.Event()
    order: list[str] = []
    prepared = prepared_evidence()

    def project(
        _context: PreparedEvidence,
        _run_id: RunId,
        _call_id: CallId,
        _position: int,
        _attempt_number: int,
        _evidence: AttemptEvidence,
        _assessment: RetryAssessment | None,
    ) -> AttemptRecord:
        started.set()
        assert release.wait(5)
        order.append("project")
        return attempt_record()

    store = create_evidence_store(
        create_evidence=lambda _directory, _plan: prepared,
        project_attempt=project,
        append_attempt=lambda _context, _record: order.append("append"),
    )
    await store.create(Path("results"), frozen_plan())
    owner = asyncio.create_task(
        store.record_attempt("run-1", "call-1", 0, 1, attempt_evidence(), None)
    )
    await wait_for_leaf_start(started, release)

    # When
    try:
        owner.cancel()
    finally:
        release.set()
    with pytest.raises(asyncio.CancelledError):
        await owner

    # Then
    assert order == ["project", "append"]


async def test_cancelled_lock_waiter_still_persists_after_prior_write() -> None:
    """A submitted operation remains queued and persists after owner cancellation."""
    # Given
    started = threading.Event()
    release = threading.Event()
    calls: list[str] = []
    prepared = prepared_evidence()

    def append(_context: PreparedEvidence, _event: WaitEvent) -> None:
        calls.append("append")
        started.set()
        assert release.wait(5)

    store = create_evidence_store(
        create_evidence=lambda _directory, _plan: prepared,
        append_wait_event=append,
        append_quota_telemetry=partial(append_telemetry, calls),
    )
    await store.create(Path("results"), frozen_plan())
    owner = asyncio.create_task(
        store.record_wait_event(quota_wait_event(empty_quota_observation()))
    )
    await wait_for_leaf_start(started, release)
    queued = asyncio.create_task(
        store.record_quota_telemetry(
            QuotaTelemetryEvent(
                run_id="run-1",
                call_id="call-1",
                attempt_number=1,
                observation=empty_quota_observation(),
            )
        )
    )
    await asyncio.sleep(0)
    # When
    try:
        queued.cancel()
    finally:
        release.set()
    await owner
    with pytest.raises(asyncio.CancelledError):
        await queued
    # Then
    assert calls == ["append", "telemetry"]


async def test_cancellation_preserves_concurrent_leaf_failure_as_cause_and_note() -> (
    None
):
    """Cancellation remains primary while a failed started write stays observable."""
    # Given
    started = threading.Event()
    release = threading.Event()
    failure = OSError("disk full")
    prepared = prepared_evidence()

    def append(_context: PreparedEvidence, _record: AttemptRecord) -> None:
        started.set()
        assert release.wait(5)
        raise failure

    store = create_evidence_store(
        create_evidence=lambda _directory, _plan: prepared,
        project_attempt=projected_attempt,
        append_attempt=append,
    )
    await store.create(Path("results"), frozen_plan())
    owner = asyncio.create_task(
        store.record_attempt("run-1", "call-1", 0, 1, attempt_evidence(), None)
    )
    await wait_for_leaf_start(started, release)
    # When
    try:
        owner.cancel()
        await asyncio.sleep(0)
    finally:
        release.set()
    with pytest.raises(asyncio.CancelledError) as captured:
        await owner
    # Then
    assert captured.value.__cause__ is failure
    assert any("disk full" in note for note in captured.value.__notes__)
