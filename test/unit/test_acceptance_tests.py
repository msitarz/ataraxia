# SPDX-License-Identifier: Apache-2.0
"""Test input validation for acceptance test targets."""

import importlib.util
from pathlib import Path
import sys
from unittest.mock import patch

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "script" / "acceptance_tests.py"
SPEC = importlib.util.spec_from_file_location("acceptance_tests", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
acceptance_tests = importlib.util.module_from_spec(SPEC)
with patch.object(sys, "path", [str(SCRIPT.parent), *sys.path]):
    SPEC.loader.exec_module(acceptance_tests)


def make_work_fixture(root: Path) -> str:
    """Create an isolated owning README and return its root-relative path."""
    work_file = root / "work" / "README.md"
    work_file.parent.mkdir(parents=True)
    work_file.write_text("# Temporary test Work\n", encoding="utf-8")
    (root / "test").mkdir()
    (root / "example").mkdir()
    return work_file.relative_to(root).as_posix()


@pytest.mark.parametrize(
    ("action", "ac", "expected"),
    [
        ("collect", "", "covers(work='work/README.md')"),
        ("test", "AC-8", "covers(work='work/README.md', ac='AC-8')"),
    ],
)
def test_build_command_scopes_work_and_optional_criterion(
    tmp_path, action, ac, expected
):
    work = make_work_fixture(tmp_path)

    with patch.object(acceptance_tests, "ROOT", tmp_path):
        command = acceptance_tests.build_command(action, work, ac)

    assert command[:4] == [sys.executable, "-m", "pytest", "-q"]
    assert command[-2:] == ["-m", expected]
    assert "test" in command and "example" in command
    assert ("--collect-only" in command) is (action == "collect")


@pytest.mark.parametrize(
    ("work", "ac", "message"),
    [
        ("", "", "WORK is required"),
        ("../README.md", "", "repo-relative"),
        ("/tmp/README.md", "", "repo-relative"),
        ("work.txt", "", "README.md or spec.md"),
        ("absent/README.md", "", "existing repository file"),
    ],
)
def test_invalid_inputs_are_rejected(tmp_path, work, ac, message):
    with (
        patch.object(acceptance_tests, "ROOT", tmp_path),
        pytest.raises(ValueError, match=message),
    ):
        acceptance_tests.build_command("test", work, ac)


def test_invalid_criterion_is_rejected_for_a_temporary_work(tmp_path):
    work = make_work_fixture(tmp_path)

    with (
        patch.object(acceptance_tests, "ROOT", tmp_path),
        pytest.raises(ValueError, match="criterion ID"),
    ):
        acceptance_tests.build_command("test", work, "AC-0")


def test_main_reports_missing_work_clearly(capsys):
    with (
        patch.object(sys, "argv", [str(SCRIPT), "collect"]),
        patch.dict(acceptance_tests.os.environ, {"WORK": ""}),
    ):
        result = acceptance_tests.main()

    assert result == 2
    assert "WORK is required" in capsys.readouterr().err


@pytest.mark.parametrize(
    "output",
    [
        "no tests collected (2 deselected)\n",
        "2 deselected in 0.04s\n",
        "no tests ran in 0.04s\n",
    ],
)
def test_empty_pytest_summaries_are_recognized(output):
    assert acceptance_tests.has_no_selected_tests(output)


def test_summary_with_a_selected_test_is_not_empty():
    assert not acceptance_tests.has_no_selected_tests(
        "1 passed, 2 deselected in 0.04s\n"
    )
