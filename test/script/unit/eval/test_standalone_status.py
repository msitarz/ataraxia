# SPDX-License-Identifier: Apache-2.0
"""Exit status reflects settled evidence while preserving cancellation."""

import asyncio
from collections.abc import Callable, Coroutine
from contextlib import AbstractContextManager
from pathlib import Path
import signal
from types import TracebackType

import pytest

from script.eval.evidence import CreateEvidence, FinalizeEvidence, create_evidence_store
from script.eval.evidence_status import EvidenceStatus
from script.eval.model import (
    DryRunReport,
    FrozenPlan,
    HarnessConfig,
    PreparedEvidence,
    RunRecord,
)
from script.eval.standalone import ProgressRun, run_owned
from test.script.integration.eval.support import frozen_plan


def record() -> RunRecord:
    return RunRecord(
        run_id="run",
        repository_root="/repo",
        head_commit="head",
        state="complete",
        runner_version="runner",
        codex_path="/codex",
        cli_version="1",
        effective_settings=(),
        calls=(),
    )


def prepared(output: Path, plan: FrozenPlan) -> PreparedEvidence:
    return PreparedEvidence(output, output / "plan", None)


def fail_create(output: Path, plan: FrozenPlan) -> PreparedEvidence:
    raise OSError("create failed")


def fail_finalize(preparation: PreparedEvidence, result: RunRecord) -> None:
    raise OSError("finalize failed")


def finalize_ok(preparation: PreparedEvidence, result: RunRecord) -> None:
    """Accept one final record without effects."""


async def create_then_finalize(
    config: HarnessConfig, status: EvidenceStatus
) -> DryRunReport | RunRecord:
    plan = frozen_plan()
    await status.create(Path("/output"), plan)
    result = record()
    await status.finalize(result)
    return result


async def ordinary_failure(
    config: HarnessConfig, status: EvidenceStatus
) -> DryRunReport | RunRecord:
    await asyncio.sleep(0)
    raise ValueError("binding failed")


async def cancelled(
    config: HarnessConfig, status: EvidenceStatus
) -> DryRunReport | RunRecord:
    await status.create(Path("/output"), frozen_plan())
    raise asyncio.CancelledError()


@pytest.mark.parametrize(
    ("operation", "create", "finalize", "expected"),
    [
        (create_then_finalize, prepared, finalize_ok, 0),
        (ordinary_failure, prepared, fail_finalize, 1),
        (create_then_finalize, fail_create, fail_finalize, 3),
        (create_then_finalize, prepared, fail_finalize, 3),
        (cancelled, prepared, fail_finalize, 130),
    ],
    ids=[
        "success",
        "ordinary-failure",
        "failed-create",
        "failed-finalize",
        "cancellation",
    ],
)
async def test_exit_status_distinguishes_failure_evidence_and_cancellation(
    operation: Callable[
        [HarnessConfig, EvidenceStatus],
        Coroutine[object, object, DryRunReport | RunRecord],
    ],
    create: CreateEvidence,
    finalize: FinalizeEvidence,
    expected: int,
) -> None:
    # Given
    status = EvidenceStatus(
        lambda: create_evidence_store(
            create_evidence=create, finalize_evidence=finalize
        )
    )

    # When
    before = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
    code = await run_owned(frozen_plan().configuration, status, operation)

    # Then
    assert code == expected
    assert {sig: signal.getsignal(sig) for sig in before} == before


async def test_evidence_failure_preserves_original_exception_and_status() -> None:
    # Given
    error = OSError("write failed")

    def finalize_failure(preparation: PreparedEvidence, result: RunRecord) -> None:
        raise error

    status = EvidenceStatus(
        lambda: create_evidence_store(
            create_evidence=prepared, finalize_evidence=finalize_failure
        )
    )
    await status.create(Path("/output"), frozen_plan())

    # When
    with pytest.raises(OSError) as caught:
        await status.finalize(record())

    # Then
    assert caught.value is error
    assert status.started and not status.finalized


async def test_signal_setup_failure_does_not_start_operation() -> None:
    # Given
    status = EvidenceStatus(lambda: create_evidence_store(create_evidence=prepared))
    invoked = False

    async def operation(
        config: HarnessConfig, store: EvidenceStatus
    ) -> DryRunReport | RunRecord:
        nonlocal invoked
        invoked = True
        await asyncio.sleep(0)
        return record()

    class FailedSignals(AbstractContextManager[None]):
        def __enter__(self) -> None:
            raise OSError("cannot install signal handlers")

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            traceback: TracebackType | None,
        ) -> None:
            pass

    def fail_install(
        loop: asyncio.AbstractEventLoop, owner: asyncio.Task[object]
    ) -> FailedSignals:
        return FailedSignals()

    # When
    with pytest.raises(OSError, match="cannot install"):
        await run_owned(
            frozen_plan().configuration, status, operation, signals=fail_install
        )

    # Then
    assert not invoked
    assert not status.started


class BrokenProgress:
    """A progress resource whose close fails."""

    def close(self) -> None:
        raise OSError("close failed")


async def test_progress_close_failure_does_not_change_success() -> None:
    # Given
    result = record()

    class Coordinator:
        async def run(self) -> RunRecord:
            await asyncio.sleep(0)
            return result

    run = ProgressRun(Coordinator(), BrokenProgress())

    # When
    outcome = await run.run()

    # Then
    assert outcome is result


async def test_progress_close_failure_preserves_original_run_failure() -> None:
    # Given
    error = ValueError("run failed")

    class Coordinator:
        async def run(self) -> RunRecord:
            await asyncio.sleep(0)
            raise error

    run = ProgressRun(Coordinator(), BrokenProgress())

    # When
    with pytest.raises(ValueError) as caught:
        await run.run()

    # Then
    assert caught.value is error
