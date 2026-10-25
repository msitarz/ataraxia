# SPDX-License-Identifier: Apache-2.0
"""Runtime guarantees for shared harness models."""

from hashlib import sha256
from pathlib import Path

from pydantic import ValidationError
import pytest

from script.eval.model import (
    AttemptRecord,
    DirectoryOption,
    FrozenPlan,
    HarnessConfig,
    InstructionsSnapshot,
    PlannedCall,
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
    instructions = InstructionsSnapshot(
        repository_path="context/instructions.bin",
        commit_blob_sha="instructions-blob",
        content_sha256=sha256(instruction_bytes).hexdigest(),
        content=instruction_bytes,
    )
    call = PlannedCall(
        position=0,
        context_indices=(0,),
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
        snapshots=(source,),
        boundary_bytes=(b"\n",),
        instructions_file=instructions,
        calls=(call,),
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
