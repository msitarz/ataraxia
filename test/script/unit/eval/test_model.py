# SPDX-License-Identifier: Apache-2.0
"""Runtime guarantees for shared harness models."""

from hashlib import sha256
from pathlib import Path

from pydantic import ValidationError
import pytest

from script.eval.model import (
    AttemptRecord,
    DirectoryOption,
    HarnessConfig,
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
    record = AttemptRecord(
        run_id="run",
        call_id="call",
        position=0,
        attempt_number=1,
        control_flow="returned",
        outcome_kind="no_observation",
        started_at_utc="2026-10-25T00:00:00Z",
        ended_at_utc=None,
        argv=("codex",),
        cwd="/work",
        timeout_seconds=1.0,
        cleanup_timeout_seconds=1.0,
        grace_seconds=0.0,
        output_limit_bytes=0,
        elapsed_seconds=None,
        elapsed_basis="unavailable",
        exit_status=None,
        termination_reason=None,
        cleanup=None,
        stdout_artifact=None,
        stderr_artifact=None,
        usage_telemetry=b"\xff\x00usage",
        error_type=None,
        diagnostic=None,
    )

    # When
    serialized = record.model_dump_json()
    restored = AttemptRecord.model_validate_json(serialized)

    # Then
    assert restored == record
    assert restored.usage_telemetry == b"\xff\x00usage"


def test_configuration_rejects_extra_fields_and_mutable_sequence_inputs() -> None:
    # Given
    values = config_values() | {"surprise": True}

    # When
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        HarnessConfig.model_validate(values)

    mutable_values = config_values() | {"models": ["model-a"]}
    with pytest.raises(ValidationError):
        HarnessConfig.model_validate(mutable_values)

    # Then
    assert "surprise" in values
    assert isinstance(mutable_values["models"], list)
