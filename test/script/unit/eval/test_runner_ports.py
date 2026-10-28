# SPDX-License-Identifier: Apache-2.0
"""Runtime configuration and immutable shared runner values."""

from dataclasses import FrozenInstanceError
from pathlib import Path

from pydantic import ValidationError
import pytest

from script.eval.model import DirectoryOption, HarnessConfig
from script.eval.runner import CliBinding, ProgressCounts


def set_field(value: object, field: str, replacement: object) -> None:
    """Attempt an attribute mutation without static-assignment type ignores."""
    setattr(value, field, replacement)


def configuration(**overrides: object) -> HarnessConfig:
    """Build a minimal valid harness configuration for boundary cases."""
    values: dict[str, object] = {
        "ordered_options": (DirectoryOption(position=0, path=Path("context")),),
        "models": ("model-a",),
        "efforts": ("low",),
        "concurrency": 1,
        "output_directory": None,
        "dry_run": True,
        "timeout_seconds": 1.0,
        "cleanup_timeout_seconds": 1.0,
        "grace_seconds": 0.0,
        "output_limit_bytes": 0,
        "instructions_file_path": None,
    }
    values.update(overrides)
    return HarnessConfig.model_validate(values)


def test_runner_configuration_defaults_are_stable_and_serialized() -> None:
    # Given
    config = configuration()

    # When
    serialized = config.model_dump_json()
    restored = HarnessConfig.model_validate_json(serialized)

    # Then
    assert config.quiet is False
    assert config.progress_interval_seconds == pytest.approx(1.0)
    assert config.retry_limit == 0
    assert config.retry_nonzero_exit is False
    assert config.quota_wait_enabled is False
    assert config.quota_wait_limit_seconds is None
    assert config.quota_poll_interval_seconds == pytest.approx(60.0)
    assert config.quota_probe_budget is None
    assert config.capacity_retry_limit == 0
    assert config.capacity_backoff_base_seconds is None
    assert config.capacity_backoff_cap_seconds is None
    assert restored == config


@pytest.mark.parametrize(
    "overrides",
    [
        {"quota_wait_enabled": True, "quota_probe_budget": None},
        {"quota_wait_enabled": True, "quota_probe_budget": 3},
        {"quota_wait_enabled": True, "quota_probe_budget": 0},
        {"quota_wait_enabled": False, "quota_probe_budget": 0},
        {
            "capacity_retry_limit": 1,
            "capacity_backoff_base_seconds": 2.0,
            "capacity_backoff_cap_seconds": 2.0,
        },
    ],
    ids=[
        "enabled-quota-uncapped",
        "enabled-quota-positive-cap",
        "enabled-quota-zero-cap",
        "disabled-quota-zero-cap",
        "capacity-retry-equal-backoff-bounds",
    ],
)
def test_valid_runner_configurations_round_trip(overrides: dict[str, object]) -> None:
    # Given
    config = configuration(**overrides)

    # When
    restored = HarnessConfig.model_validate_json(config.model_dump_json())

    # Then
    assert restored == config


def test_nondefault_runner_configuration_round_trips() -> None:
    # Given
    config = configuration(
        quiet=True,
        progress_interval_seconds=2.5,
        retry_limit=2,
        retry_nonzero_exit=True,
        quota_wait_enabled=True,
        quota_wait_limit_seconds=120.0,
        quota_poll_interval_seconds=7.5,
        quota_probe_budget=4,
        capacity_retry_limit=2,
        capacity_backoff_base_seconds=0.5,
        capacity_backoff_cap_seconds=4.0,
    )

    # When
    restored = HarnessConfig.model_validate_json(config.model_dump_json())

    # Then
    assert restored == config


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("progress_interval_seconds", 0.0),
        ("progress_interval_seconds", float("inf")),
        ("quota_wait_limit_seconds", float("nan")),
        ("quota_poll_interval_seconds", 0.0),
        ("quota_probe_budget", -1),
        ("capacity_retry_limit", -1),
        ("capacity_backoff_base_seconds", 0.0),
        ("capacity_backoff_cap_seconds", float("inf")),
    ],
    ids=[
        "zero-progress-interval",
        "infinite-progress-interval",
        "nan-quota-wait-limit",
        "zero-poll-interval",
        "negative-probe-budget",
        "negative-capacity-retry-limit",
        "zero-capacity-base",
        "infinite-capacity-cap",
    ],
)
def test_runner_configuration_rejects_invalid_scalar_bounds(
    field: str, value: object
) -> None:
    # Given
    invalid_value = {field: value}

    # When
    with pytest.raises(ValidationError) as error:
        configuration(**invalid_value)

    # Then
    assert error.value.errors()[0]["loc"] == (field,)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        (
            {
                "capacity_retry_limit": 1,
                "capacity_backoff_base_seconds": 1.0,
            },
            "capacity retries require backoff base and cap durations",
        ),
        (
            {
                "capacity_retry_limit": 1,
                "capacity_backoff_cap_seconds": 1.0,
            },
            "capacity retries require backoff base and cap durations",
        ),
        (
            {
                "capacity_backoff_base_seconds": 2.0,
                "capacity_backoff_cap_seconds": 1.0,
            },
            "capacity backoff cap must be at least its base",
        ),
    ],
    ids=[
        "capacity-cap-required",
        "capacity-base-required",
        "cap-below-base",
    ],
)
def test_runner_configuration_enforces_cross_field_contracts(
    overrides: dict[str, object], message: str
) -> None:
    # Given
    invalid_settings = overrides

    # When
    with pytest.raises(ValidationError, match=message) as error:
        configuration(**invalid_settings)

    # Then
    assert error.value.errors()[0]["loc"] == ()


def test_shared_runner_values_are_frozen() -> None:
    # Given
    binding = CliBinding(
        executable_path=Path("/usr/bin/codex"),
        cli_version=None,
        runner_version="1",
        effective_settings=(),
        quota_scope=None,
    )
    counts = ProgressCounts(
        calls_queued=1,
        calls_stopped_not_started=0,
        calls_active=0,
        calls_retry_wait=0,
        calls_evidence_pending=0,
        calls_succeeded=0,
        calls_failed=0,
        calls_cancelled=0,
        attempts_started=0,
        retries_started=0,
        attempts_active=0,
        attempts_evidence_pending=0,
        attempts_succeeded=0,
        attempts_failed=0,
        attempts_cancelled=0,
        probes_started=0,
        probes_active=0,
        probes_evidence_pending=0,
        probes_completed=0,
        probes_failed=0,
        probes_cancelled=0,
    )

    # When
    with pytest.raises(FrozenInstanceError):
        set_field(binding, "runner_version", "2")
    with pytest.raises(FrozenInstanceError):
        set_field(counts, "calls_queued", 0)

    # Then
    assert binding.runner_version == "1"
    assert counts.calls_queued == 1
