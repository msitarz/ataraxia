# SPDX-License-Identifier: Apache-2.0
"""Runtime guarantees for shared harness models."""

from hashlib import sha256
from pathlib import Path

from pydantic import ValidationError
import pytest

from script.eval.model import (
    AttemptRecord,
    CallRecord,
    DirectoryOption,
    FrozenPlan,
    HarnessConfig,
    InstructionsSnapshot,
    PlannedCall,
    RunRecord,
    SeparatorOption,
    SourceSnapshot,
)


def config_values() -> dict[str, object]:
    """Return a valid configuration at the meaningful zero-cap boundary."""
    return {
        "ordered_options": (DirectoryOption(position=0, path=Path("context")),),
        "models": ("model-a",),
        "efforts": ("low",),
        "concurrency": 1,
        "output_directory": Path("results"),
        "dry_run": False,
        "timeout_seconds": 1.0,
        "cleanup_timeout_seconds": 1.0,
        "grace_seconds": 0.0,
        "output_limit_bytes": 0,
        "instructions_file_path": None,
    }


def attempt_values() -> dict[str, object]:
    """Return a valid persisted attempt with an uncapped output allowance."""
    return {
        "run_id": "run",
        "call_id": "call",
        "position": 0,
        "attempt_number": 1,
        "control_flow": "returned",
        "outcome_kind": "no_observation",
        "started_at_utc": "2026-10-25T00:00:00Z",
        "ended_at_utc": None,
        "argv": ("codex",),
        "cwd": "/work",
        "timeout_seconds": 1.0,
        "cleanup_timeout_seconds": 1.0,
        "grace_seconds": 0.0,
        "output_limit_bytes": 0,
        "elapsed_seconds": None,
        "elapsed_basis": "unavailable",
        "exit_status": None,
        "termination_reason": None,
        "cleanup": None,
        "stdout_artifact": None,
        "stderr_artifact": None,
        "usage_telemetry": b"\xff\x00usage",
        "error_type": None,
        "diagnostic": None,
    }


def call_record_values(
    *, attempts: tuple[dict[str, object], ...] = ()
) -> dict[str, object]:
    """Return a persisted call record consistent with its attempt fixtures."""
    return {
        "run_id": "run",
        "call_id": "call",
        "position": 0,
        "state": "complete",
        "source_paths": ("context/source.txt",),
        "source_sha256": ("source-digest",),
        "boundary_bytes_hex": (),
        "prompt_sha256": "prompt-digest",
        "model": "model-a",
        "effort": "low",
        "effective_settings_sha256": "settings-digest",
        "attempts": attempts,
    }


def run_record_values(calls: tuple[CallRecord, ...] = ()) -> dict[str, object]:
    """Return a run record containing the supplied child call records."""
    return {
        "run_id": "run",
        "repository_root": "/repo",
        "head_commit": "commit",
        "state": "complete",
        "runner_version": "runner",
        "codex_path": None,
        "cli_version": None,
        "effective_settings": (),
        "calls": calls,
    }


def frozen_plan() -> FrozenPlan:
    """Build a full plan with paths, ordered options, and binary snapshots."""
    source_bytes = b"source\xff"
    instruction_bytes = b"instructions\x00"
    prompt_bytes = b"prompt\x80"
    configuration = HarnessConfig.model_validate(
        config_values()
        | {
            "ordered_options": (
                DirectoryOption(position=0, path=Path("context")),
                SeparatorOption(position=1, value="\\n"),
                DirectoryOption(position=2, path=Path("more-context")),
            ),
            "instructions_file_path": Path("context/instructions.bin"),
            "output_directory": None,
            "dry_run": True,
        }
    )
    source = SourceSnapshot(
        directory_position=0,
        repository_path="context/source.bin",
        commit_blob_sha="source-blob",
        content_sha256=sha256(source_bytes).hexdigest(),
        content=source_bytes,
    )
    other_source_bytes = b"other source"
    other_source = SourceSnapshot(
        directory_position=2,
        repository_path="more-context/other.bin",
        commit_blob_sha="other-source-blob",
        content_sha256=sha256(other_source_bytes).hexdigest(),
        content=other_source_bytes,
    )
    second_source_bytes = b"second context source"
    second_source = SourceSnapshot(
        directory_position=0,
        repository_path="context/second.bin",
        commit_blob_sha="second-source-blob",
        content_sha256=sha256(second_source_bytes).hexdigest(),
        content=second_source_bytes,
    )
    instructions = InstructionsSnapshot(
        repository_path="context/instructions.bin",
        commit_blob_sha="instructions-blob",
        content_sha256=sha256(instruction_bytes).hexdigest(),
        content=instruction_bytes,
    )
    call = PlannedCall(
        position=0,
        context_indices=(0, 1),
        model="model-a",
        effort="low",
        prompt_sha256=sha256(prompt_bytes).hexdigest(),
        prompt=prompt_bytes,
    )
    other_call = PlannedCall(
        position=1,
        context_indices=(2,),
        model="model-a",
        effort="low",
        prompt_sha256=sha256(prompt_bytes).hexdigest(),
        prompt=prompt_bytes,
    )
    return FrozenPlan(
        run_id="run",
        configuration=configuration,
        repository_root=Path("/repo"),
        head_commit="commit",
        snapshots=(source, second_source, other_source),
        boundary_bytes=(b"\n",),
        instructions_file=instructions,
        calls=(call, other_call),
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("concurrency", True),
        ("concurrency", 0),
        ("timeout_seconds", float("inf")),
        ("cleanup_timeout_seconds", 0.0),
        ("grace_seconds", -0.1),
        ("output_limit_bytes", -1),
        ("retry_limit", -1),
    ],
    ids=[
        "bool-is-not-integer",
        "concurrency-positive",
        "timeout-finite",
        "cleanup-positive",
        "grace-nonnegative",
        "output-limit-nonnegative",
        "retry-limit-nonnegative",
    ],
)
def test_configuration_rejects_invalid_runtime_limits(
    field: str, value: object
) -> None:
    # Given
    values = config_values() | {field: value}

    # When
    with pytest.raises(ValidationError) as error:
        HarnessConfig.model_validate(values)

    # Then
    assert field in str(error.value)


def test_configuration_keeps_zero_output_cap_and_enforces_grace_order() -> None:
    # Given
    values = config_values()

    # When
    configuration = HarnessConfig.model_validate(values)
    too_long_grace = values | {"grace_seconds": 1.0}

    # Then
    assert configuration.output_limit_bytes == 0
    with pytest.raises(ValidationError, match="grace_seconds must be less"):
        HarnessConfig.model_validate(too_long_grace)


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"ordered_options": ()}, "at least one directory"),
        ({"models": ()}, "at least one model"),
        ({"efforts": ()}, "at least one effort"),
        ({"output_directory": None}, "execution requires an output directory"),
    ],
    ids=["directory-required", "model-required", "effort-required", "output-required"],
)
def test_configuration_rejects_missing_matrix_inputs_or_execution_output(
    changes: dict[str, object], reason: str
) -> None:
    # Given
    values = config_values() | changes

    # When
    with pytest.raises(ValidationError) as error:
        HarnessConfig.model_validate(values)

    # Then
    assert reason in str(error.value)


@pytest.mark.parametrize(
    "options",
    [
        (
            DirectoryOption(position=1, path=Path("a")),
            SeparatorOption(position=1, value="\n"),
            DirectoryOption(position=2, path=Path("b")),
        ),
        (
            DirectoryOption(position=0, path=Path("a")),
            SeparatorOption(position=2, value="\n"),
            DirectoryOption(position=1, path=Path("b")),
        ),
        (
            DirectoryOption(position=0, path=Path("a")),
            SeparatorOption(position=1, value="\n"),
            SeparatorOption(position=2, value="\t"),
            DirectoryOption(position=3, path=Path("b")),
        ),
        (
            SeparatorOption(position=0, value="\n"),
            DirectoryOption(position=1, path=Path("a")),
        ),
        (
            DirectoryOption(position=0, path=Path("a")),
            SeparatorOption(position=1, value="\n"),
        ),
        (
            DirectoryOption(position=0, path=Path("a")),
            SeparatorOption(position=1, value=r"\q"),
            DirectoryOption(position=2, path=Path("b")),
        ),
        (
            DirectoryOption(position=0, path=Path("a")),
            SeparatorOption(position=1, value="dangling\\"),
            DirectoryOption(position=2, path=Path("b")),
        ),
    ],
    ids=[
        "duplicate-position",
        "unordered-positions",
        "multiple-separators",
        "leading",
        "trailing",
        "unknown-escape",
        "dangling-escape",
    ],
)
def test_configuration_rejects_malformed_ordered_options(
    options: tuple[DirectoryOption | SeparatorOption, ...],
) -> None:
    # Given
    values = config_values() | {"ordered_options": options}

    # When
    with pytest.raises(ValidationError):
        HarnessConfig.model_validate(values)


def test_configuration_accepts_all_supported_separator_escapes() -> None:
    # Given
    values = config_values() | {
        "ordered_options": (
            DirectoryOption(position=0, path=Path("a")),
            SeparatorOption(position=1, value=r"\n\r\t\\"),
            DirectoryOption(position=2, path=Path("b")),
        )
    }

    # When
    configuration = HarnessConfig.model_validate(values)

    # Then
    separator = configuration.ordered_options[1]
    assert isinstance(separator, SeparatorOption)
    assert separator.value == r"\n\r\t\\"


def test_option_and_call_positions_must_be_nonnegative() -> None:
    # Given
    call_values = call_record_values() | {"position": -1}

    # When / Then
    with pytest.raises(ValidationError):
        DirectoryOption.model_validate({"position": -1, "path": Path("context")})
    with pytest.raises(ValidationError):
        SeparatorOption.model_validate({"position": -1, "value": "\n"})
    with pytest.raises(ValidationError):
        CallRecord.model_validate(call_values)


def test_dry_run_allows_the_output_destination_to_be_omitted() -> None:
    # Given
    values = config_values() | {"dry_run": True, "output_directory": None}

    # When
    configuration = HarnessConfig.model_validate(values)

    # Then
    assert configuration.output_directory is None


def test_snapshot_json_round_trip_preserves_arbitrary_output_bytes() -> None:
    # Given
    snapshot = SourceSnapshot(
        directory_position=0,
        repository_path="context/data.bin",
        commit_blob_sha="blob",
        content_sha256=sha256(b"\xff\x00\x80").hexdigest(),
        content=b"\xff\x00\x80",
    )

    # When
    serialized = snapshot.model_dump_json()
    restored = SourceSnapshot.model_validate_json(serialized)

    # Then
    assert restored == snapshot
    assert restored.content == b"\xff\x00\x80"


def test_snapshot_rejects_a_digest_that_does_not_identify_its_bytes() -> None:
    # Given
    content = b"captured bytes"

    # When
    with pytest.raises(ValidationError) as error:
        SourceSnapshot(
            directory_position=0,
            repository_path="context/data.bin",
            commit_blob_sha="blob",
            content_sha256=sha256(b"different bytes").hexdigest(),
            content=content,
        )

    # Then
    assert "content_sha256 must match content" in str(error.value)


def test_attempt_metadata_json_round_trip_keeps_arbitrary_telemetry_bytes() -> None:
    # Given
    record = AttemptRecord.model_validate(attempt_values())

    # When
    serialized = record.model_dump_json()
    restored = AttemptRecord.model_validate_json(serialized)

    # Then
    assert restored == record
    assert restored.usage_telemetry == b"\xff\x00usage"


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"timeout_seconds": 0.0}, "timeout_seconds"),
        ({"timeout_seconds": float("inf")}, "timeout_seconds"),
        ({"cleanup_timeout_seconds": 0.0}, "cleanup_timeout_seconds"),
        ({"grace_seconds": -0.1}, "grace_seconds"),
        ({"grace_seconds": 1.0}, "grace_seconds must be less"),
        ({"output_limit_bytes": -1}, "output_limit_bytes"),
        ({"elapsed_seconds": -0.1}, "elapsed_seconds"),
        ({"elapsed_seconds": float("inf")}, "elapsed_seconds"),
        (
            {"elapsed_basis": "supervisor_observation"},
            "elapsed_seconds must match elapsed_basis",
        ),
        (
            {"elapsed_seconds": 0.0},
            "elapsed_seconds must match elapsed_basis",
        ),
    ],
    ids=[
        "timeout-positive",
        "timeout-finite",
        "cleanup-positive",
        "grace-nonnegative",
        "grace-below-cleanup",
        "output-nonnegative",
        "elapsed-nonnegative",
        "elapsed-finite",
        "observed-needs-value",
        "unavailable-needs-none",
    ],
)
def test_attempt_metadata_rejects_invalid_limits_and_elapsed_basis(
    changes: dict[str, object], reason: str
) -> None:
    # Given
    values = attempt_values() | changes

    # When
    with pytest.raises(ValidationError) as error:
        AttemptRecord.model_validate(values)

    # Then
    assert reason in str(error.value)


def test_attempt_metadata_accepts_zero_cap_and_observed_zero_elapsed() -> None:
    # Given
    values = attempt_values() | {
        "cleanup_timeout_seconds": 2.0,
        "grace_seconds": 1.0,
        "elapsed_seconds": 0.0,
        "elapsed_basis": "supervisor_observation",
    }

    # When
    record = AttemptRecord.model_validate(values)

    # Then
    assert record.output_limit_bytes == 0
    assert record.elapsed_seconds == pytest.approx(0.0)


def test_attempt_metadata_preserves_negative_exit_status_and_unknown_evidence() -> None:
    # Given
    values = attempt_values() | {
        "control_flow": "raised",
        "outcome_kind": "unexpected_exception",
        "exit_status": -9,
    }

    # When
    record = AttemptRecord.model_validate(values)

    # Then
    assert record.exit_status == -9
    assert record.cleanup is None
    assert record.elapsed_seconds is None


def test_frozen_plan_json_round_trip_preserves_nested_binary_and_path_values() -> None:
    # Given
    plan = frozen_plan()

    # When
    serialized = plan.model_dump_json()
    restored = FrozenPlan.model_validate_json(serialized)

    # Then
    assert restored == plan
    assert isinstance(restored.configuration.ordered_options[1], SeparatorOption)
    assert restored.snapshots[0].content == b"source\xff"
    assert restored.instructions_file is not None
    assert restored.instructions_file.content == b"instructions\x00"
    assert restored.calls[0].prompt == b"prompt\x80"
    assert restored.repository_root == Path("/repo")


def test_frozen_plan_rejects_mutation_of_nested_models() -> None:
    # Given
    plan = frozen_plan()
    concurrency_field = "concurrency"
    prompt_field = "prompt"

    # When
    with pytest.raises(ValidationError):
        setattr(plan.configuration, concurrency_field, 2)
    with pytest.raises(ValidationError):
        setattr(plan.calls[0], prompt_field, b"changed")

    # Then
    assert plan.configuration.concurrency == 1
    assert plan.calls[0].prompt == b"prompt\x80"


@pytest.mark.parametrize(
    ("changed_call", "instructions_file", "expected"),
    [
        ({"context_indices": (3,)}, "keep", "outside snapshots"),
        ({"context_indices": (0, 2)}, "keep", "one directory"),
        ({"context_indices": (0, 0)}, "keep", "must be unique"),
        ({"context_indices": (0, 1)}, None, "requires an instructions snapshot"),
        (
            {"context_indices": (0, 1)},
            "clear-config",
            "requires a configured instructions file",
        ),
        ({"context_indices": (1,)}, "keep", "every snapshot"),
    ],
)
def test_frozen_plan_rejects_inconsistent_input_relationships(
    changed_call: dict[str, object],
    instructions_file: str | None,
    expected: str,
) -> None:
    # Given
    plan = frozen_plan()
    values = plan.model_dump()
    values["calls"] = (
        values["calls"][0] | changed_call,
        values["calls"][1],
    )
    if instructions_file is None:
        values["instructions_file"] = None
    elif instructions_file == "clear-config":
        values["configuration"] = values["configuration"] | {
            "instructions_file_path": None
        }

    # When
    with pytest.raises(ValidationError, match=expected):
        FrozenPlan.model_validate(values)


def test_frozen_plan_requires_calls_to_cover_every_directory() -> None:
    # Given
    values = frozen_plan().model_dump()
    values["calls"] = values["calls"][:1]

    # When
    with pytest.raises(ValidationError, match="cover every configured directory"):
        FrozenPlan.model_validate(values)


def test_frozen_plan_requires_snapshots_in_directory_order() -> None:
    # Given
    values = frozen_plan().model_dump()
    values["snapshots"] = (
        values["snapshots"][2],
        values["snapshots"][0],
        values["snapshots"][1],
    )

    # When / Then
    with pytest.raises(ValidationError, match="cover every configured directory"):
        FrozenPlan.model_validate(values)


def test_attempt_metadata_rejects_non_utc_or_unordered_timestamps() -> None:
    # Given
    values = attempt_values() | {
        "ended_at_utc": "2026-10-25T00:00:01Z",
    }

    # When / Then
    for changes in (
        {"started_at_utc": "2026-10-25T00:00:00"},
        {"started_at_utc": "2026-10-25T01:00:00+01:00"},
        {"ended_at_utc": "2026-10-24T23:59:59Z"},
    ):
        with pytest.raises(ValidationError):
            AttemptRecord.model_validate(values | changes)


@pytest.mark.parametrize(
    ("control_flow", "outcome_kind"),
    [("cancelled", "no_observation"), ("raised", "infrastructure_failure")],
)
def test_attempt_metadata_rejects_mechanically_inconsistent_outcomes(
    control_flow: str, outcome_kind: str
) -> None:
    # Given
    values = attempt_values() | {
        "control_flow": control_flow,
        "outcome_kind": outcome_kind,
    }

    # When / Then
    with pytest.raises(ValidationError, match="outcome_kind must agree"):
        AttemptRecord.model_validate(values)


def test_call_record_checks_parallel_source_identity_and_attempt_owner() -> None:
    # Given
    valid_attempt = attempt_values()
    call = CallRecord.model_validate(call_record_values(attempts=(valid_attempt,)))
    bad_sources = call_record_values() | {"source_sha256": ()}
    wrong_attempt = valid_attempt | {"position": 1}
    bad_attempt_owner = call_record_values(attempts=(wrong_attempt,))

    # When / Then
    assert call.attempts[0].call_id == call.call_id
    with pytest.raises(ValidationError, match="must have equal lengths"):
        CallRecord.model_validate(bad_sources)
    with pytest.raises(ValidationError, match="must match its call"):
        CallRecord.model_validate(bad_attempt_owner)


def test_run_record_checks_child_call_identity_and_positions() -> None:
    # Given
    call = CallRecord.model_validate(call_record_values())
    other_run_call = call_record_values() | {"run_id": "other-run"}
    duplicate_position = CallRecord.model_validate(
        call_record_values() | {"call_id": "another-call"}
    )

    # When / Then
    assert RunRecord.model_validate(run_record_values((call,))).calls == (call,)
    with pytest.raises(ValidationError, match="must match its run record"):
        RunRecord.model_validate(
            run_record_values((CallRecord.model_validate(other_run_call),))
        )
    with pytest.raises(ValidationError, match="positions must be unique"):
        RunRecord.model_validate(run_record_values((call, duplicate_position)))


def test_instructions_snapshot_rejects_mismatched_content_digest() -> None:
    # Given
    content = b"instructions"

    # When
    with pytest.raises(ValidationError) as error:
        InstructionsSnapshot(
            repository_path="instructions.md",
            commit_blob_sha="blob",
            content_sha256=sha256(b"different").hexdigest(),
            content=content,
        )

    # Then
    assert "content_sha256 must match content" in str(error.value)


def test_planned_call_rejects_mismatched_prompt_digest() -> None:
    # Given
    prompt = b"frozen prompt"

    # When
    with pytest.raises(ValidationError) as error:
        PlannedCall(
            position=0,
            context_indices=(0,),
            model="model-a",
            effort="low",
            prompt_sha256=sha256(b"different").hexdigest(),
            prompt=prompt,
        )

    # Then
    assert "prompt_sha256 must match prompt" in str(error.value)


def test_configuration_rejects_extra_fields() -> None:
    # Given
    values = config_values() | {"surprise": True}

    # When
    with pytest.raises(ValidationError) as error:
        HarnessConfig.model_validate(values)

    # Then
    assert "Extra inputs are not permitted" in str(error.value)


def test_configuration_rejects_mutable_sequence_inputs() -> None:
    # Given
    values = config_values() | {"models": ["model-a"]}

    # When
    with pytest.raises(ValidationError) as error:
        HarnessConfig.model_validate(values)

    # Then
    assert "tuple_type" in str(error.value)
