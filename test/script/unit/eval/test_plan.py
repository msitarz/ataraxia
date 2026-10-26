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
    SeparatorOption,
    SourceSnapshot,
)
from script.eval.plan import (
    ComposeContexts,
    ComposedContexts,
    GroupedInputs,
    GroupInputs,
    PurePlanBuilder,
    ScheduleCalls,
)


def _configuration(
    *,
    instructions_path: Path | None = None,
    ordered_options: tuple[DirectoryOption | SeparatorOption, ...] | None = None,
    models: tuple[str, ...] = ("model-a",),
    efforts: tuple[str, ...] = ("low",),
) -> HarnessConfig:
    return HarnessConfig(
        ordered_options=ordered_options
        if ordered_options is not None
        else (DirectoryOption(position=0, path=Path("context")),),
        models=models,
        efforts=efforts,
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


def _record_grouper(
    events: list[str],
    received: list[tuple[FrozenInputs, HarnessConfig]],
    result: GroupedInputs,
) -> GroupInputs:
    def group(inputs: FrozenInputs, config: HarnessConfig) -> GroupedInputs:
        events.append("group")
        received.append((inputs, config))
        return result

    return group


def _record_composer(
    events: list[str],
    received: list[tuple[FrozenInputs, GroupedInputs, HarnessConfig]],
    result: ComposedContexts,
) -> ComposeContexts:
    def compose(
        inputs: FrozenInputs, grouped: GroupedInputs, config: HarnessConfig
    ) -> ComposedContexts:
        events.append("compose")
        received.append((inputs, grouped, config))
        return result

    return compose


def _record_scheduler(
    events: list[str],
    received: list[tuple[ComposedContexts, HarnessConfig]],
    result: tuple[PlannedCall, ...],
) -> ScheduleCalls:
    def schedule(
        composed: ComposedContexts, config: HarnessConfig
    ) -> tuple[PlannedCall, ...]:
        events.append("schedule")
        received.append((composed, config))
        return result

    return schedule


def test_plan_wires_pure_steps_in_order_and_preserves_frozen_values() -> None:
    # Given
    inputs = _inputs()
    config = _configuration(instructions_path=Path("context/instructions.txt"))
    events: list[str] = []
    grouped_received: list[tuple[FrozenInputs, HarnessConfig]] = []
    composed_received: list[tuple[FrozenInputs, GroupedInputs, HarnessConfig]] = []
    scheduled_received: list[tuple[ComposedContexts, HarnessConfig]] = []
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
    builder = PurePlanBuilder(
        "caller-run-id",
        grouper=_record_grouper(events, grouped_received, grouped),
        composer=_record_composer(events, composed_received, composed),
        scheduler=_record_scheduler(events, scheduled_received, (call,)),
    )

    # When
    plan = builder.plan(inputs, config)

    # Then
    assert events == ["group", "compose", "schedule"]
    assert grouped_received == [(inputs, config)]
    assert composed_received == [(inputs, grouped, config)]
    composer_inputs = composed_received[0][0]
    assert composer_inputs is inputs
    assert composer_inputs.sources[0].content == b"source"
    assert composer_inputs.instructions_file is inputs.instructions_file
    assert composer_inputs.instructions_file is not None
    assert composer_inputs.instructions_file.content == b"instruction bytes\x00"
    assert scheduled_received == [(composed, config)]
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

    def fail_composition(
        inputs: FrozenInputs, grouped: GroupedInputs, config: HarnessConfig
    ) -> ComposedContexts:
        events.append("compose")
        raise ValueError("composition failed")

    builder = PurePlanBuilder(
        "run",
        grouper=_record_grouper(events, [], GroupedInputs(snapshots=())),
        composer=fail_composition,
        scheduler=_record_scheduler(events, [], ()),
    )

    # When
    with pytest.raises(ValueError) as error:
        builder.plan(_inputs(), _configuration())

    # Then
    assert events == ["group", "compose"]
    assert str(error.value) == "composition failed"


def test_default_plan_composes_one_directory_and_preserves_instructions() -> None:
    # Given
    builder = PurePlanBuilder("run")
    inputs = _inputs()
    config = _configuration(instructions_path=Path("context/instructions.txt"))

    # When
    plan = builder.plan(inputs, config)

    # Then
    assert plan.run_id == "run"
    assert plan.calls[0].prompt == b"source"
    assert plan.instructions_file is not None
    assert plan.instructions_file.content == b"instruction bytes\x00"


def test_plan_orders_context_model_and_effort_products_deterministically() -> None:
    # Given
    options = (
        DirectoryOption(position=0, path=Path("first")),
        SeparatorOption(position=1, value="|"),
        DirectoryOption(position=2, path=Path("second")),
    )
    sources = (
        _source(0, "first/a.txt", b"A"),
        _source(0, "first/b.txt", b"B"),
        _source(2, "second/a.txt", b"1"),
        _source(2, "second/b.txt", b"2"),
    )
    instructions = _inputs().instructions_file
    inputs = FrozenInputs(Path("/repo"), "head", sources, instructions)
    config = _configuration(
        instructions_path=Path("context/instructions.txt"),
        ordered_options=options,
        models=("m", "m"),
        efforts=("low", "high"),
    )
    builder = PurePlanBuilder("repeat-one")

    # When
    plan = builder.plan(inputs, config)

    # Then
    assert plan.boundary_bytes == (b"|",)
    assert tuple(
        (call.position, call.context_indices, call.model, call.effort, call.prompt)
        for call in plan.calls
    ) == (
        (0, (0, 2), "m", "low", b"A|1"),
        (1, (0, 2), "m", "high", b"A|1"),
        (2, (0, 2), "m", "low", b"A|1"),
        (3, (0, 2), "m", "high", b"A|1"),
        (4, (0, 3), "m", "low", b"A|2"),
        (5, (0, 3), "m", "high", b"A|2"),
        (6, (0, 3), "m", "low", b"A|2"),
        (7, (0, 3), "m", "high", b"A|2"),
        (8, (1, 2), "m", "low", b"B|1"),
        (9, (1, 2), "m", "high", b"B|1"),
        (10, (1, 2), "m", "low", b"B|1"),
        (11, (1, 2), "m", "high", b"B|1"),
        (12, (1, 3), "m", "low", b"B|2"),
        (13, (1, 3), "m", "high", b"B|2"),
        (14, (1, 3), "m", "low", b"B|2"),
        (15, (1, 3), "m", "high", b"B|2"),
    )
    assert tuple(call.prompt_sha256 for call in plan.calls[::4]) == (
        sha256(b"A|1").hexdigest(),
        sha256(b"A|2").hexdigest(),
        sha256(b"B|1").hexdigest(),
        sha256(b"B|2").hexdigest(),
    )
    assert plan.instructions_file is instructions
    assert all(b"instruction bytes" not in call.prompt for call in plan.calls)


def test_caller_run_id_changes_without_changing_deterministic_plan_parts() -> None:
    # Given
    inputs = _inputs()
    config = _configuration(instructions_path=Path("context/instructions.txt"))
    first_builder = PurePlanBuilder("repeat-one")
    second_builder = PurePlanBuilder("repeat-two")

    # When
    first_plan = first_builder.plan(inputs, config)
    second_plan = second_builder.plan(inputs, config)

    # Then
    assert first_plan.run_id == "repeat-one"
    assert second_plan.run_id == "repeat-two"
    assert first_plan.calls == second_plan.calls
    assert first_plan.boundary_bytes == second_plan.boundary_bytes


def test_three_directory_boundaries_and_model_effort_order_are_preserved() -> None:
    # Given
    options = (
        DirectoryOption(position=1, path=Path("first")),
        SeparatorOption(position=3, value="|"),
        DirectoryOption(position=5, path=Path("second")),
        DirectoryOption(position=9, path=Path("third")),
    )
    inputs = FrozenInputs(
        Path("/repo"),
        "head",
        (
            _source(1, "first/a.txt", b"A"),
            _source(5, "second/b.txt", b"B"),
            _source(9, "third/c.txt", b"C"),
        ),
        None,
    )
    config = _configuration(
        ordered_options=options,
        models=("model-z", "model-a"),
        efforts=("high", "low", "high"),
    )

    # When
    plan = PurePlanBuilder("run").plan(inputs, config)

    # Then
    assert plan.boundary_bytes == (b"|", b"\n\n")
    assert tuple(
        (call.position, call.context_indices, call.model, call.effort, call.prompt)
        for call in plan.calls
    ) == (
        (0, (0, 1, 2), "model-z", "high", b"A|B\n\nC"),
        (1, (0, 1, 2), "model-z", "low", b"A|B\n\nC"),
        (2, (0, 1, 2), "model-z", "high", b"A|B\n\nC"),
        (3, (0, 1, 2), "model-a", "high", b"A|B\n\nC"),
        (4, (0, 1, 2), "model-a", "low", b"A|B\n\nC"),
        (5, (0, 1, 2), "model-a", "high", b"A|B\n\nC"),
    )


def _source(position: int, path: str, content: bytes) -> SourceSnapshot:
    return SourceSnapshot(
        directory_position=position,
        repository_path=path,
        commit_blob_sha="trusted-input",
        content_sha256=sha256(content).hexdigest(),
        content=content,
    )


@pytest.mark.parametrize(
    ("separator", "expected"),
    [(None, b"\n\n"), ("", b""), (r"\n\r\t\\é", "\n\r\t\\é".encode())],
    ids=["default-double-lf", "empty-override", "controls-backslash-unicode"],
)
def test_default_plan_composes_exact_boundary_bytes(
    separator: str | None, expected: bytes
) -> None:
    # Given
    options: tuple[DirectoryOption | SeparatorOption, ...] = (
        DirectoryOption(position=3, path=Path("one")),
        *(
            (SeparatorOption(position=4, value=separator),)
            if separator is not None
            else ()
        ),
        DirectoryOption(position=5, path=Path("two")),
    )
    inputs = FrozenInputs(
        Path("/repo"),
        "head",
        (_source(3, "one/empty", b""), _source(5, "two/text", "é".encode())),
        None,
    )

    # When
    plan = PurePlanBuilder("run").plan(inputs, _configuration(ordered_options=options))

    # Then
    assert plan.boundary_bytes == (expected,)
    assert plan.calls[0].prompt == expected + "é".encode()
    assert plan.calls[0].prompt_sha256 == sha256(expected + "é".encode()).hexdigest()


def test_repeated_directory_options_keep_distinct_groups_and_indices() -> None:
    # Given
    options = (
        DirectoryOption(position=0, path=Path("same")),
        DirectoryOption(position=1, path=Path("same")),
    )
    inputs = FrozenInputs(
        Path("/repo"),
        "head",
        (_source(0, "same/a", b"a"), _source(1, "same/a", b"a")),
        None,
    )

    # When
    plan = PurePlanBuilder("run").plan(inputs, _configuration(ordered_options=options))

    # Then
    assert plan.calls[0].context_indices == (0, 1)
    assert plan.boundary_bytes == (b"\n\n",)
    assert plan.calls[0].prompt == b"a\n\na"
