# SPDX-License-Identifier: Apache-2.0
"""Composition ordering and cancellation without provider effects."""

import asyncio
from hashlib import sha256
from pathlib import Path
from threading import Event

import pytest

from script.eval.cli import Composition
from script.eval.evidence import EvidenceStore, create_evidence_store
from script.eval.model import (
    DirectoryOption,
    DryRunReport,
    EstimateBasis,
    FrozenInputs,
    FrozenPlan,
    HarnessConfig,
    PlannedCall,
    PreparedEvidence,
    RunRecord,
    SourceSnapshot,
    TokenEstimate,
)
from script.eval.plan import PurePlanBuilder
from script.eval.runner import BoundRun, CliBinding, EffectiveCall
from script.process_supervisor import AttemptRequest


class Harness:
    """Recording collaborators with an actual pure planner."""

    def __init__(self) -> None:
        self.events: list[str] = []
        self.fail: str | None = None
        self.bound: BoundRun | None = None
        self.prepared = PreparedEvidence(Path("/out"), Path("/out/plan"), None)
        self.store = create_evidence_store(create_evidence=self.create)
        self.binding = CliBinding(Path("/codex"), "version", "runner", (), None)
        self.record = RunRecord(
            run_id="run",
            repository_root="/repo",
            head_commit="head",
            state="complete",
            runner_version="runner",
            codex_path="/codex",
            cli_version="version",
            effective_settings=(),
            calls=(),
        )

    def step(self, name: str) -> None:
        self.events.append(name)
        if self.fail == name:
            raise ValueError(name)

    def freeze(self, config: HarnessConfig, /) -> FrozenInputs:
        self.step("freeze")
        content = b"prompt"
        source = SourceSnapshot(
            directory_position=0,
            repository_path="context/a",
            commit_blob_sha="blob",
            content_sha256=sha256(content).hexdigest(),
            content=content,
        )
        return FrozenInputs(Path("/repo"), "head", (source,), None)

    def plan(self, inputs: FrozenInputs, config: HarnessConfig, /) -> FrozenPlan:
        self.step("plan")
        return PurePlanBuilder("run").plan(inputs, config)

    def estimate(
        self, content: bytes, model: str, basis: EstimateBasis, /
    ) -> TokenEstimate:
        self.step("estimate")
        return TokenEstimate(model, 1, "fake", None, None, basis, "exact", None)

    def resolve(self, config: HarnessConfig, /) -> CliBinding:
        self.step("bind")
        return self.binding

    def build(
        self,
        plan: FrozenPlan,
        call: PlannedCall,
        binding: CliBinding,
        evidence: PreparedEvidence,
        config: HarnessConfig,
        /,
    ) -> EffectiveCall:
        self.step("request")
        assert binding is self.binding and evidence is self.prepared
        return EffectiveCall(
            plan.run_id,
            "call",
            call,
            AttemptRequest(("/codex",), Path("/repo"), 1, 1, 0, "devnull"),
        )

    def create(self, output_directory: Path, plan: FrozenPlan, /) -> PreparedEvidence:
        self.step("create")
        assert output_directory == Path("/out")
        return self.prepared

    def evidence(self) -> EvidenceStore:
        self.step("store")
        return self.store

    def coordinator(
        self, bound: BoundRun, evidence: EvidenceStore, config: HarnessConfig, /
    ) -> Harness:
        self.step("coordinator")
        assert evidence is self.store
        self.bound = bound
        return self

    async def run(self) -> RunRecord:
        self.step("run")
        return self.record

    def composition(self) -> Composition:
        return Composition(
            self, self, self, self, self, self.evidence, self.coordinator
        )


def config(*, dry_run: bool) -> HarnessConfig:
    return HarnessConfig(
        ordered_options=(DirectoryOption(position=0, path=Path("context")),),
        models=("model",),
        efforts=("low",),
        concurrency=1,
        output_directory=None if dry_run else Path("/out"),
        dry_run=dry_run,
        timeout_seconds=1.0,
        cleanup_timeout_seconds=1.0,
        grace_seconds=0.0,
        output_limit_bytes=0,
        instructions_file_path=None,
    )


def test_dry_run_stops_after_estimation() -> None:
    # Given
    harness = Harness()

    # When
    result = asyncio.run(harness.composition().execute(config(dry_run=True)))

    # Then
    assert isinstance(result, DryRunReport)
    assert result.scheduled_call_count == 1
    assert harness.events == ["freeze", "plan", "estimate"]


def test_execution_binds_evidence_and_requests_before_coordinator() -> None:
    # Given
    harness = Harness()

    # When
    result = asyncio.run(harness.composition().execute(config(dry_run=False)))

    # Then
    assert result is harness.record
    assert harness.events == [
        "freeze",
        "plan",
        "bind",
        "store",
        "create",
        "request",
        "coordinator",
        "run",
    ]
    assert harness.bound is not None
    assert harness.bound.binding is harness.binding
    assert harness.bound.evidence is harness.prepared
    assert len(harness.bound.calls) == 1
    assert harness.bound.calls[0].planned_call is harness.bound.plan.calls[0]


@pytest.mark.parametrize(
    ("failure", "events"),
    [
        ("freeze", ["freeze"]),
        ("plan", ["freeze", "plan"]),
        ("bind", ["freeze", "plan", "bind"]),
        ("create", ["freeze", "plan", "bind", "store", "create"]),
        ("request", ["freeze", "plan", "bind", "store", "create", "request"]),
    ],
    ids=["freeze", "plan", "binding", "evidence", "request"],
)
def test_failure_prevents_later_steps(failure: str, events: list[str]) -> None:
    # Given
    harness = Harness()
    harness.fail = failure

    # When
    with pytest.raises(ValueError, match=failure):
        asyncio.run(harness.composition().execute(config(dry_run=False)))

    # Then
    assert harness.events == events


def test_cancellation_retains_blocking_preparation_and_prevents_dispatch() -> None:
    # Given
    started, release = Event(), Event()
    harness = Harness()

    class BlockingRepository:
        def freeze(self, configuration: HarnessConfig, /) -> FrozenInputs:
            started.set()
            release.wait()
            return harness.freeze(configuration)

    composition = Composition(
        BlockingRepository(),
        harness,
        harness,
        harness,
        harness,
        harness.evidence,
        harness.coordinator,
    )

    async def exercise() -> None:
        task = asyncio.create_task(composition.execute(config(dry_run=False)))
        await asyncio.to_thread(started.wait)
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task

    # When
    asyncio.run(exercise())

    # Then
    assert harness.events == ["freeze"]
