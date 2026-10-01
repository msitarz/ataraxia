# SPDX-License-Identifier: Apache-2.0
"""Check static Work acceptance coverage declarations."""

import importlib.util
from pathlib import Path
import sys
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[2] / "script" / "acceptance_coverage.py"
SPEC = importlib.util.spec_from_file_location("acceptance_coverage", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
acceptance_coverage = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = acceptance_coverage
with patch.object(sys, "path", [str(SCRIPT.parent), *sys.path]):
    SPEC.loader.exec_module(acceptance_coverage)

check_work = acceptance_coverage.check_work
parse_criteria = acceptance_coverage.parse_criteria


def write_work(root: Path, content: str) -> str:
    """Create an owning Work contract and return its repository-relative path."""
    contract = root / "doc" / "example" / "README.md"
    contract.parent.mkdir(parents=True, exist_ok=True)
    contract.write_text(content, encoding="utf-8")
    return contract.relative_to(root).as_posix()


def write_tests(root: Path, content: str) -> None:
    """Create Python test sources under the checker's test root."""
    tests = root / "test"
    tests.mkdir(parents=True, exist_ok=True)
    (tests / "test_markers.py").write_text(content, encoding="utf-8")


def test_check_work_ignores_fenced_examples_and_other_work_markers(tmp_path):
    work = write_work(
        tmp_path,
        "# Work\n\n"
        "- **AC-1 DONE** Output stays stable.\n"
        "- **AC-2 TODO** A later behavior.\n\n"
        "```markdown\n"
        "- **AC-99 DONE** This is only an example.\n"
        "```\n",
    )
    write_tests(
        tmp_path,
        "import pytest\n\n"
        f"@pytest.mark.covers(work={work!r}, ac='AC-1')\n"
        "def test_output_stays_stable():\n    pass\n\n"
        "@pytest.mark.covers(work='doc/other/README.md', ac='AC-99')\n"
        "def test_other_work():\n    pass\n",
    )

    errors, reports = check_work(tmp_path, work)

    assert errors == []
    assert reports == [
        "AC-1 DONE: 1 test marker(s)",
        "AC-2 TODO: coverage missing",
    ]


def test_done_accepts_a_specific_non_test_verification(tmp_path):
    work = write_work(
        tmp_path,
        "# Work\n\n"
        "- **AC-1 DONE** Output matches the saved fixture.\n"
        "  Verification: compare generated output with the committed fixture.\n",
    )

    errors, reports = check_work(tmp_path, work)

    assert errors == []
    assert reports == ["AC-1 DONE: Verification method declared"]


def test_done_without_marker_or_method_fails_with_work_and_ac(tmp_path):
    work = write_work(tmp_path, "# Work\n\n- **AC-1 DONE** Output is stable.\n")

    errors, _ = check_work(tmp_path, work)

    assert len(errors) == 1
    assert f"{work}: AC-1 is DONE" in errors[0]


def test_unknown_marker_reference_fails_with_work_and_ac(tmp_path):
    work = write_work(tmp_path, "# Work\n\n- **AC-1 TODO** Output is stable.\n")
    write_tests(
        tmp_path,
        "import pytest\n"
        f"@pytest.mark.covers(work={work!r}, ac='AC-9')\n"
        "def test_unknown_criterion():\n    pass\n",
    )

    errors, _ = check_work(tmp_path, work)

    assert errors == [f"{work}: marker refers to undeclared criterion AC-9"]


def test_selected_marker_with_dynamic_ac_fails_clearly(tmp_path):
    work = write_work(tmp_path, "# Work\n\n- **AC-1 TODO** Output is stable.\n")
    write_tests(
        tmp_path,
        "import pytest\n"
        "criterion = 'AC-1'\n"
        f"@pytest.mark.covers(work={work!r}, ac=criterion)\n"
        "def test_dynamic_criterion():\n    pass\n",
    )

    errors, _ = check_work(tmp_path, work)

    assert len(errors) == 1
    assert "selected covers marker needs literal work and ac strings" in errors[0]


def test_duplicate_malformed_and_empty_declarations_are_reported():
    criteria, errors = parse_criteria(
        "# Work\n"
        "- **AC-1 TODO** First criterion.\n"
        "- **AC-1 DONE** Duplicate criterion.\n"
        "- **AC-0 DONE** Invalid ID.\n"
        "- **AC1 DONE** Malformed ID syntax.\n",
        "doc/example/README.md",
    )

    assert list(criteria) == ["AC-1"]
    assert any("duplicate criterion AC-1" in error for error in errors)
    assert any("malformed AC declaration" in error for error in errors)

    _, empty_errors = parse_criteria("# Empty Work\n", "doc/empty/README.md")
    assert "no AC declarations" in empty_errors[0]


def test_empty_verification_annotation_is_rejected():
    _, errors = parse_criteria(
        "# Work\n- **AC-1 DONE** Output.\n  Verification:\n",
        "doc/example/README.md",
    )

    assert len(errors) == 1
    assert "Verification annotation needs a method" in errors[0]
