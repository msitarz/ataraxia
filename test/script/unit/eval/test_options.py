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
        "working_directory": None,
        "sandbox_mode": "read-only",
        "enable_tools": False,
    }


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (["-m", "model", "-e", "low", "-n"], "provide at least one -d/--directory"),
        (["-d", "context", "-e", "low", "-n"], "provide at least one -m/--model"),
        (["-d", "context", "-m", "model", "-n"], "provide at least one -e/--effort"),
        (
            ["-d", "context", "-m", "model", "-e", "low"],
            "execution requires -o/--output-directory",
        ),
        (
            ["-d", "context", "-m", "model", "-e", "low", "-n", "--concurency", "2"],
            "Did you mean --concurrency?",
        ),
        (["-d", "context", "-m"], "expected one argument"),
        (
            ["-d", "context", "-m", "model", "-e", "low", "-n", "-c", "no"],
            "-c/--concurrency requires a valid integer",
        ),
        (
            ["-d", "context", "-m", "model", "-e", "low", "-n", "-c", "0"],
            "--concurrency must be greater than 0",
        ),
        (
            [
                "-d",
                "context",
                "-m",
                "model",
                "-e",
                "low",
                "-n",
                "--timeout-seconds",
                "nan",
            ],
            "--timeout-seconds must be finite",
        ),
        (
            [
                "-d",
                "context",
                "-m",
                "model",
                "-e",
                "low",
                "-n",
                "--grace-seconds",
                "10",
            ],
            "--grace-seconds must be less than --cleanup-timeout-seconds",
        ),
        (
            [
                "-d",
                "context",
                "-m",
                "model",
                "-e",
                "low",
                "-n",
                "--capacity-retry-limit",
                "1",
            ],
            "--capacity-retry-limit requires --capacity-backoff-base-seconds",
        ),
        (
            [
                "-d",
                "context",
                "-m",
                "model",
                "-e",
                "low",
                "-n",
                "--quota-probe-budget",
                "-1",
            ],
            "--quota-probe-budget must be at least 0",
        ),
        (
            [
                "-d",
                "context",
                "-m",
                "model",
                "-e",
                "low",
                "-n",
                "--capacity-backoff-base-seconds",
                "2",
                "--capacity-backoff-cap-seconds",
                "1",
            ],
            (
                "--capacity-backoff-cap-seconds must be at least "
                "--capacity-backoff-base-seconds"
            ),
        ),
        (
            [
                "-d",
                "context",
                "-s",
                r"\q",
                "-d",
                "other",
                "-m",
                "model",
                "-e",
                "low",
                "-n",
            ],
            "-s/--separator supports only",
        ),
        (
            ["-d", "context", "-s", "x", "-m", "model", "-e", "low", "-n"],
            "place each -s/--separator between",
        ),
    ],
    ids=[
        "directory",
        "model",
        "effort",
        "output",
        "typo",
        "missing-value",
        "numeric",
        "bound",
        "finite",
        "grace",
        "capacity",
        "quota-budget",
        "capacity-cap",
        "escape",
        "separator",
    ],
)
def test_invalid_options_explain_how_to_fix(
    argv: list[str], message: str, capsys: pytest.CaptureFixture[str]
) -> None:
    # Given an invalid command line

    # When
    with pytest.raises(SystemExit) as caught:
        parse_config(argv)

    # Then
    captured = capsys.readouterr()
    assert caught.value.code == 2
    assert message in captured.err
    assert "Run with --help for all options." in captured.err
    assert "usage:" not in captured.err
    assert "input_value" not in captured.err
    assert captured.out == ""


@pytest.mark.parametrize("argument", ["", "   "], ids=["empty", "whitespace"])
def test_blank_unrecognized_argument_is_reported(
    argument: str, capsys: pytest.CaptureFixture[str]
) -> None:
    # Given an unexpected blank argument

    # When
    with pytest.raises(SystemExit) as caught:
        parse_config([argument])

    # Then
    captured = capsys.readouterr()
    assert caught.value.code == 2
    assert "remove the empty or whitespace argument" in captured.err
    assert "Did you mean" not in captured.err
    assert "Run with --help for all options." in captured.err
    assert captured.out == ""


def test_unrelated_option_has_no_suggestion(capsys: pytest.CaptureFixture[str]) -> None:
    # Given an unknown option with no close match
    argv = ["--xyzzy"]

    # When
    with pytest.raises(SystemExit) as caught:
        parse_config(argv)

    # Then
    captured = capsys.readouterr()
    assert caught.value.code == 2
    assert "unrecognized argument '--xyzzy'" in captured.err
    assert "Did you mean" not in captured.err
    assert "Run with --help for all options." in captured.err


def test_help_remains_available(capsys: pytest.CaptureFixture[str]) -> None:
    # Given a request for help

    # When
    with pytest.raises(SystemExit) as caught:
        parse_config(["--help"])

    # Then
    captured = capsys.readouterr()
    assert caught.value.code == 0
    assert "usage:" in captured.out
    assert "--directory" in captured.out
    assert captured.err == ""
