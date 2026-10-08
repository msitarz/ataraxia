# SPDX-License-Identifier: Apache-2.0
"""Test input validation for acceptance test targets."""

import importlib.util
from pathlib import Path
import sys
from unittest.mock import patch

import pytest

SCRIPT = Path(__file__).resolve().parents[3] / "script" / "acceptance_tests.py"
SPEC = importlib.util.spec_from_file_location("acceptance_tests", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
acceptance_tests = importlib.util.module_from_spec(SPEC)
with patch.object(sys, "path", [str(SCRIPT.parent), *sys.path]):
    SPEC.loader.exec_module(acceptance_tests)


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
