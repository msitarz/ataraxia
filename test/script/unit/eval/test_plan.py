# SPDX-License-Identifier: Apache-2.0
"""Runtime guarantees for pure plan orchestration."""

from hashlib import sha256
from pathlib import Path

import pytest

from script.eval.model import (
    DirectoryOption,
    FrozenInputs,
    HarnessConfig,
    InstructionsSnapshot,
    PlannedCall,
    SourceSnapshot,
)
from script.eval.plan import (
    CallScheduler,
    ComposedContexts,
    ContextComposer,
    GroupedInputs,
    InputGrouper,
    PurePlanBuilder,
)


def _configuration(*, instructions_path: Path | None = None) -> HarnessConfig:
    return HarnessConfig(
        ordered_options=(DirectoryOption(position=0, path=Path("context")),),
        models=("model-a",),
        efforts=("low",),
        concurrency=1,
        output_directory=None,
        dry_run=True,
        timeout_seconds=1.0,
        cleanup_timeout_seconds=1.0,
        grace_seconds=0.0,
        output_limit_bytes=0,
        instructions_file_path=instructions_path,
    )


def _inputs() -> FrozenInputs:
    content = b"source"
    source = SourceSnapshot(
        directory_position=0,
        repository_path="context/source.txt",
        commit_blob_sha="blob-sha",
        content_sha256=sha256(content).hexdigest(),
        content=content,
    )
    instruction_content = b"instruction bytes\x00"
    instructions = InstructionsSnapshot(
        repository_path="context/instructions.txt",
        commit_blob_sha="instructions-blob",
        content_sha256=sha256(instruction_content).hexdigest(),
        content=instruction_content,
    )
    return FrozenInputs(Path("/repo"), "commit-sha", (source,), instructions)


class _RecordingGrouper(InputGrouper):
    def __init__(self, events: list[str], result: GroupedInputs) -> None:
        self.events = events
        self.result = result
        self.received: tuple[FrozenInputs, HarnessConfig] | None = None

    def group(self, inputs: FrozenInputs, config: HarnessConfig, /) -> GroupedInputs:
        self.events.append("group")
        self.received = (inputs, config)
        return self.result


class _RecordingComposer(ContextComposer):
    def __init__(self, events: list[str], result: ComposedContexts) -> None:
        self.events = events
        self.result = result
        self.received: tuple[FrozenInputs, GroupedInputs, HarnessConfig] | None = None

    def compose(
        self,
        inputs: FrozenInputs,
        grouped: GroupedInputs,
        config: HarnessConfig,
        /,
    ) -> ComposedContexts:
        self.events.append("compose")
        self.received = (inputs, grouped, config)
        return self.result


class _RecordingScheduler(CallScheduler):
    def __init__(self, events: list[str], result: tuple[PlannedCall, ...]) -> None:
        self.events = events
        self.result = result
        self.received: tuple[ComposedContexts, HarnessConfig] | None = None

    def schedule(
        self, composed: ComposedContexts, config: HarnessConfig, /
    ) -> tuple[PlannedCall, ...]:
        self.events.append("schedule")
        self.received = (composed, config)
        return self.result


def test_plan_wires_pure_steps_in_order_and_preserves_frozen_values() -> None:
    # Given
    inputs = _inputs()
    config = _configuration(instructions_path=Path("context/instructions.txt"))
    events: list[str] = []
    grouped = GroupedInputs(snapshots=((0, (0,)),))
    composed = ComposedContexts(boundary_bytes=(), prompts=(((0,), b"source"),))
    call = PlannedCall(
        position=0,
        context_indices=(0,),
        model="model-a",
        effort="low",
        prompt_sha256=sha256(b"source").hexdigest(),
        prompt=b"source",
    )
    grouper = _RecordingGrouper(events, grouped)
    composer = _RecordingComposer(events, composed)
    scheduler = _RecordingScheduler(events, (call,))
    builder = PurePlanBuilder(
        "caller-run-id",
        grouper=grouper,
        composer=composer,
        scheduler=scheduler,
    )

    # When
    plan = builder.plan(inputs, config)

    # Then
    assert events == ["group", "compose", "schedule"]
    assert grouper.received == (inputs, config)
    assert composer.received == (inputs, grouped, config)
    assert composer.received is not None and composer.received[0] is inputs
    assert composer.received[0].sources[0].content == b"source"
    assert composer.received[0].instructions_file is inputs.instructions_file
    assert composer.received[0].instructions_file is not None
    assert composer.received[0].instructions_file.content == b"instruction bytes\x00"
    assert scheduler.received == (composed, config)
    assert plan.run_id == "caller-run-id"
    assert plan.configuration is config
    assert plan.instructions_file is inputs.instructions_file
    assert (
        plan.repository_root,
        plan.head_commit,
        plan.snapshots,
        plan.boundary_bytes,
        plan.calls,
    ) == (
        inputs.repository_root,
        inputs.head_commit,
        inputs.sources,
        composed.boundary_bytes,
        (call,),
    )


def test_plan_propagates_leaf_failure_without_running_later_steps() -> None:
    # Given
    events: list[str] = []

    class FailingComposer(ContextComposer):
        def compose(
            self,
            inputs: FrozenInputs,
            grouped: GroupedInputs,
            config: HarnessConfig,
            /,
        ) -> ComposedContexts:
            events.append("compose")
            raise ValueError("composition failed")

    builder = PurePlanBuilder(
        "run",
        grouper=_RecordingGrouper(events, GroupedInputs(snapshots=())),
        composer=FailingComposer(),
        scheduler=_RecordingScheduler(events, ()),
    )

    # When
    with pytest.raises(ValueError) as error:
        builder.plan(_inputs(), _configuration())

    # Then
    assert events == ["group", "compose"]
    assert str(error.value) == "composition failed"


def test_default_plan_leaf_fails_visibly_until_implemented() -> None:
    # Given
    builder = PurePlanBuilder("run")

    # When
    with pytest.raises(NotImplementedError) as error:
        builder.plan(_inputs(), _configuration())

    # Then
    assert str(error.value) == "source grouping is not implemented yet"


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason="not implemented: AC-1 deterministic Cartesian matrix composition",
)
def test_plan_orders_context_model_and_effort_products_deterministically() -> None:
    """Keep the full matrix behavior unclaimed until its leaf work is delivered."""
    # Given
    # Ordered contexts with default and explicit separators plus repeated flags.

    # When
    # The pure planner composes every context, model, and effort combination.

    # Then
    # The full product has last-context-fastest order before model and effort
    # order; exact separator bytes and duplicate scheduled positions are retained.
    pass
