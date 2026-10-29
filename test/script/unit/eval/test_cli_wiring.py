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
    InstructionsSnapshot,
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
        self.frozen: FrozenInputs | None = None
        self.plan_value: FrozenPlan | None = None
        self.configs: list[HarnessConfig] = []
        self.requests: list[
            tuple[FrozenPlan, PlannedCall, CliBinding, PreparedEvidence, HarnessConfig]
        ] = []
        self.estimates: list[tuple[bytes, str, EstimateBasis]] = []
        self.prepared = PreparedEvidence(
            Path("/out"), Path("/out/plan"), Path("/out/instructions")
        )
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
        self.configs.append(config)
        instruction = b"instructions"
        snapshot = InstructionsSnapshot(
            repository_path="instructions",
            commit_blob_sha="blob",
            content_sha256=sha256(instruction).hexdigest(),
            content=instruction,
        )
        self.frozen = FrozenInputs(Path("/repo"), "head", (source,), snapshot)
        return self.frozen

    def plan(self, inputs: FrozenInputs, config: HarnessConfig, /) -> FrozenPlan:
        self.step("plan")
        assert inputs is self.frozen
        self.configs.append(config)
        self.plan_value = PurePlanBuilder("run").plan(inputs, config)
        return self.plan_value

    def estimate(
        self, content: bytes, model: str, basis: EstimateBasis, /
    ) -> TokenEstimate:
        self.step("estimate")
        self.estimates.append((content, model, basis))
        return TokenEstimate(model, 1, "fake", None, None, basis, "exact", None)

    def resolve(self, config: HarnessConfig, /) -> CliBinding:
        self.step("bind")
        self.configs.append(config)
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
        self.requests.append((plan, call, binding, evidence, config))
        return EffectiveCall(
            plan.run_id,
            "call",
            call,
            AttemptRequest(("/codex",), Path("/repo"), 1, 1, 0, "devnull"),
        )

    def create(self, output_directory: Path, plan: FrozenPlan, /) -> PreparedEvidence:
        self.step("create")
        assert output_directory == Path("/out")
        assert plan is self.plan_value
        return self.prepared

    def evidence(self) -> EvidenceStore:
        self.step("store")
        return self.store

    def coordinator(self, bound: BoundRun, evidence: EvidenceStore, /) -> Harness:
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
        models=("model-a", "model-b"),
        efforts=("low",),
        concurrency=1,
        output_directory=None if dry_run else Path("/out"),
        dry_run=dry_run,
        timeout_seconds=1.0,
        cleanup_timeout_seconds=1.0,
        grace_seconds=0.0,
        output_limit_bytes=0,
        instructions_file_path=Path("instructions"),
    )


async def test_dry_run_stops_after_estimation() -> None:
    # Given
    harness = Harness()

    # When
    configuration = config(dry_run=True)
    result = await harness.composition().execute(configuration)

    # Then
    assert isinstance(result, DryRunReport)
    assert result.plan is harness.plan_value
    assert result.scheduled_call_count == 2
    assert harness.configs == [configuration, configuration]
    assert harness.estimates == [
        (b"prompt", "model-a", "supplied_context"),
        (b"instructions", "model-a", "instructions_file"),
        (b"prompt", "model-b", "supplied_context"),
        (b"instructions", "model-b", "instructions_file"),
    ]
    assert harness.events == [
        "freeze",
        "plan",
        "estimate",
        "estimate",
        "estimate",
        "estimate",
    ]


async def test_execution_binds_evidence_and_requests_before_coordinator() -> None:
    # Given
    harness = Harness()

    # When
    configuration = config(dry_run=False)
    result = await harness.composition().execute(configuration)

    # Then
    assert result is harness.record
    assert harness.events == [
        "freeze",
        "plan",
        "bind",
        "store",
        "create",
        "request",
        "request",
        "coordinator",
        "run",
    ]
    assert harness.bound is not None
    assert harness.bound.binding is harness.binding
    assert harness.bound.evidence is harness.prepared
    assert harness.bound.plan is harness.plan_value
    assert harness.configs == [configuration, configuration, configuration]
    assert [call.planned_call for call in harness.bound.calls] == list(
        harness.bound.plan.calls
    )
    assert [call.planned_call.model for call in harness.bound.calls] == [
        "model-a",
        "model-b",
    ]
    assert harness.requests == [
        (harness.bound.plan, call, harness.binding, harness.prepared, configuration)
        for call in harness.bound.plan.calls
    ]
    assert all(
        plan is harness.bound.plan
        and binding is harness.binding
        and prepared is harness.prepared
        and supplied is configuration
        for plan, _, binding, prepared, supplied in harness.requests
    )
    assert harness.prepared.model_instructions_file == Path("/out/instructions")


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
async def test_failure_prevents_later_steps(failure: str, events: list[str]) -> None:
    # Given
    harness = Harness()
    harness.fail = failure

    # When
    with pytest.raises(ValueError, match=failure):
        await harness.composition().execute(config(dry_run=False))

    # Then
    assert harness.events == events


async def test_cancellation_retains_failed_preparation_and_prevents_dispatch() -> None:
    # Given
    started, release = Event(), Event()
    harness = Harness()
    failure = ValueError("worker failed")

    class BlockingRepository:
        def freeze(self, configuration: HarnessConfig, /) -> FrozenInputs:
            started.set()
            if not release.wait(timeout=5):
                raise TimeoutError("test did not release worker")
            raise failure

    composition = Composition(
        BlockingRepository(),
        harness,
        harness,
        harness,
        harness,
        harness.evidence,
        harness.coordinator,
    )
    task = asyncio.create_task(composition.execute(config(dry_run=False)))

    # When
    try:
        assert await asyncio.to_thread(started.wait, 5)
        task.cancel("first")
        await asyncio.sleep(0)
        task.cancel("second")
        await asyncio.sleep(0)
        assert not task.done()
        release.set()
        with pytest.raises(asyncio.CancelledError) as caught:
            await asyncio.wait_for(task, timeout=5)
    finally:
        release.set()

    # Then
    assert caught.value.args == ("first",)
    assert caught.value.__cause__ is failure
    assert harness.events == []
