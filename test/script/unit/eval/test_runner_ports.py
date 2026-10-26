# SPDX-License-Identifier: Apache-2.0
"""Runtime configuration and immutable shared runner values."""

from dataclasses import FrozenInstanceError
from pathlib import Path

from pydantic import ValidationError
import pytest

from script.eval.model import DirectoryOption, HarnessConfig
from script.eval.runner import CliBinding, ProgressCounts


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
    return HarnessConfig(**values)  # type: ignore[arg-type]


def test_runner_configuration_defaults_are_stable_and_serialized() -> None:
    # Given
    config = configuration()

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
    serialized = config.model_dump()
    assert serialized["progress_interval_seconds"] == pytest.approx(1.0)
    assert serialized["quota_probe_budget"] is None
    assert serialized["capacity_retry_limit"] == 0
    assert HarnessConfig.model_validate_json(config.model_dump_json()) == config


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
    with pytest.raises(ValidationError):
        configuration(**{field: value})


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        (
            {"quota_wait_enabled": True, "quota_probe_budget": 0},
            "enabled quota waiting requires a positive probe budget",
        ),
        (
            {"capacity_retry_limit": 1},
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
    ids=["quota-budget-zero", "capacity-backoff-required", "cap-below-base"],
)
def test_runner_configuration_enforces_cross_field_contracts(
    overrides: dict[str, object], message: str
) -> None:
    with pytest.raises(ValidationError, match=message):
        configuration(**overrides)


def test_shared_runner_values_are_frozen() -> None:
    # Given
    binding = CliBinding(Path("/usr/bin/codex"), None, "1", (), None)
    counts = ProgressCounts(*([0] * 21))

    # Then
    with pytest.raises(FrozenInstanceError):
        binding.runner_version = "2"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        counts.calls_queued = 1  # type: ignore[misc]
