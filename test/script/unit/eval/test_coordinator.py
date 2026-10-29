# SPDX-License-Identifier: Apache-2.0
"""Run coordination through real call owners and filesystem evidence."""

import asyncio
from dataclasses import replace
from pathlib import Path
from threading import Event as ThreadEvent
from typing import override

import pytest

from script.eval.evidence import EvidenceStoreAdapter, create_evidence_store
from script.eval.model import (
    AttemptEvidence,
    AttemptRecord,
    FrozenPlan,
    PreparedEvidence,
    QuotaObservation,
    QuotaProbeEvidence,
    QuotaProbeRequest,
    QuotaScope,
    QuotaWaitContext,
    RetryAssessment,
    RunRecord,
    SourceSnapshot,
)
from script.eval.runner.coordinator import Coordinator
from script.eval.runner.coordinator.coordinator import _raise_outcome, _stop_watcher
from script.eval.runner.coordinator.settlement import SettledFailure, SettledValue
from script.eval.runner.ports import BoundRun, CliBinding, ProgressSnapshot
from script.process_supervisor import (
    AttemptObservation,
    AttemptRequest,
    AttemptResult,
    CapturedOutput,
    CleanupEvidence,
    Completed,
    DispatchStop,
    OutputLimitExceeded,
    SignalAttempt,
)
from test.script.unit.eval.test_coordinator_calls import (
    Classifier,
    Clock,
    NoQuota,
    Store,
)
from test.script.unit.eval.test_coordinator_states import (
    assessment,
    call,
    config,
    observation,
)


class Sink:
    """Retain coordinator snapshots for independent accounting assertions."""

    def __init__(self) -> None:
        self.snapshots: list[ProgressSnapshot] = []

    def publish(self, snapshot: ProgressSnapshot, /) -> None:
        """Record a snapshot without other effects."""
        self.snapshots.append(snapshot)


async def prepare(
    tmp_path: Path,
    count: int,
    *,
    store: EvidenceStoreAdapter | None = None,
    **options: object,
) -> tuple[BoundRun, EvidenceStoreAdapter]:
    """Create an exclusive evidence area for a frozen typed matrix."""
    template = call()
    calls = tuple(
        replace(
            template,
            call_id=f"call-{position}",
            planned_call=template.planned_call.model_copy(
                update={"position": position}
            ),
            request=replace(template.request, argv=("cmd", str(position))),
        )
        for position in range(count)
    )
    plan = FrozenPlan(
        run_id="run",
        configuration=config(**options),
        repository_root=Path("/tmp"),
        head_commit="head",
        snapshots=(
            SourceSnapshot(
                directory_position=0,
                repository_path="context/a",
                commit_blob_sha="blob",
                content_sha256="source-digest",
                content=b"context",
            ),
        ),
        boundary_bytes=(b"\n\n",),
        instructions_file=None,
        calls=tuple(item.planned_call for item in calls),
    )
    store = store or create_evidence_store()
    prepared = await store.create(tmp_path / "output", plan)
    return BoundRun(
        plan,
        CliBinding(
            Path("/tmp/codex"),
            "1",
            "runner",
            (("setting", "value"),),
            observation().scope if plan.configuration.quota_wait_enabled else None,
        ),
        prepared,
        calls,
    ), store


def result() -> Completed:
    """Return a safely reaped, successful supervisor outcome."""
    return Completed(
        AttemptObservation(
            CapturedOutput(b"out", b"err"),
            1.0,
            CleanupEvidence(
                "owned", (SignalAttempt("SIGKILL", "sent", None),), "reaped", None
            ),
        ),
        0,
    )


async def attempt(request: AttemptRequest, stop: DispatchStop, /) -> AttemptResult:
    """Yield once and return a controlled supervisor result."""
    await asyncio.sleep(0)
    return result()


async def test_frozen_matrix_runs_and_finalizes_real_evidence(tmp_path: Path) -> None:
    # Given
    bound, store = await prepare(tmp_path, 3, concurrency=2)
    sink = Sink()
    coordinator = Coordinator(
        bound, store, attempt, Classifier(), NoQuota(), Clock(), sink
    )

    # When
    record = await coordinator.run()

    # Then
    assert record.state == "complete"
    assert [(item.position, item.state) for item in record.calls] == [
        (0, "complete"),
        (1, "complete"),
        (2, "complete"),
    ]
    assert [item.source_paths for item in record.calls] == [("context/a",)] * 3
    assert record.calls[0].source_sha256 == ("source-digest",)
    assert record.calls[0].boundary_bytes_hex == ("0a0a",)
    assert record.calls[0].prompt_sha256 == "digest"
    assert (
        record.calls[0].effective_settings_sha256
        == "ba3f3fe73afa35af8be97ad36bff0fff85da5e0b199e35fc0e987aa4e845ad42"
    )
    assert [item.attempts[0].argv for item in record.calls] == [
        ("cmd", "0"),
        ("cmd", "1"),
        ("cmd", "2"),
    ]
    assert sink.snapshots[-1].phase == "final"
    assert sink.snapshots[-1].counts.calls_succeeded == 3
    assert (bound.evidence.output_directory / "run.json").is_file()


async def test_reuse_is_refused(tmp_path: Path) -> None:
    # Given
    bound, store = await prepare(tmp_path, 0)
    coordinator = Coordinator(
        bound, store, attempt, Classifier(), NoQuota(), Clock(), Sink()
    )
    await coordinator.run()

    # When / Then
    with pytest.raises(RuntimeError, match="already ran"):
        await coordinator.run()


class BlockingAttempts:
    """Hold invoked attempts until explicitly released."""

    def __init__(self, expected: int) -> None:
        self.expected = expected
        self.started: list[str] = []
        self.full = asyncio.Event()
        self.release = asyncio.Event()

    async def __call__(
        self, request: AttemptRequest, stop: DispatchStop, /
    ) -> AttemptResult:
        """Record an invocation and await controlled completion."""
        self.started.append(request.argv[1])
        if len(self.started) == self.expected:
            self.full.set()
        await self.release.wait()
        return result()


async def test_concurrency_bounds_invocations_until_cleanup_finishes(
    tmp_path: Path,
) -> None:
    # Given
    bound, store = await prepare(tmp_path, 3, concurrency=2)
    blocked = BlockingAttempts(2)
    task = asyncio.create_task(
        Coordinator(
            bound, store, blocked, Classifier(), NoQuota(), Clock(), Sink()
        ).run()
    )
    await blocked.full.wait()

    # When
    before_release = tuple(blocked.started)
    blocked.release.set()
    record = await task

    # Then
    assert before_release == ("0", "1")
    assert blocked.started == ["0", "1", "2"]
    assert record.state == "complete"


class CancelledAttempt:
    """Model a supervisor whose cancellation cleanup has not yet settled."""

    def __init__(self) -> None:
        self.entered = asyncio.Event()
        self.cleaning = asyncio.Event()
        self.release = asyncio.Event()

    async def __call__(
        self, request: AttemptRequest, stop: DispatchStop, /
    ) -> AttemptResult:
        """Hold cancellation until the simulated cleanup is released."""
        self.entered.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            self.cleaning.set()
            await self.release.wait()
            raise
        raise AssertionError("unreachable")


async def test_owner_cancellation_waits_for_attempt_cleanup_and_finalizes(
    tmp_path: Path,
) -> None:
    # Given
    bound, store = await prepare(tmp_path, 2, concurrency=1)
    blocked, sink = CancelledAttempt(), Sink()
    task = asyncio.create_task(
        Coordinator(bound, store, blocked, Classifier(), NoQuota(), Clock(), sink).run()
    )
    await blocked.entered.wait()

    # When
    task.cancel("owner")
    await blocked.cleaning.wait()
    assert not task.done()
    task.cancel("later")
    await asyncio.sleep(0)
    assert not task.done()
    blocked.release.set()
    with pytest.raises(asyncio.CancelledError, match="owner"):
        await task

    # Then
    record = RunRecord.model_validate_json(
        (bound.evidence.output_directory / "run.json").read_bytes()
    )
    assert record.state == "incomplete"
    assert [item.state for item in record.calls] == ["failed", "not_started"]
    assert sink.snapshots[-1].final_status == "cancelled"


async def test_failed_attempt_write_retains_no_fabricated_attempt(
    tmp_path: Path,
) -> None:
    # Given
    failure = OSError("attempt write")

    def fail_write(prepared: PreparedEvidence, record: AttemptRecord) -> None:
        """Fail the append after process evidence has been captured."""
        raise failure

    store = create_evidence_store(append_attempt=fail_write)
    bound, store = await prepare(tmp_path, 2, store=store, concurrency=1)
    sink = Sink()
    coordinator = Coordinator(
        bound, store, attempt, Classifier(), NoQuota(), Clock(), sink
    )

    # When
    record = await coordinator.run()

    # Then
    assert record.state == "incomplete"
    assert [item.state for item in record.calls] == ["failed", "not_started"]
    assert record.calls[0].attempts == ()
    assert sink.snapshots[-1].counts.calls_evidence_pending == 1
    assert sink.snapshots[-1].counts.attempts_evidence_pending == 1


class QuotaAttempt:
    """Exhaust quota while another attempt remains active."""

    def __init__(self) -> None:
        self.second_started = asyncio.Event()
        self.release_second = asyncio.Event()
        self.first_count = 0

    async def __call__(
        self, request: AttemptRequest, stop: DispatchStop, /
    ) -> AttemptResult:
        """Return quota exhaustion once, then safe completions."""
        if request.argv[1] == "1":
            self.second_started.set()
            await self.release_second.wait()
        if request.argv[1] == "0" and self.first_count == 0:
            self.first_count += 1
            await self.second_started.wait()
            return replace(result(), exit_status=1)
        return result()


class QuotaClassifier(Classifier):
    """Recognize only the controlled quota-exhaustion outcome."""

    @override
    def assess(self, evidence: AttemptEvidence, /) -> RetryAssessment:
        """Classify the first nonzero process as quota exhaustion."""
        if (
            isinstance(evidence.outcome, Completed)
            and evidence.outcome.exit_status == 1
        ):
            return assessment("quota")
        return assessment("other")


class RecoveryReader(NoQuota):
    """Supply one durable exhaustion observation and a fresh probe."""

    def __init__(self) -> None:
        self.observed = asyncio.Event()
        self.probed = asyncio.Event()
        self.observations = 0

    @property
    @override
    def expected_scope(self) -> QuotaScope | None:
        """Return the controlled provider scope."""
        return observation().scope

    @override
    async def observe_settled_attempt(
        self, evidence: AttemptEvidence, /
    ) -> QuotaObservation:
        """Return exhaustion for the trigger and availability afterward."""
        self.observations += 1
        value = observation()
        if self.observations == 1:
            self.observed.set()
            return value.model_copy(
                update={
                    "windows": (
                        value.windows[0].model_copy(update={"state": "exhausted"}),
                    )
                }
            )
        return value

    @override
    async def poll(
        self, request: QuotaProbeRequest, stop: DispatchStop, /
    ) -> QuotaProbeEvidence:
        """Return separately supervised probe evidence with fresh availability."""
        self.probed.set()
        process = AttemptEvidence(
            "returned",
            result(),
            None,
            None,
            call().request,
            "2026-01-01T00:00:00Z",
            "2026-01-01T00:00:01Z",
            b"out",
        )
        return QuotaProbeEvidence(
            request, process, "available", observation(), "confirmed"
        )


async def test_quota_recovery_waits_for_active_cleanup_and_retries_origin(
    tmp_path: Path,
) -> None:
    # Given
    bound, store = await prepare(tmp_path, 2, concurrency=2, quota_wait_enabled=True)
    attempts, reader = QuotaAttempt(), RecoveryReader()
    task = asyncio.create_task(
        Coordinator(
            bound, store, attempts, QuotaClassifier(), reader, Clock(), Sink()
        ).run()
    )
    await reader.observed.wait()

    # When
    assert not reader.probed.is_set()
    attempts.release_second.set()
    record = await task

    # Then
    assert reader.probed.is_set()
    assert [len(item.attempts) for item in record.calls] == [2, 1]
    assert [item.state for item in record.calls] == ["complete", "complete"]
    assert len(record.waits) == 1
    assert record.waits[0].end == "quota_available"


class CapacityClock(Clock):
    """Keep one capacity delay asleep until explicitly released."""

    def __init__(self) -> None:
        self.waiting = asyncio.Event()
        self.release = asyncio.Event()

    @override
    def uniform(self, lower: float, upper: float, /) -> float:
        """Select the full deterministic backoff bound."""
        return upper

    @override
    async def sleep(self, seconds: float, /) -> None:
        """Block capacity delay while allowing zero-duration yields."""
        if seconds == 0:
            await asyncio.sleep(0)
            return
        self.waiting.set()
        await self.release.wait()


class CapacityAttempt:
    """Return a retryable capacity failure only for the first call."""

    def __init__(self) -> None:
        self.first_count = 0
        self.second_started = asyncio.Event()

    async def __call__(
        self, request: AttemptRequest, stop: DispatchStop, /
    ) -> AttemptResult:
        """Record the other call while the first waits for backoff."""
        if request.argv[1] == "1":
            self.second_started.set()
        if request.argv[1] == "0" and self.first_count == 0:
            self.first_count += 1
            return replace(result(), exit_status=1)
        return result()


class CapacityClassifier(Classifier):
    """Mark the controlled nonzero result as retryable capacity failure."""

    @override
    def assess(self, evidence: AttemptEvidence, /) -> RetryAssessment:
        """Classify without inspecting semantic output."""
        if (
            isinstance(evidence.outcome, Completed)
            and evidence.outcome.exit_status == 1
        ):
            return assessment("capacity")
        return assessment("other")


async def test_capacity_delay_does_not_block_another_planned_call(
    tmp_path: Path,
) -> None:
    # Given
    bound, store = await prepare(
        tmp_path,
        2,
        concurrency=1,
        capacity_retry_limit=1,
        capacity_backoff_base_seconds=1.0,
        capacity_backoff_cap_seconds=1.0,
    )
    clock, attempts = CapacityClock(), CapacityAttempt()
    task = asyncio.create_task(
        Coordinator(
            bound, store, attempts, CapacityClassifier(), NoQuota(), clock, Sink()
        ).run()
    )
    await clock.waiting.wait()

    # When
    await attempts.second_started.wait()
    clock.release.set()
    record = await task

    # Then
    assert [len(item.attempts) for item in record.calls] == [2, 1]
    assert [item.state for item in record.calls] == ["complete", "complete"]
    assert record.waits[0].end == "delay_elapsed"


class StopDuringCapacity(CapacityAttempt):
    """Stop the run when the second call starts during a retry wait."""

    @override
    async def __call__(
        self, request: AttemptRequest, stop: DispatchStop, /
    ) -> AttemptResult:
        """Latch the supervisor stop without turning it into owner cancellation."""
        if request.argv[1] == "1":
            value = result()
            stop(value)
            return value
        return await super().__call__(request, stop)


async def test_stop_cancels_and_durably_closes_sibling_capacity_wait(
    tmp_path: Path,
) -> None:
    # Given
    bound, store = await prepare(
        tmp_path,
        2,
        concurrency=1,
        capacity_retry_limit=1,
        capacity_backoff_base_seconds=1.0,
        capacity_backoff_cap_seconds=1.0,
    )
    clock = CapacityClock()
    coordinator = Coordinator(
        bound,
        store,
        StopDuringCapacity(),
        CapacityClassifier(),
        NoQuota(),
        clock,
        Sink(),
    )

    # When
    record = await coordinator.run()

    # Then
    assert record.state == "incomplete"
    assert record.waits[0].end == "cancelled"
    assert [len(item.attempts) for item in record.calls] == [1, 1]


async def test_repeated_cancellation_retains_final_write(tmp_path: Path) -> None:
    # Given
    started, release = asyncio.Event(), ThreadEvent()
    loop = asyncio.get_running_loop()
    written: list[RunRecord] = []

    def finalize(prepared: PreparedEvidence, record: RunRecord) -> None:
        """Block the submitted write in its worker thread."""
        loop.call_soon_threadsafe(started.set)
        assert release.wait(5)
        written.append(record)

    store = create_evidence_store(finalize_evidence=finalize)
    bound, store = await prepare(tmp_path, 0, store=store)
    sink = Sink()
    task = asyncio.create_task(
        Coordinator(bound, store, attempt, Classifier(), NoQuota(), Clock(), sink).run()
    )
    await started.wait()

    # When
    task.cancel("first")
    await asyncio.sleep(0)
    task.cancel("second")
    await asyncio.sleep(0)
    assert not task.done()
    release.set()
    with pytest.raises(asyncio.CancelledError, match="first"):
        await task

    # Then
    assert len(written) == 1
    assert sink.snapshots[-1].phase == "final"
    assert sink.snapshots[-1].final_status == "cancelled"


async def test_quota_probe_waits_for_active_attempt_record_write(
    tmp_path: Path,
) -> None:
    # Given
    entered, release = asyncio.Event(), ThreadEvent()
    loop = asyncio.get_running_loop()

    def append(prepared: PreparedEvidence, record: AttemptRecord) -> None:
        """Hold the second attempt write, then publish a unique record."""
        if record.position == 1:
            loop.call_soon_threadsafe(entered.set)
            assert release.wait(5)
        path = (
            prepared.output_directory
            / f"attempt-{record.position}-{record.attempt_number}.json"
        )
        with path.open("x") as stream:
            stream.write(record.model_dump_json())

    store = create_evidence_store(append_attempt=append)
    bound, store = await prepare(
        tmp_path, 2, store=store, concurrency=2, quota_wait_enabled=True
    )
    attempts, reader = QuotaAttempt(), RecoveryReader()
    task = asyncio.create_task(
        Coordinator(
            bound, store, attempts, QuotaClassifier(), reader, Clock(), Sink()
        ).run()
    )
    await reader.observed.wait()
    attempts.release_second.set()
    await entered.wait()

    # When
    assert not reader.probed.is_set()
    release.set()
    record = await task

    # Then
    assert reader.probed.is_set()
    assert record.state == "complete"
    assert [len(item.attempts) for item in record.calls] == [2, 1]


@pytest.mark.parametrize(
    ("local", "final", "owner", "primary", "cause"),
    [
        (asyncio.CancelledError("local"), OSError("write"), None, "local", "final"),
        (ValueError("call"), asyncio.CancelledError("leaf"), None, "final", "local"),
        (
            ValueError("call"),
            OSError("write"),
            asyncio.CancelledError("owner"),
            "owner",
            "final",
        ),
        (ValueError("call"), OSError("write"), None, "local", "final"),
        (None, asyncio.CancelledError("leaf"), None, "final", None),
    ],
    ids=["local-cancel", "leaf-cancel", "owner-cancel", "ordinary-error", "leaf-only"],
)
def test_final_outcome_preserves_exception_identity_and_cause(
    local: BaseException | None,
    final: BaseException,
    owner: asyncio.CancelledError | None,
    primary: str,
    cause: str | None,
) -> None:
    # Given
    errors = {"local": local, "final": final, "owner": owner}
    expected = errors[primary]
    assert expected is not None

    # When
    with pytest.raises(type(expected)) as raised:
        _raise_outcome(local, SettledFailure(final, owner))

    # Then
    assert raised.value is expected
    assert raised.value.__cause__ is (None if cause is None else errors[cause])


def test_final_outcome_does_not_chain_an_exception_to_itself() -> None:
    # Given
    cancellation = asyncio.CancelledError("same")

    # When
    with pytest.raises(asyncio.CancelledError) as raised:
        _raise_outcome(cancellation, SettledFailure(cancellation, None))

    # Then
    assert raised.value is cancellation
    assert cancellation.__cause__ is None


def test_owner_cancellation_after_successful_finalization_remains_primary() -> None:
    # Given
    original = ValueError("call")
    cancellation = asyncio.CancelledError("owner")

    # When
    with pytest.raises(asyncio.CancelledError) as raised:
        _raise_outcome(original, SettledValue(None, cancellation))

    # Then
    assert raised.value is cancellation
    assert cancellation.__cause__ is original


def test_same_owner_and_leaf_cancellation_does_not_cause_itself() -> None:
    # Given
    original = ValueError("call")
    cancellation = asyncio.CancelledError("same")

    # When
    with pytest.raises(asyncio.CancelledError) as raised:
        _raise_outcome(original, SettledFailure(cancellation, cancellation))

    # Then
    assert raised.value is cancellation
    assert cancellation.__cause__ is original


async def test_finalization_failure_stops_without_final_success_report(
    tmp_path: Path,
) -> None:
    # Given
    failure = OSError("final write")

    def finalize(prepared: PreparedEvidence, record: RunRecord) -> None:
        """Fail the requested final accounting write."""
        raise failure

    store = create_evidence_store(finalize_evidence=finalize)
    bound, store = await prepare(tmp_path, 1, store=store)
    sink = Sink()
    coordinator = Coordinator(
        bound, store, attempt, Classifier(), NoQuota(), Clock(), sink
    )

    # When
    with pytest.raises(OSError, match="final write") as raised:
        await coordinator.run()

    # Then
    assert raised.value is failure
    assert coordinator._control.reason is not None
    assert coordinator._control.reason.recording_failure is failure
    assert all(snapshot.phase != "final" for snapshot in sink.snapshots)


async def test_final_write_failure_is_cause_of_owner_cancellation(
    tmp_path: Path,
) -> None:
    # Given
    started, release = asyncio.Event(), ThreadEvent()
    loop = asyncio.get_running_loop()
    failure = OSError("final write")

    def finalize(prepared: PreparedEvidence, record: RunRecord) -> None:
        """Fail only after the cancelled owner allows the write to finish."""
        loop.call_soon_threadsafe(started.set)
        assert release.wait(5)
        raise failure

    store = create_evidence_store(finalize_evidence=finalize)
    bound, store = await prepare(tmp_path, 0, store=store)
    sink = Sink()
    coordinator = Coordinator(
        bound, store, attempt, Classifier(), NoQuota(), Clock(), sink
    )
    task = asyncio.create_task(coordinator.run())
    await started.wait()

    # When
    task.cancel("owner")
    await asyncio.sleep(0)
    release.set()
    with pytest.raises(asyncio.CancelledError, match="owner") as raised:
        await task

    # Then
    assert raised.value.__cause__ is failure
    assert coordinator._control.reason is not None
    assert coordinator._control.reason.recording_failure is failure
    assert all(snapshot.phase != "final" for snapshot in sink.snapshots)


class LeafCancelledAttempt:
    """Cancel one invocation while its sibling owns cleanup."""

    def __init__(self) -> None:
        self.error = asyncio.CancelledError("leaf")
        self.sibling_entered = asyncio.Event()
        self.sibling_cleaning = asyncio.Event()
        self.release = asyncio.Event()

    async def __call__(
        self, request: AttemptRequest, stop: DispatchStop, /
    ) -> AttemptResult:
        """Raise the exact leaf cancellation and retain sibling cleanup."""
        if request.argv[1] == "0":
            await self.sibling_entered.wait()
            raise self.error
        self.sibling_entered.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            self.sibling_cleaning.set()
            await self.release.wait()
            raise
        raise AssertionError("unreachable")


async def test_leaf_cancellation_stays_primary_while_sibling_cleanup_settles(
    tmp_path: Path,
) -> None:
    # Given
    bound, store = await prepare(tmp_path, 2, concurrency=2)
    calls = LeafCancelledAttempt()
    task = asyncio.create_task(
        Coordinator(bound, store, calls, Classifier(), NoQuota(), Clock(), Sink()).run()
    )
    await calls.sibling_cleaning.wait()

    # When
    assert not task.done()
    calls.release.set()
    with pytest.raises(asyncio.CancelledError, match="leaf") as raised:
        await task

    # Then
    assert raised.value is calls.error
    record = RunRecord.model_validate_json(
        (bound.evidence.output_directory / "run.json").read_bytes()
    )
    assert record.state == "incomplete"
    assert [len(item.attempts) for item in record.calls] == [1, 1]


async def test_owner_cancellation_preserves_attempt_recording_failure(
    tmp_path: Path,
) -> None:
    # Given
    entered, release = asyncio.Event(), ThreadEvent()
    loop = asyncio.get_running_loop()
    failure = OSError("attempt write")

    def append(prepared: PreparedEvidence, record: AttemptRecord) -> None:
        """Fail a submitted attempt write after owner cancellation."""
        loop.call_soon_threadsafe(entered.set)
        assert release.wait(5)
        raise failure

    store = create_evidence_store(append_attempt=append)
    bound, store = await prepare(tmp_path, 1, store=store)
    sink = Sink()
    task = asyncio.create_task(
        Coordinator(bound, store, attempt, Classifier(), NoQuota(), Clock(), sink).run()
    )
    await entered.wait()

    # When
    task.cancel("owner")
    await asyncio.sleep(0)
    assert not task.done()
    release.set()
    with pytest.raises(asyncio.CancelledError, match="owner") as raised:
        await task

    # Then
    assert raised.value.__cause__ is failure
    assert sink.snapshots[-1].counts.calls_evidence_pending == 1
    record = RunRecord.model_validate_json(
        (bound.evidence.output_directory / "run.json").read_bytes()
    )
    assert record.calls[0].state == "failed"
    assert record.calls[0].attempts == ()


async def unsafe_last(request: AttemptRequest, stop: DispatchStop, /) -> AttemptResult:
    """Return an unsafe cleanup observation without relying on a later call."""
    await asyncio.sleep(0)
    return Completed(
        AttemptObservation(
            None,
            1.0,
            CleanupEvidence("acquisition_uncertain", (), "unknown", "unknown process"),
        ),
        0,
    )


async def test_unsafe_cleanup_on_last_call_makes_run_incomplete(tmp_path: Path) -> None:
    # Given
    bound, store = await prepare(tmp_path, 1)
    sink = Sink()

    # When
    record = await Coordinator(
        bound, store, unsafe_last, Classifier(), NoQuota(), Clock(), sink
    ).run()

    # Then
    assert record.state == "incomplete"
    assert record.calls[0].state == "failed"
    assert record.calls[0].attempts[0].cleanup is not None
    assert record.calls[0].attempts[0].cleanup.process == "acquisition_uncertain"
    assert sink.snapshots[-1].final_status == "incomplete_evidence"


async def overflow(request: AttemptRequest, stop: DispatchStop, /) -> AttemptResult:
    """Return a safely cleaned output overflow."""
    await asyncio.sleep(0)
    return OutputLimitExceeded(result().observation, None)


async def test_overflow_stops_before_the_next_planned_call(tmp_path: Path) -> None:
    # Given
    bound, store = await prepare(tmp_path, 2, concurrency=1)

    # When
    record = await Coordinator(
        bound, store, overflow, Classifier(), NoQuota(), Clock(), Sink()
    ).run()

    # Then
    assert record.state == "incomplete"
    assert [item.state for item in record.calls] == ["failed", "not_started"]
    assert record.calls[0].attempts[0].outcome_kind == "output_limit_exceeded"


class UncertainQuotaClassifier(Classifier):
    """Classify quota exhaustion without claiming the answer is absent."""

    @override
    def assess(self, evidence: AttemptEvidence, /) -> RetryAssessment:
        """Return quota classification with an unknown semantic result."""
        return assessment("quota", "present_or_unknown")


async def test_no_quota_probe_when_no_call_can_continue(tmp_path: Path) -> None:
    # Given
    bound, store = await prepare(tmp_path, 1, quota_wait_enabled=True)
    reader = RecoveryReader()

    # When
    record = await Coordinator(
        bound,
        store,
        nonzero_attempt,
        UncertainQuotaClassifier(),
        reader,
        Clock(),
        Sink(),
    ).run()

    # Then
    assert record.calls[0].state == "failed"
    assert not reader.probed.is_set()
    assert record.waits == ()


async def nonzero_attempt(
    request: AttemptRequest, stop: DispatchStop, /
) -> AttemptResult:
    """Return a settled nonzero process without interpreting its output."""
    await asyncio.sleep(0)
    return replace(result(), exit_status=1)


class StaleRecoveryReader(RecoveryReader):
    """Return a correctly scoped but expired exhaustion observation."""

    @override
    async def observe_settled_attempt(
        self, evidence: AttemptEvidence, /
    ) -> QuotaObservation:
        """Make the triggering telemetry stale before recovery."""
        value = await super().observe_settled_attempt(evidence)
        return value.model_copy(update={"valid_until_utc": "2025-12-31T23:59:59Z"})


async def test_stale_quota_trigger_cannot_authorize_a_probe(tmp_path: Path) -> None:
    # Given
    bound, store = await prepare(tmp_path, 1, quota_wait_enabled=True)
    reader = StaleRecoveryReader()

    # When
    record = await Coordinator(
        bound, store, nonzero_attempt, QuotaClassifier(), reader, Clock(), Sink()
    ).run()

    # Then
    assert record.state == "incomplete"
    assert not reader.probed.is_set()
    assert len(record.calls[0].attempts) == 1
    assert record.waits[0].end == "unknown"


async def test_cancellation_during_quota_wait_retains_closed_wait(
    tmp_path: Path,
) -> None:
    # Given
    bound, store = await prepare(tmp_path, 1, quota_wait_enabled=True)
    clock, reader, sink = CapacityClock(), RecoveryReader(), Sink()
    task = asyncio.create_task(
        Coordinator(
            bound, store, nonzero_attempt, QuotaClassifier(), reader, clock, sink
        ).run()
    )
    await clock.waiting.wait()

    # When
    task.cancel("owner")
    with pytest.raises(asyncio.CancelledError, match="owner"):
        await task

    # Then
    record = RunRecord.model_validate_json(
        (bound.evidence.output_directory / "run.json").read_bytes()
    )
    assert record.state == "incomplete"
    assert len(record.waits) == 1
    assert record.waits[0].end == "cancelled"
    assert not reader.probed.is_set()
    assert sink.snapshots[-1].final_status == "cancelled"


class FailedSink:
    """Raise one configured presentation failure."""

    def __init__(self, error: BaseException) -> None:
        self.error = error
        self.calls = 0

    def publish(self, snapshot: ProgressSnapshot, /) -> None:
        """Fail at the presentation boundary."""
        self.calls += 1
        raise self.error


async def test_expected_progress_failure_disables_further_presentation(
    tmp_path: Path,
) -> None:
    # Given
    bound, store = await prepare(tmp_path, 1)
    sink = FailedSink(OSError("closed output"))

    # When
    record = await Coordinator(
        bound, store, attempt, Classifier(), NoQuota(), Clock(), sink
    ).run()

    # Then
    assert record.state == "complete"
    assert record.calls[0].state == "complete"
    assert sink.calls == 1


async def test_progress_cancellation_propagates_after_finalization(
    tmp_path: Path,
) -> None:
    # Given
    bound, store = await prepare(tmp_path, 1)
    cancellation = asyncio.CancelledError("presenter")
    sink = FailedSink(cancellation)

    # When
    with pytest.raises(asyncio.CancelledError) as raised:
        await Coordinator(
            bound, store, attempt, Classifier(), NoQuota(), Clock(), sink
        ).run()

    # Then
    assert raised.value is cancellation
    record = RunRecord.model_validate_json(
        (bound.evidence.output_directory / "run.json").read_bytes()
    )
    assert record.state == "incomplete"
    assert record.calls[0].state == "not_started"


async def test_watcher_join_retains_owner_cancellation() -> None:
    # Given
    started, cleaning, release = asyncio.Event(), asyncio.Event(), asyncio.Event()

    async def watcher() -> object:
        """Delay watcher cancellation until cleanup is released."""
        started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cleaning.set()
            await release.wait()
            raise
        raise AssertionError("unreachable")

    owned = asyncio.create_task(watcher())
    await started.wait()
    joining = asyncio.create_task(_stop_watcher(owned))
    await cleaning.wait()

    # When
    joining.cancel("owner")
    await asyncio.sleep(0)
    assert not joining.done()
    release.set()
    cancellation = await joining

    # Then
    assert isinstance(cancellation, asyncio.CancelledError)
    assert str(cancellation) == "owner"
    assert owned.done()


async def test_mismatched_binding_scope_never_authorizes_quota_probe(
    tmp_path: Path,
) -> None:
    # Given
    original, store = await prepare(tmp_path, 1, quota_wait_enabled=True)
    bound = replace(original, binding=replace(original.binding, quota_scope=None))
    reader = RecoveryReader()

    # When
    record = await Coordinator(
        bound, store, nonzero_attempt, QuotaClassifier(), reader, Clock(), Sink()
    ).run()

    # Then
    assert record.state == "incomplete"
    assert not reader.probed.is_set()
    assert len(record.calls[0].attempts) == 1
    assert record.waits == ()


async def test_progress_retains_durable_passive_quota_observation(
    tmp_path: Path,
) -> None:
    # Given
    bound, store = await prepare(tmp_path, 1, quota_wait_enabled=True)
    reader, sink = RecoveryReader(), Sink()

    # When
    record = await Coordinator(
        bound, store, attempt, Classifier(), reader, Clock(), sink
    ).run()

    # Then
    assert record.state == "complete"
    assert sink.snapshots[-1].quota_observation is not None
    assert sink.snapshots[-1].quota_observation.windows[0].state == "exhausted"
    assert not reader.probed.is_set()


class AdvancingClock(Clock):
    """Advance monotonic time on each deterministic quota delay."""

    def __init__(self) -> None:
        self.now = 0.0

    @override
    def monotonic(self) -> float:
        """Return the manually advanced clock."""
        return self.now

    @override
    async def sleep(self, seconds: float, /) -> None:
        """Advance time and yield without wall-clock waiting."""
        self.now += seconds
        await asyncio.sleep(0)


class DoubleQuotaAttempt:
    """Return two exhausted attempts followed by a successful attempt."""

    def __init__(self) -> None:
        self.count = 0

    async def __call__(
        self, request: AttemptRequest, stop: DispatchStop, /
    ) -> AttemptResult:
        """Return two nonzero quota outcomes, then a successful outcome."""
        self.count += 1
        await asyncio.sleep(0)
        return replace(result(), exit_status=1) if self.count <= 2 else result()


class DoubleRecoveryReader(RecoveryReader):
    """Supply exhausted telemetry for two distinct pause origins."""

    @override
    async def observe_settled_attempt(
        self, evidence: AttemptEvidence, /
    ) -> QuotaObservation:
        """Return exhaustion for the first two attempts."""
        self.observations += 1
        value = observation()
        if self.observations <= 2:
            return value.model_copy(
                update={
                    "windows": (
                        value.windows[0].model_copy(update={"state": "exhausted"}),
                    )
                }
            )
        return value


async def test_separate_quota_pauses_retain_cumulative_wait_history(
    tmp_path: Path,
) -> None:
    # Given
    bound, store = await prepare(tmp_path, 1, quota_wait_enabled=True)
    reader, clock = DoubleRecoveryReader(), AdvancingClock()

    # When
    record = await Coordinator(
        bound, store, DoubleQuotaAttempt(), QuotaClassifier(), reader, clock, Sink()
    ).run()

    # Then
    assert record.state == "complete"
    assert len(record.calls[0].attempts) == 3
    first, second = record.waits
    assert isinstance(first.context, QuotaWaitContext)
    assert isinstance(second.context, QuotaWaitContext)
    assert first.context.cumulative_waited_before_seconds == pytest.approx(0.0)
    assert second.context.cumulative_waited_before_seconds == pytest.approx(60.0)
    assert [wait.end for wait in record.waits] == ["quota_available", "quota_available"]


class LeafFinalStore(Store):
    """Raise the exact cancellation at the async evidence boundary."""

    def __init__(self, cancellation: asyncio.CancelledError) -> None:
        super().__init__()
        self.cancellation = cancellation

    @override
    async def finalize(self, record: RunRecord, /) -> None:
        """Fail with the retained cancellation object."""
        raise self.cancellation


async def test_finalization_leaf_cancellation_preserves_prior_local_error(
    tmp_path: Path,
) -> None:
    # Given
    original = ValueError("presentation")
    cancellation = asyncio.CancelledError("final leaf")
    bound, _ = await prepare(tmp_path, 1)
    store = LeafFinalStore(cancellation)
    coordinator = Coordinator(
        bound, store, attempt, Classifier(), NoQuota(), Clock(), FailedSink(original)
    )

    # When
    with pytest.raises(asyncio.CancelledError) as raised:
        await coordinator.run()

    # Then
    assert raised.value is cancellation
    assert raised.value.__cause__ is original
    assert coordinator._control.reason is not None
    assert coordinator._control.reason.first is original
    assert coordinator._control.reason.recording_failure is cancellation


class DurableSink(Sink):
    """Assert progress never reports facts before their filesystem writes."""

    def __init__(self, output: Path) -> None:
        super().__init__()
        self.output = output

    @override
    def publish(self, snapshot: ProgressSnapshot, /) -> None:
        """Check durable attempt and final records at publication time."""
        if snapshot.counts.attempts_succeeded:
            assert tuple((self.output / "attempts").rglob("attempt-*.json"))
        if snapshot.phase == "final":
            assert (self.output / "run.json").is_file()
        super().publish(snapshot)


async def test_progress_reports_only_after_corresponding_evidence_is_durable(
    tmp_path: Path,
) -> None:
    # Given
    bound, store = await prepare(tmp_path, 1)
    sink = DurableSink(bound.evidence.output_directory)

    # When
    record = await Coordinator(
        bound, store, attempt, Classifier(), NoQuota(), Clock(), sink
    ).run()

    # Then
    assert record.calls[0].state == "complete"
    assert sink.snapshots[-1].counts.attempts_succeeded == 1
    assert sink.snapshots[-1].phase == "final"


class InterruptAttempt:
    """Raise an interrupt while another invocation is active."""

    def __init__(self) -> None:
        self.error = KeyboardInterrupt("leaf interrupt")
        self.sibling_started = asyncio.Event()
        self.sibling_cleaned = asyncio.Event()

    async def __call__(
        self, request: AttemptRequest, stop: DispatchStop, /
    ) -> AttemptResult:
        """Keep the interrupt local until sibling cleanup completes."""
        if request.argv[1] == "0":
            await self.sibling_started.wait()
            raise self.error
        self.sibling_started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            self.sibling_cleaned.set()
            raise
        raise AssertionError("unreachable")


async def test_leaf_interrupt_settles_sibling_before_propagation(
    tmp_path: Path,
) -> None:
    # Given
    bound, store = await prepare(tmp_path, 2, concurrency=2)
    calls = InterruptAttempt()

    # When
    with pytest.raises(KeyboardInterrupt, match="leaf interrupt") as raised:
        await Coordinator(
            bound, store, calls, Classifier(), NoQuota(), Clock(), Sink()
        ).run()

    # Then
    assert raised.value is calls.error
    assert calls.sibling_cleaned.is_set()
    assert (bound.evidence.output_directory / "run.json").is_file()


async def test_exhausted_quota_probe_budget_stops_without_restarting_wait(
    tmp_path: Path,
) -> None:
    # Given
    bound, store = await prepare(
        tmp_path, 1, quota_wait_enabled=True, quota_probe_budget=0
    )
    reader = RecoveryReader()

    # When
    record = await Coordinator(
        bound, store, nonzero_attempt, QuotaClassifier(), reader, Clock(), Sink()
    ).run()

    # Then
    assert record.state == "incomplete"
    assert len(record.waits) == 1
    assert record.waits[0].end == "bound"
    assert not reader.probed.is_set()
    assert len(record.calls[0].attempts) == 1


class StoppingSink(Sink):
    """Signal when the run begins stopping its owned tasks."""

    def __init__(self) -> None:
        super().__init__()
        self.stopping = asyncio.Event()

    @override
    def publish(self, snapshot: ProgressSnapshot, /) -> None:
        """Signal the stop transition after retaining the snapshot."""
        super().publish(snapshot)
        if snapshot.phase == "stopping":
            self.stopping.set()


class FailedInvocation:
    """Raise a retained invocation failure."""

    def __init__(self, failure: ValueError) -> None:
        self.failure = failure

    async def __call__(
        self, request: AttemptRequest, stop: DispatchStop, /
    ) -> AttemptResult:
        """Yield, then fail without a supervisor outcome."""
        await asyncio.sleep(0)
        raise self.failure


async def test_invocation_error_survives_failed_write_during_internal_stop(
    tmp_path: Path,
) -> None:
    # Given
    entered, release = asyncio.Event(), ThreadEvent()
    loop = asyncio.get_running_loop()
    invocation_error = ValueError("invocation")
    write_error = OSError("attempt write")

    def append(prepared: PreparedEvidence, record: AttemptRecord) -> None:
        """Hold and fail the submitted attempt write."""
        loop.call_soon_threadsafe(entered.set)
        assert release.wait(5)
        raise write_error

    store = create_evidence_store(append_attempt=append)
    bound, store = await prepare(tmp_path, 1, store=store)
    sink = StoppingSink()
    task = asyncio.create_task(
        Coordinator(
            bound,
            store,
            FailedInvocation(invocation_error),
            Classifier(),
            NoQuota(),
            Clock(),
            sink,
        ).run()
    )
    await entered.wait()
    await sink.stopping.wait()

    # When
    release.set()
    with pytest.raises(ValueError, match="invocation") as raised:
        await task

    # Then
    assert raised.value is invocation_error
    assert raised.value.__cause__ is write_error
    record = RunRecord.model_validate_json(
        (bound.evidence.output_directory / "run.json").read_bytes()
    )
    assert record.state == "incomplete"
    assert record.calls[0].attempts == ()


class InterruptingStopSink:
    """Raise an ordinary error, then an interrupt during stopping."""

    def __init__(self) -> None:
        self.original = ValueError("first report")
        self.interrupt = KeyboardInterrupt("stop report")
        self.calls = 0

    def publish(self, snapshot: ProgressSnapshot, /) -> None:
        """Fail initially and interrupt the stop report."""
        self.calls += 1
        if self.calls == 1:
            raise self.original
        if self.calls == 2:
            raise self.interrupt


async def test_progress_interrupt_during_stop_preserves_prior_error(
    tmp_path: Path,
) -> None:
    # Given
    bound, store = await prepare(tmp_path, 1)
    sink = InterruptingStopSink()

    # When
    with pytest.raises(KeyboardInterrupt, match="stop report") as raised:
        await Coordinator(
            bound, store, attempt, Classifier(), NoQuota(), Clock(), sink
        ).run()

    # Then
    assert raised.value is sink.interrupt
    assert raised.value.__cause__ is sink.original
    assert (bound.evidence.output_directory / "run.json").is_file()
