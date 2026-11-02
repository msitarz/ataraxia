# SPDX-License-Identifier: Apache-2.0
"""Coordinator execution through the real local process supervisor."""

import asyncio
from dataclasses import replace
from pathlib import Path
import sys

import pytest

from script.eval.evidence import create_evidence_store
from script.eval.model import AttemptRecord, PreparedEvidence, RunRecord
from script.eval.runner.coordinator import Coordinator
from script.eval.runner.ports import BoundRun
from script.process_supervisor import (
    AttemptRequest,
    AttemptResult,
    DispatchStop,
    call_supervisor,
    run_attempt,
)
from test.script.unit.eval.test_coordinator import Sink, prepare
from test.script.unit.eval.test_coordinator_calls import Classifier, Clock, NoQuota


async def supervised(request: AttemptRequest, stop: DispatchStop, /) -> AttemptResult:
    """Use the production supervisor around a controlled local process."""
    return await call_supervisor(request, run_attempt, stop)


async def test_coordinator_retains_supervised_process_output(tmp_path: Path) -> None:
    # Given
    bound, store = await prepare(tmp_path, 1)
    effective = bound.calls[0]
    request = replace(
        effective.request,
        argv=("/usr/bin/env", "-i", sys.executable, "-c", "print('controlled')"),
        cwd=tmp_path,
    )
    bound = replace(bound, calls=(replace(effective, request=request),))

    # When
    record = await Coordinator(
        bound, store, supervised, Classifier(), NoQuota(), Clock(), Sink()
    ).run()

    # Then
    assert record.state == "complete"
    assert record.calls[0].attempts[0].exit_status == 0
    artifact = record.calls[0].attempts[0].stdout_artifact
    assert artifact is not None
    assert Path(artifact).read_bytes() == b"controlled\n"


def process_calls(
    bound: BoundRun, directory: Path, program: str, limit: int
) -> BoundRun:
    """Bind each planned call to the same controlled local Python process."""
    calls = tuple(
        replace(
            item,
            request=replace(
                item.request,
                argv=(sys.executable, "-c", program, str(index)),
                cwd=directory,
                output_limit_bytes=limit,
            ),
        )
        for index, item in enumerate(bound.calls)
    )
    return replace(bound, calls=calls)


class HeldSupervisedAttempts:
    """Hold the supervisor boundary after real child cleanup has settled."""

    def __init__(self) -> None:
        self.started: list[str] = []
        self.settled: list[str] = []
        self.two_settled = asyncio.Event()
        self.release = asyncio.Event()

    async def __call__(
        self, request: AttemptRequest, stop: DispatchStop, /
    ) -> AttemptResult:
        """Retain the completed supervisor call until the test releases it."""
        self.started.append(request.argv[-1])
        outcome = await supervised(request, stop)
        assert outcome.observation.cleanup.dispatch_permitted
        self.settled.append(request.argv[-1])
        if len(self.settled) == 2:
            self.two_settled.set()
        await self.release.wait()
        return outcome


async def test_real_supervisor_slot_is_held_until_settlement(tmp_path: Path) -> None:
    # Given
    bound, store = await prepare(tmp_path, 3, concurrency=2)
    bound = process_calls(bound, tmp_path, "print('done')", 0)
    held = HeldSupervisedAttempts()
    # When
    task = asyncio.create_task(
        Coordinator(bound, store, held, Classifier(), NoQuota(), Clock(), Sink()).run()
    )
    try:
        await asyncio.wait_for(held.two_settled.wait(), 10)

        # Then
        assert set(held.started) == {"0", "1"}
        held.release.set()
        record = await asyncio.wait_for(task, 10)
    finally:
        held.release.set()
        if not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
    assert held.started == ["0", "1", "2"]
    assert record.state == "complete"


@pytest.mark.parametrize(
    ("limit", "expected_bytes", "outcome", "run_state", "second_state"),
    [
        (0, b"abcdefghijklmnop", "completed", "complete", "complete"),
        (8, b"abcdefgh", "output_limit_exceeded", "incomplete", "not_started"),
    ],
    ids=["unbounded", "overflow"],
)
async def test_real_supervisor_output_cap_stops_or_captures(
    tmp_path: Path,
    limit: int,
    expected_bytes: bytes,
    outcome: str,
    run_state: str,
    second_state: str,
) -> None:
    # Given
    bound, store = await prepare(tmp_path, 2, concurrency=1, retry_limit=1)
    bound = process_calls(
        bound, tmp_path, "import sys; sys.stdout.write('abcdefghijklmnop')", limit
    )

    # When
    record = await asyncio.wait_for(
        Coordinator(
            bound, store, supervised, Classifier(), NoQuota(), Clock(), Sink()
        ).run(),
        10,
    )

    # Then
    first = record.calls[0].attempts[0]
    assert first.stdout_artifact is not None
    assert Path(first.stdout_artifact).read_bytes() == expected_bytes
    assert len(record.calls[0].attempts) == 1
    assert first.outcome_kind == outcome
    assert record.state == run_state
    assert record.calls[1].state == second_state


class FailingSupervisedAttempt:
    """Raise after a real child settles and record its supervisor stop hook."""

    def __init__(self) -> None:
        self.stopped: list[BaseException] = []
        self.failure = RuntimeError("controlled supervisor failure")

    async def __call__(
        self, request: AttemptRequest, stop: DispatchStop, /
    ) -> AttemptResult:
        async def completed_then_fail(request: AttemptRequest, /) -> AttemptResult:
            result = await run_attempt(request)
            assert result.observation.cleanup.dispatch_permitted
            raise self.failure

        def observe_stop(reason: BaseException | AttemptResult, /) -> None:
            """Observe and forward the supervisor's stop request."""
            if isinstance(reason, BaseException):
                self.stopped.append(reason)
            stop(reason)

        return await call_supervisor(request, completed_then_fail, observe_stop)


async def test_supervisor_stop_hook_precedes_failed_recording(tmp_path: Path) -> None:
    # Given
    attempt = FailingSupervisedAttempt()

    def fail_write(prepared: PreparedEvidence, record: AttemptRecord) -> None:
        """Verify the stop hook has run before simulating a failed write."""
        assert attempt.stopped == [attempt.failure]
        raise OSError("controlled evidence failure")

    store = create_evidence_store(append_attempt=fail_write)
    bound, store = await prepare(tmp_path, 2, store=store, concurrency=1)
    bound = process_calls(bound, tmp_path, "print('done')", 0)

    # When
    with pytest.raises(RuntimeError, match="controlled supervisor failure") as raised:
        await asyncio.wait_for(
            Coordinator(
                bound,
                store,
                attempt,
                Classifier(),
                NoQuota(),
                Clock(),
                Sink(),
            ).run(),
            10,
        )
    # Then
    assert isinstance(raised.value.__cause__, OSError)
    record = RunRecord.model_validate_json(
        (bound.evidence.output_directory / "run.json").read_bytes()
    )
    assert attempt.stopped == [attempt.failure]
    assert record.state == "incomplete"
    assert [call.state for call in record.calls] == ["failed", "not_started"]
    assert not record.calls[0].attempts
