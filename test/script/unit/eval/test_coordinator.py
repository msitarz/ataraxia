# SPDX-License-Identifier: Apache-2.0
"""Exercise the coordinator's thin composition, not final metadata projection."""

import asyncio
from pathlib import Path
from typing import override

import pytest

from script.eval.model import FrozenPlan, PreparedEvidence, RunRecord, SourceSnapshot
from script.eval.runner.coordinator import Coordinator
from script.eval.runner.coordinator.call_states import (
    CallHistory,
    CallState,
    Finished,
    Queued,
    Stopped,
)
from script.eval.runner.coordinator.coordinator import _final_status, _raise_outcome
from script.eval.runner.coordinator.quota_states import Draining, QuotaHistory
from script.eval.runner.coordinator.settlement import SettledFailure, SettledValue
from script.eval.runner.ports import (
    BoundRun,
    CliBinding,
    ProgressFinalStatus,
    ProgressSnapshot,
)
from script.process_supervisor import (
    AttemptObservation,
    AttemptRequest,
    AttemptResult,
    CapturedOutput,
    CleanupEvidence,
    Completed,
    DispatchStop,
    SignalAttempt,
)
from test.script.unit.eval.test_coordinator_calls import (
    Classifier,
    Clock,
    NoQuota,
    Store,
)
from test.script.unit.eval.test_coordinator_states import call, config, waiting


class FinalStore(Store):
    """Record finalization alongside its durable attempt."""

    def __init__(self) -> None:
        super().__init__()
        self.final: RunRecord | None = None

    @override
    async def finalize(self, record: RunRecord, /) -> None:
        """Retain the submitted record."""
        self.final = record


class Sink:
    """Collect snapshots in their publication order."""

    def __init__(self, store: FinalStore | None = None) -> None:
        self.snapshots: list[ProgressSnapshot] = []
        self.store = store

    def publish(self, snapshot: ProgressSnapshot, /) -> None:
        """Retain one projection."""
        if snapshot.phase == "final" and self.store is not None:
            assert self.store.final is not None
        self.snapshots.append(snapshot)


def bound_run() -> BoundRun:
    """Provide one typed frozen call and its already-prepared evidence."""
    effective = call()
    plan = FrozenPlan(
        run_id="run",
        configuration=config(),
        repository_root=Path("/tmp"),
        head_commit="head",
        snapshots=(
            SourceSnapshot(
                directory_position=0,
                repository_path="a",
                commit_blob_sha="b",
                content_sha256="c",
                content=b"context",
            ),
        ),
        boundary_bytes=(),
        instructions_file=None,
        calls=(effective.planned_call,),
    )
    return BoundRun(
        plan,
        CliBinding(Path("/tmp/codex"), "1", "runner", (("setting", "value"),), None),
        PreparedEvidence(Path("/tmp/out"), Path("/tmp/out/plan"), None),
        (effective,),
    )


class Projection:
    """Capture composition inputs; this does not implement call metadata."""

    def __init__(self) -> None:
        self.states: tuple[CallState, ...] = ()
        self.bound: BoundRun | None = None

    def __call__(
        self, bound: BoundRun, states: tuple[CallState, ...], history: QuotaHistory
    ) -> RunRecord:
        """Return a deliberately minimal test record after capturing inputs."""
        self.bound = bound
        self.states = states
        assert history == QuotaHistory((), ())
        return RunRecord(
            run_id=bound.plan.run_id,
            repository_root=str(bound.plan.repository_root),
            head_commit=bound.plan.head_commit,
            state="complete",
            runner_version=bound.binding.runner_version,
            codex_path=str(bound.binding.executable_path),
            cli_version=bound.binding.cli_version,
            effective_settings=bound.binding.effective_settings,
            calls=(),
        )


async def test_one_call_settles_before_projection_and_final_progress() -> None:
    # Given
    bound = bound_run()
    store = FinalStore()
    sink, projection = Sink(store), Projection()
    coordinator = Coordinator(
        bound,
        store,
        _attempt,
        Classifier(),
        NoQuota(),
        Clock(),
        sink,
        _projection=projection,
    )
    store.slots = coordinator._slots

    # When
    record = await coordinator.run()

    # Then
    assert len(store.seen) == 1
    assert isinstance(projection.states[0], Finished)
    assert projection.bound is bound
    assert record.effective_settings == (("setting", "value"),)
    assert store.final == record
    assert [item.phase for item in sink.snapshots] == ["running", "final"]
    assert sink.snapshots[-1].counts.calls_succeeded == 1


async def test_missing_projection_refuses_dispatch() -> None:
    # Given
    store = FinalStore()
    coordinator = Coordinator(
        bound_run(), store, _attempt, Classifier(), NoQuota(), Clock(), Sink()
    )

    # When / Then
    with pytest.raises(NotImplementedError, match="projection"):
        await coordinator.run()
    assert store.seen == []
    assert store.final is None


async def _attempt(
    request: AttemptRequest, stop_dispatch: DispatchStop, /
) -> AttemptResult:
    """Return a safe process result through the existing typed fake."""
    await asyncio.sleep(0)
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


class BlockingFinalStore(FinalStore):
    """Hold the final write until the test releases it."""

    def __init__(self) -> None:
        super().__init__()
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    @override
    async def finalize(self, record: RunRecord, /) -> None:
        """Expose a submitted final write to cancellation."""
        self.started.set()
        await self.release.wait()
        self.final = record


async def test_repeated_cancellation_retains_submitted_final_write() -> None:
    # Given
    store, projection = BlockingFinalStore(), Projection()
    coordinator = Coordinator(
        bound_run(),
        store,
        _attempt,
        Classifier(),
        NoQuota(),
        Clock(),
        Sink(),
        _projection=projection,
    )
    store.slots = coordinator._slots
    task = asyncio.create_task(coordinator.run())
    await store.started.wait()

    # When
    task.cancel("first")
    await asyncio.sleep(0)
    task.cancel("second")
    await asyncio.sleep(0)
    assert not task.done()
    store.release.set()

    # Then
    with pytest.raises(asyncio.CancelledError, match="first"):
        await task
    assert store.final is not None


async def test_empty_run_finalizes_without_attempt() -> None:
    # Given
    original = bound_run()
    bound = BoundRun(
        original.plan.model_copy(update={"calls": ()}),
        original.binding,
        original.evidence,
        (),
    )
    store, projection = FinalStore(), Projection()
    coordinator = Coordinator(
        bound,
        store,
        _attempt,
        Classifier(),
        NoQuota(),
        Clock(),
        Sink(),
        _projection=projection,
    )

    # When
    record = await coordinator.run()

    # Then
    assert projection.states == ()
    assert store.seen == []
    assert store.final == record


async def test_supervisor_stop_is_visible_to_projection_after_attempt_settles() -> None:
    # Given
    store, projection, sink = FinalStore(), Projection(), Sink()
    coordinator = Coordinator(
        bound_run(),
        store,
        _stop_attempt,
        Classifier(),
        NoQuota(),
        Clock(),
        sink,
        _projection=projection,
    )
    store.slots = coordinator._slots

    # When
    await coordinator.run()

    # Then
    assert len(store.seen) == 1
    assert isinstance(projection.states[0], Stopped)
    assert sink.snapshots[-1].final_status == "failure"


async def _stop_attempt(
    request: AttemptRequest, stop_dispatch: DispatchStop, /
) -> AttemptResult:
    """Latch stop through the actual supervisor hook before returning."""
    result = await _attempt(request, stop_dispatch)
    stop_dispatch(result)
    return result


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        (Finished(CallHistory(call(), (), ()), "success"), "success"),
        (Finished(CallHistory(call(), (), ()), "failure"), "failure"),
        (Stopped(CallHistory(call(), (), ()), "cancelled"), "cancelled"),
        (Queued(CallHistory(call(), (), ())), "failure"),
    ],
    ids=["success", "failure", "cancelled", "unfinished"],
)
def test_final_status_distinguishes_call_outcomes(
    state: CallState, expected: ProgressFinalStatus
) -> None:
    # Given
    record = Projection()(bound_run(), (), QuotaHistory((), ()))

    # When
    status = _final_status(record, (state,))

    # Then
    assert status == expected


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
            "local",
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


class FailedFinalStore(FinalStore):
    """Raise the exact configured finalization failure."""

    def __init__(self, error: BaseException) -> None:
        super().__init__()
        self.error = error

    @override
    async def finalize(self, record: RunRecord, /) -> None:
        """Fail the submitted write without publishing a record."""
        raise self.error


@pytest.mark.parametrize(
    "error",
    [OSError("write"), asyncio.CancelledError("leaf")],
    ids=["write", "leaf-cancel"],
)
async def test_failed_finalization_latches_failure_without_final_report(
    error: BaseException,
) -> None:
    # Given
    store, sink = FailedFinalStore(error), Sink()
    coordinator = Coordinator(
        bound_run(),
        store,
        _attempt,
        Classifier(),
        NoQuota(),
        Clock(),
        sink,
        _projection=Projection(),
    )
    store.slots = coordinator._slots

    # When
    with pytest.raises(type(error)) as raised:
        await coordinator.run()

    # Then
    assert raised.value is error
    assert coordinator._control.reason is not None
    assert coordinator._control.reason.recording_failure is error
    assert [snapshot.phase for snapshot in sink.snapshots] == ["running"]


class BlockingFailedFinalStore(BlockingFinalStore):
    """Fail the final write after the test releases it."""

    def __init__(self, error: BaseException) -> None:
        super().__init__()
        self.error = error

    @override
    async def finalize(self, record: RunRecord, /) -> None:
        """Retain the submitted write through cancellation, then fail."""
        self.started.set()
        await self.release.wait()
        raise self.error


async def test_final_write_failure_during_cancellation_preserves_both() -> None:
    # Given
    failure = OSError("write")
    store, sink = BlockingFailedFinalStore(failure), Sink()
    coordinator = Coordinator(
        bound_run(),
        store,
        _attempt,
        Classifier(),
        NoQuota(),
        Clock(),
        sink,
        _projection=Projection(),
    )
    store.slots = coordinator._slots
    task = asyncio.create_task(coordinator.run())
    await store.started.wait()

    # When
    task.cancel("owner")
    await asyncio.sleep(0)
    store.release.set()
    with pytest.raises(asyncio.CancelledError, match="owner") as raised:
        await task

    # Then
    assert raised.value.__cause__ is failure
    assert coordinator._control.reason is not None
    assert coordinator._control.reason.recording_failure is failure
    assert coordinator._control.reason.cancellation is raised.value
    assert [snapshot.phase for snapshot in sink.snapshots] == ["running"]


def test_quota_owner_construction_retains_drained_context_without_effects() -> None:
    # Given
    store = FinalStore()
    coordinator = Coordinator(
        bound_run(),
        store,
        _attempt,
        Classifier(),
        NoQuota(),
        Clock(),
        Sink(),
        _projection=Projection(),
    )
    context = waiting().context

    # When
    owner = coordinator._quota_owner(context)

    # Then
    assert owner.state == Draining(context)
    assert owner.history == QuotaHistory((), ())
    assert owner._control is coordinator._control
    assert owner._evidence is store
    assert store.events == []


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


class FailingSink(Sink):
    """Fail the initial report with the supplied original exception."""

    def __init__(self, error: BaseException) -> None:
        super().__init__()
        self.error = error

    @override
    def publish(self, snapshot: ProgressSnapshot, /) -> None:
        """Fail before the attempt starts."""
        raise self.error


async def test_leaf_cancellation_of_final_write_preserves_prior_error() -> None:
    # Given
    original = ValueError("report")
    cancellation = asyncio.CancelledError("leaf")
    store, sink = FailedFinalStore(cancellation), FailingSink(original)
    coordinator = Coordinator(
        bound_run(),
        store,
        _attempt,
        Classifier(),
        NoQuota(),
        Clock(),
        sink,
        _projection=Projection(),
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
    assert coordinator._control.reason.cancellation is cancellation
