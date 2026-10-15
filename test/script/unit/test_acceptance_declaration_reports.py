# SPDX-License-Identifier: Apache-2.0
"""Check static reports across method and status combinations."""

from pathlib import Path

import pytest

from test.script.acceptance_support import acceptance_coverage as acceptance_coverage


def write_work(root: Path, work: str, content: str) -> str:
    """Create a temporary Work declaration and return its relative path."""
    contract = root / work
    contract.parent.mkdir(parents=True, exist_ok=True)
    contract.write_text(content, encoding="utf-8")
    return work


@pytest.mark.parametrize(
    ("work", "content", "expected_reports"),
    [
        (
            "doc/example/README.md",
            "# Work\n\n- **AC-1 TODO** Output is stable.\n",
            ["AC-1 TODO: no Validation method declared"],
        ),
        (
            "doc/example/README.md",
            "# Work\n\n- **AC-1 DONE** Output is stable.\n",
            ["AC-1 DONE: no Validation method declared"],
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
    ],
    ids=[
        "todo-no-declarations",
        "done-no-declarations",
        "todo-method-only",
        "done-method-only",
    ],
)
def test_reports_declarations_without_judging_status(
    tmp_path: Path,
    work: str,
    content: str,
    expected_reports: list[str],
) -> None:
    """Report declared methods neutrally for either criterion status."""
    # Given
    relative_work = write_work(tmp_path, work, content)
    contract = tmp_path / relative_work
    work_bytes = content.encode("utf-8")
    assert contract.read_bytes() == work_bytes

    # When
    errors, reports = acceptance_coverage.check_work(tmp_path, relative_work)

    # Then
    assert errors == []
    assert reports == expected_reports
    assert contract.read_bytes() == work_bytes
