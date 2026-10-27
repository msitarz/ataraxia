# SPDX-License-Identifier: Apache-2.0
"""Pure runner policy calculations and their boundaries."""

from pathlib import Path

import pytest

from script.eval.model import (
    DirectoryOption,
    HarnessConfig,
    NoResultBasis,
    RetryAssessment,
    RetryClass,
)
from script.eval.runner.policy import (
    capacity_jitter_bound,
    capacity_retry_allowed,
    confident_no_result,
    infrastructure_retry_allowed,
    quota_poll_delay,
    quota_probe_allowed,
    quota_wait_remaining,
)


def configuration(**overrides: object) -> HarnessConfig:
    """Build a minimal valid config with selected policy settings."""
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


def assessment(
    retry_class: RetryClass, no_result_basis: NoResultBasis = "confident_absence"
) -> RetryAssessment:
    """Create a classifier result without deriving it from answer content."""
    return RetryAssessment(
        retry_class=retry_class,
        classification_basis="controlled classification",
        no_result_basis=no_result_basis,
        diagnostic=None,
    )


@pytest.mark.parametrize(
    ("basis", "expected"),
    [("confident_absence", True), ("present_or_unknown", False)],
    ids=["explicit-absence", "semantic-result-or-unknown"],
)
def test_confident_no_result_requires_explicit_absence(
    basis: NoResultBasis, expected: bool
) -> None:
    # Given
    result = assessment("unknown", basis)

    # When
    allowed = confident_no_result(result)

    # Then
    assert allowed is expected


@pytest.mark.parametrize(
    ("category", "limit", "used", "basis", "expected"),
    [
        ("infrastructure", 0, 0, "confident_absence", False),
        ("infrastructure", 2, 0, "confident_absence", True),
        ("infrastructure", 2, 2, "confident_absence", False),
        ("infrastructure", 2, 3, "confident_absence", False),
        ("capacity", 2, 0, "confident_absence", False),
        ("unknown", 2, 0, "confident_absence", False),
        ("infrastructure", 2, 0, "present_or_unknown", False),
    ],
    ids=[
        "default-zero-limit",
        "under-infrastructure-limit",
        "at-infrastructure-limit",
        "past-infrastructure-limit",
        "capacity-is-separate-category",
        "unknown-class-refused",
        "semantic-result-or-unknown-refused",
    ],
)
def test_infrastructure_retry_uses_its_category_and_limit(
    category: RetryClass,
    limit: int,
    used: int,
    basis: NoResultBasis,
    expected: bool,
) -> None:
    # Given
    config = configuration(retry_limit=limit)
    result = assessment(category, basis)

    # When
    allowed = infrastructure_retry_allowed(result, used, config)

    # Then
    assert allowed is expected


@pytest.mark.parametrize(
    ("category", "limit", "used", "basis", "expected"),
    [
        ("capacity", 0, 0, "confident_absence", False),
        ("capacity", 1, 0, "confident_absence", True),
        ("capacity", 1, 1, "confident_absence", False),
        ("capacity", 1, 2, "confident_absence", False),
        ("infrastructure", 1, 0, "confident_absence", False),
        ("unknown", 1, 0, "confident_absence", False),
        ("capacity", 1, 0, "present_or_unknown", False),
    ],
    ids=[
        "default-zero-limit",
        "under-capacity-limit",
        "at-capacity-limit",
        "past-capacity-limit",
        "infrastructure-is-separate-category",
        "unknown-class-refused",
        "semantic-result-or-unknown-refused",
    ],
)
def test_capacity_retry_uses_its_category_and_limit(
    category: RetryClass,
    limit: int,
    used: int,
    basis: NoResultBasis,
    expected: bool,
) -> None:
    # Given
    config = configuration(
        capacity_retry_limit=limit,
        capacity_backoff_base_seconds=0.5,
        capacity_backoff_cap_seconds=1.0,
    )
    result = assessment(category, basis)

    # When
    allowed = capacity_retry_allowed(result, used, config)

    # Then
    assert allowed is expected


@pytest.mark.parametrize(
    ("index", "base", "cap", "expected"),
    [
        (0, 0.5, 4.0, 0.5),
        (1, 0.5, 4.0, 1.0),
        (3, 0.5, 4.0, 4.0),
        (100_000, 0.5, 4.0, 4.0),
        (100_000, 4.0, 4.0, 4.0),
        (3, 0.1, 0.7, 0.7),
        (10**100, 5e-324, 1.0, 1.0),
    ],
    ids=[
        "first-bound",
        "second-bound-below-cap",
        "equal-cap",
        "saturates-before-overflow",
        "equal-base-cap",
        "cap-not-power-of-two",
        "huge-index-from-subnormal-base",
    ],
)
def test_capacity_jitter_bound_saturates_exponential_growth(
    index: int, base: float, cap: float, expected: float
) -> None:
    # Given
    bounds = index, base, cap

    # When
    bound = capacity_jitter_bound(*bounds)

    # Then
    assert bound == expected


@pytest.mark.parametrize(
    ("enabled", "limit", "waited", "expected"),
    [
        (False, None, 0.0, 0.0),
        (True, None, 400.0, None),
        (True, 10.0, 0.0, 10.0),
        (True, 10.0, 7.5, 2.5),
        (True, 10.0, 10.0, 0.0),
        (True, 10.0, 12.0, 0.0),
    ],
    ids=[
        "disabled",
        "enabled-unbounded",
        "at-start",
        "remaining-duration",
        "at-bound",
        "past-bound",
    ],
)
def test_quota_wait_remaining_respects_opt_in_and_optional_bound(
    enabled: bool, limit: float | None, waited: float, expected: float | None
) -> None:
    # Given
    config = configuration(quota_wait_enabled=enabled, quota_wait_limit_seconds=limit)

    # When
    remaining = quota_wait_remaining(config, waited)

    # Then
    assert remaining == expected


@pytest.mark.parametrize(
    ("enabled", "budget", "used", "expected"),
    [
        (False, None, 0, False),
        (True, None, 20, True),
        (True, 2, 1, True),
        (True, 2, 2, False),
        (True, 2, 3, False),
    ],
    ids=[
        "default-no-opt-in",
        "enabled-no-count-cap",
        "under-finite-cap",
        "at-finite-cap",
        "past-finite-cap",
    ],
)
def test_quota_probe_requires_opt_in_and_respects_optional_cap(
    enabled: bool, budget: int | None, used: int, expected: bool
) -> None:
    # Given
    config = configuration(quota_wait_enabled=enabled, quota_probe_budget=budget)

    # When
    allowed = quota_probe_allowed(config, used)

    # Then
    assert allowed is expected


@pytest.mark.parametrize(
    ("now", "hint", "expected"),
    [
        ("2030-01-01T00:00:00Z", None, 60.0),
        ("2030-01-01T00:00:00Z", "2029-12-31T23:59:00Z", 60.0),
        ("2030-01-01T00:00:00Z", "2030-01-01T00:00:00Z", 60.0),
        ("2030-01-01T00:00:00Z", "2030-01-01T00:00:20Z", 20.0),
        ("2030-01-01T00:00:00Z", "2030-01-01T00:02:00Z", 60.0),
        ("2030-01-01T00:00:00Z", "2030-01-01T00:00:00.000001Z", 0.000001),
    ],
    ids=[
        "missing-hint",
        "stale-hint",
        "past-or-now-hint",
        "earlier-future-hint",
        "interval-first",
        "fractional-second-hint",
    ],
)
def test_quota_poll_delay_uses_earlier_positive_reset_hint_or_interval(
    now: str, hint: str | None, expected: float
) -> None:
    # Given
    interval = 60.0

    # When
    delay = quota_poll_delay(interval, now, hint)

    # Then
    assert delay == expected
