# SPDX-License-Identifier: Apache-2.0
"""Runtime guarantees for pure plan orchestration."""

from hashlib import sha256
from pathlib import Path

import pytest

from script.eval.model import (
    DirectoryOption,
    FrozenInputs,
    HarnessConfig,
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


def _configuration() -> HarnessConfig:
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
        instructions_file_path=None,
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
    return FrozenInputs(Path("/repo"), "commit-sha", (source,), None)


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
        self.received: tuple[GroupedInputs, HarnessConfig] | None = None

    def compose(
        self, grouped: GroupedInputs, config: HarnessConfig, /
    ) -> ComposedContexts:
        self.events.append("compose")
        self.received = (grouped, config)
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
    config = _configuration()
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
    assert composer.received == (grouped, config)
    assert scheduler.received == (composed, config)
    assert plan.run_id == "caller-run-id"
    assert plan.configuration is config
    assert plan.repository_root == inputs.repository_root
    assert plan.head_commit == inputs.head_commit
    assert plan.snapshots == inputs.sources
    assert plan.boundary_bytes == composed.boundary_bytes
    assert plan.instructions_file is inputs.instructions_file
    assert plan.calls == (call,)


def test_plan_propagates_leaf_failure_without_running_later_steps() -> None:
    # Given
    events: list[str] = []

    class FailingComposer(ContextComposer):
        def compose(
            self, grouped: GroupedInputs, config: HarnessConfig, /
        ) -> ComposedContexts:
            events.append("compose")
            raise ValueError("composition failed")

    builder = PurePlanBuilder(
        "run",
        grouper=_RecordingGrouper(events, GroupedInputs(snapshots=())),
        composer=FailingComposer(),
        scheduler=_RecordingScheduler(events, ()),
    )

    # When / Then
    with pytest.raises(ValueError, match="composition failed"):
        builder.plan(_inputs(), _configuration())
    assert events == ["group", "compose"]


def test_default_plan_leaf_fails_visibly_until_implemented() -> None:
    # Given
    builder = PurePlanBuilder("run")

    # When / Then
    with pytest.raises(NotImplementedError, match="source grouping is not implemented"):
        builder.plan(_inputs(), _configuration())


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
