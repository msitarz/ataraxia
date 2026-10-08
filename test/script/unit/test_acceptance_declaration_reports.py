# SPDX-License-Identifier: Apache-2.0
"""Check complete static reports across marker, method, and status combinations."""

from pathlib import Path
import shutil
from typing import Literal

import pytest

from test.script.acceptance_support import ROOT
from test.script.acceptance_support import acceptance_coverage as acceptance_coverage

MARKER_SOURCE = (
    ROOT / "test" / "script" / "fixtures" / "acceptance_report_marker_source.py"
)
type WorkPath = Literal["doc/example/README.md", "doc/other/README.md"]


def write_work(root: Path, work: WorkPath, content: str) -> str:
    """Create a temporary Work declaration and return its relative path."""
    contract = root / work
    contract.parent.mkdir(parents=True, exist_ok=True)
    contract.write_text(content, encoding="utf-8")
    return work


def copy_marker_source(root: Path) -> None:
    """Copy the named marker source unchanged into the checker test root."""
    tests = root / "test"
    tests.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(MARKER_SOURCE, tests / "test_marker_source.py")


@pytest.mark.parametrize(
    ("work", "content", "expected_reports"),
    [
        (
            "doc/example/README.md",
            "# Work\n\n- **AC-1 TODO** Output is stable.\n",
            ["AC-1 TODO: no test marker or Validation method declared"],
        ),
        (
            "doc/example/README.md",
            "# Work\n\n- **AC-1 DONE** Output is stable.\n",
            ["AC-1 DONE: no test marker or Validation method declared"],
        ),
        (
            "doc/example/README.md",
            "# Work\n\n- **AC-1 TODO** Output is stable.\n"
            "  Validation: compare the output with the fixture.\n",
            ["AC-1 TODO: Validation method declared"],
        ),
        (
            "doc/example/README.md",
            "# Work\n\n- **AC-1 DONE** Output is stable.\n"
            "  Validation: compare the output with the fixture.\n",
            ["AC-1 DONE: Validation method declared"],
        ),
        (
            "doc/other/README.md",
            "# Work\n\n- **AC-1 TODO** Output is stable.\n",
            ["AC-1 TODO: 1 test marker(s) declared"],
        ),
        (
            "doc/other/README.md",
            "# Work\n\n- **AC-1 DONE** Output is stable.\n",
            ["AC-1 DONE: 1 test marker(s) declared"],
        ),
        (
            "doc/other/README.md",
            "# Work\n\n- **AC-1 TODO** Output is stable.\n"
            "  Validation: compare the output with the fixture.\n",
            ["AC-1 TODO: 1 test marker(s) declared"],
        ),
        (
            "doc/other/README.md",
            "# Work\n\n- **AC-1 DONE** Output is stable.\n"
            "  Validation: compare the output with the fixture.\n",
            ["AC-1 DONE: 1 test marker(s) declared"],
        ),
    ],
    ids=[
        "todo-no-declarations",
        "done-no-declarations",
        "todo-method-only",
        "done-method-only",
        "todo-marker-only",
        "done-marker-only",
        "todo-marker-and-method",
        "done-marker-and-method",
    ],
)
@pytest.mark.covers(
    work=(
        "doc/feat/reviewable-workflow-v2/trial-preparation/"
        "workflow-efficiency/verification-plan/README.md"
    ),
    ac="AC-4",
)
@pytest.mark.covers(
    work=(
        "doc/feat/testing-conformance/scripts/acceptance/declaration-reports/README.md"
    ),
    ac="AC-1",
)
def test_reports_declarations_without_judging_status(
    tmp_path: Path,
    work: WorkPath,
    content: str,
    expected_reports: list[str],
) -> None:
    """Report the declared marker or method neutrally for either criterion status."""
    # Given
    relative_work = write_work(tmp_path, work, content)
    copy_marker_source(tmp_path)

    # When
    errors, reports = acceptance_coverage.check_work(tmp_path, relative_work)

    # Then
    assert errors == []
    assert reports == expected_reports
