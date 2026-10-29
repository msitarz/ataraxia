# SPDX-License-Identifier: Apache-2.0
"""Exit status reflects settled evidence while preserving cancellation."""

import asyncio
from collections.abc import Callable, Coroutine
from pathlib import Path

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
from script.eval.standalone import run_owned
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
        (ordinary_failure, prepared, fail_finalize, 1),
        (create_then_finalize, fail_create, fail_finalize, 1),
        (create_then_finalize, prepared, fail_finalize, 3),
        (cancelled, prepared, fail_finalize, 130),
    ],
    ids=["ordinary-failure", "failed-create", "failed-finalize", "cancellation"],
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
    code = await run_owned(frozen_plan().configuration, status, operation)

    # Then
    assert code == expected


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
