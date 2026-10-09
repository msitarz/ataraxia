# SPDX-License-Identifier: Apache-2.0
"""Argument-only behavior of the public CLI entry point."""

from pathlib import Path
import sys

import pytest
from pytest import CaptureFixture, MonkeyPatch

from ataraxia.cli import main

USAGE = "usage: ataraxia [-h] -s SINK -d SHARDS_DIR [-o OUTPUT]\n"


def _run_main(
    argv: list[str],
    expected_code: int,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> tuple[str, str]:
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(SystemExit) as raised:
        main()

    assert raised.value.code == expected_code
    captured = capsys.readouterr()
    return captured.out, captured.err


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/cli/arguments/README.md",
    ac="AC-1",
)
def test_main_requires_sink_before_backtest(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    """Reports the required sink option before attempting backtest work."""
    # Given
    argv = ["ataraxia", "--shards-dir", str(tmp_path / "shards")]

    # When
    stdout, stderr = _run_main(argv, 2, monkeypatch, capsys)

    # Then
    assert stdout == ""
    assert stderr == USAGE + (
        "ataraxia: error: the following arguments are required: -s/--sink\n"
    )


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/cli/arguments/README.md",
    ac="AC-1",
)
def test_main_requires_shards_directory_before_backtest(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    """Reports the required shard option before attempting backtest work."""
    # Given
    argv = ["ataraxia", "--sink", str(tmp_path / "sink.py")]

    # When
    stdout, stderr = _run_main(argv, 2, monkeypatch, capsys)

    # Then
    assert stdout == ""
    assert stderr == USAGE + (
        "ataraxia: error: the following arguments are required: -d/--shards-dir\n"
    )


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/cli/arguments/README.md",
    ac="AC-1",
)
def test_main_rejects_unknown_option_before_backtest(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    """Rejects an unknown option despite otherwise complete valid-looking paths."""
    # Given
    argv = [
        "ataraxia",
        "--sink",
        str(tmp_path / "sink.py"),
        "--shards-dir",
        str(tmp_path / "shards"),
        "--mystery",
    ]

    # When
    stdout, stderr = _run_main(argv, 2, monkeypatch, capsys)

    # Then
    assert stdout == ""
    assert stderr == USAGE + "ataraxia: error: unrecognized arguments: --mystery\n"


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/cli/arguments/README.md",
    ac="AC-1",
)
def test_main_help_lists_supported_options(
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    """Shows all supported option forms and exits before backtest work."""
    # Given
    argv = ["ataraxia", "--help"]

    # When
    stdout, stderr = _run_main(argv, 0, monkeypatch, capsys)

    # Then
    assert stdout.startswith(USAGE)
    assert "-h, --help" in stdout
    assert "-s, --sink SINK" in stdout
    assert "-d, --shards-dir SHARDS_DIR" in stdout
    assert "-o, --output OUTPUT" in stdout
    assert stderr == ""
