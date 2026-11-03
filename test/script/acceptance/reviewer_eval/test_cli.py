# SPDX-License-Identifier: Apache-2.0
"""Command behavior for saved reviewer reports."""

import json
from pathlib import Path
import subprocess
import sys


def test_cli_creates_exclusive_report(saved_run: Path, tmp_path: Path) -> None:
    # Given
    output = tmp_path / "report.json"
    command = [
        sys.executable,
        "-m",
        "script.reviewer_eval",
        str(saved_run),
        "--output",
        str(output),
    ]

    # When
    first = subprocess.run(command, capture_output=True, timeout=10, check=False)
    before = output.read_bytes()
    second = subprocess.run(command, capture_output=True, timeout=10, check=False)

    # Then
    assert first.returncode == 0
    assert json.loads(before)["counts"]["complete"] == 1
    assert second.returncode == 1
    assert output.read_bytes() == before


def test_help_and_missing_plan_failure(tmp_path: Path) -> None:
    # Given
    root = tmp_path / "run"
    root.mkdir()
    output = tmp_path / "report.json"

    # When
    help_result = subprocess.run(
        [sys.executable, "-m", "script.reviewer_eval", "--help"],
        capture_output=True,
        timeout=10,
        check=False,
    )
    failed = subprocess.run(
        [
            sys.executable,
            "-m",
            "script.reviewer_eval",
            str(root),
            "--output",
            str(output),
        ],
        capture_output=True,
        timeout=10,
        check=False,
    )

    # Then
    assert help_result.returncode == 0
    assert b"original harness run directory" in help_result.stdout
    assert failed.returncode == 1
    assert json.loads(output.read_bytes())["planned_count"] is None
