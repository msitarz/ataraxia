# SPDX-License-Identifier: Apache-2.0
"""Test safe construction and failure handling for acceptance test targets."""

import importlib.util
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "script" / "acceptance_tests.py"
SPEC = importlib.util.spec_from_file_location("acceptance_tests", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
acceptance_tests = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(acceptance_tests)

WORK = (
    "doc/feat/reviewable-workflow-v2/validation/docs-checks/"
    "acceptance-traceability/coverage-checker/README.md"
)


@pytest.mark.parametrize(
    ("action", "ac", "expected"),
    [
        (
            "collect",
            "",
            ["-m", f"covers(work='{WORK}')"],
        ),
        (
            "test",
            "AC-8",
            ["-m", f"covers(work='{WORK}', ac='AC-8')"],
        ),
    ],
)
def test_build_command_scopes_work_and_optional_criterion(action, ac, expected):
    command = acceptance_tests.build_command(action, WORK, ac)

    assert command[:4] == [sys.executable, "-m", "pytest", "-q"]
    assert command[-2:] == expected
    assert ("--collect-only" in command) is (action == "collect")


@pytest.mark.parametrize(
    ("work", "ac", "message"),
    [
        ("", "", "WORK is required"),
        ("../README.md", "", "repo-relative"),
        ("/tmp/README.md", "", "repo-relative"),
        ("Makefile", "", "README.md or spec.md"),
        ("doc/not-present/README.md", "", "existing repository file"),
        (WORK, "AC-0", "criterion ID"),
    ],
)
def test_invalid_inputs_fail_before_running_pytest(work, ac, message):
    with (
        patch.object(acceptance_tests.subprocess, "run") as run,
        pytest.raises(ValueError, match=message),
    ):
        acceptance_tests.build_command("test", work, ac)
    run.assert_not_called()


def test_no_matching_tests_preserves_pytest_failure_status(monkeypatch):
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "test"])
    monkeypatch.setenv("WORK", WORK)
    monkeypatch.setenv("AC", "AC-999")
    completed = subprocess.CompletedProcess([], 5)

    with patch.object(
        acceptance_tests.subprocess, "run", return_value=completed
    ) as run:
        result = acceptance_tests.main()

    assert result == 5
    assert "covers(work=" in run.call_args.args[0][-1]
    assert "ac='AC-999'" in run.call_args.args[0][-1]


def test_collect_only_no_match_becomes_pytest_no_tests_status(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "collect"])
    monkeypatch.setenv("WORK", WORK)
    completed = subprocess.CompletedProcess(
        [], 0, stdout="no tests collected (161 deselected)\n", stderr=""
    )

    with patch.object(acceptance_tests.subprocess, "run", return_value=completed):
        result = acceptance_tests.main()

    assert result == 5
    assert "no tests collected" in capsys.readouterr().out


def test_main_reports_missing_work_clearly(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "collect"])
    monkeypatch.delenv("WORK", raising=False)

    assert acceptance_tests.main() == 2
    assert "WORK is required" in capsys.readouterr().err
