# SPDX-License-Identifier: Apache-2.0
"""Public argument parsing preserves matrix option order."""

from pathlib import Path

import pytest

from script.eval.model import DirectoryOption, SeparatorOption
from script.eval.options import parse_config


def test_options_preserve_order_across_other_flags() -> None:
    # Given
    argv = [
        "-d",
        "first",
        "-m",
        "a",
        "-s",
        r"\n",
        "-e",
        "low",
        "-d",
        "second",
        "-m",
        "a",
        "-n",
    ]

    # When
    config = parse_config(argv)

    # Then
    assert config.ordered_options == (
        DirectoryOption(position=0, path=Path("first")),
        SeparatorOption(position=1, value=r"\n"),
        DirectoryOption(position=2, path=Path("second")),
    )
    assert config.models == ("a", "a")
    assert config.efforts == ("low",)
    assert config.dry_run


@pytest.mark.parametrize(
    "extra",
    [["-s", "x"], ["-c", "0"], ["--capacity-retry-limit", "1"]],
    ids=["dangling-separator", "zero-concurrency", "missing-backoff"],
)
def test_invalid_arguments_are_rejected(extra: list[str]) -> None:
    # Given
    argv = ["-d", "context", "-m", "model", "-e", "low", "-n", *extra]

    # When
    with pytest.raises(SystemExit) as caught:
        parse_config(argv)

    # Then
    assert caught.value.code == 2


def test_custom_runner_options_are_forwarded_to_validated_config() -> None:
    # Given
    argv = [
        "-d",
        "context",
        "-m",
        "model",
        "-e",
        "high",
        "-e",
        "low",
        "-c",
        "3",
        "-o",
        "out",
        "-i",
        "instructions",
        "--quiet",
        "--timeout-seconds",
        "12.5",
        "--cleanup-timeout-seconds",
        "4",
        "--grace-seconds",
        "1",
        "--output-limit-bytes",
        "512",
        "--progress-interval-seconds",
        "2",
        "--retry-limit",
        "2",
        "--retry-nonzero-exit",
        "--wait-for-quota",
        "--quota-wait-limit-seconds",
        "50",
        "--quota-poll-interval-seconds",
        "7",
        "--quota-probe-budget",
        "4",
        "--capacity-retry-limit",
        "3",
        "--capacity-backoff-base-seconds",
        "2",
        "--capacity-backoff-cap-seconds",
        "9",
    ]

    # When
    config = parse_config(argv)

    # Then
    assert config.model_dump() == {
        "ordered_options": ({"position": 0, "path": Path("context")},),
        "models": ("model",),
        "efforts": ("high", "low"),
        "concurrency": 3,
        "output_directory": Path("out"),
        "dry_run": False,
        "timeout_seconds": 12.5,
        "cleanup_timeout_seconds": 4.0,
        "grace_seconds": 1.0,
        "output_limit_bytes": 512,
        "quiet": True,
        "progress_interval_seconds": 2.0,
        "retry_limit": 2,
        "retry_nonzero_exit": True,
        "quota_wait_enabled": True,
        "quota_wait_limit_seconds": 50.0,
        "quota_poll_interval_seconds": 7.0,
        "quota_probe_budget": 4,
        "capacity_retry_limit": 3,
        "capacity_backoff_base_seconds": 2.0,
        "capacity_backoff_cap_seconds": 9.0,
        "instructions_file_path": Path("instructions"),
    }
