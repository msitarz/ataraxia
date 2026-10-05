# SPDX-License-Identifier: Apache-2.0
"""Check static Work acceptance declarations."""

import importlib.util
from pathlib import Path
import sys
from unittest.mock import patch

import pytest

SCRIPT = Path(__file__).resolve().parents[3] / "script" / "acceptance_coverage.py"
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


@pytest.mark.covers(
    work=(
        "doc/feat/reviewable-workflow-v2/trial-preparation/"
        "workflow-efficiency/verification-plan/README.md"
    ),
    ac="AC-4",
)
def test_check_work_ignores_fenced_examples_and_other_work_markers(tmp_path):
    """`ac-check` validates AC declarations, `Validation:` annotations, and literal
    marker references without requiring markers or `Validation:` based on TODO/DONE
    status; neutral summaries do not claim coverage or completion."""
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
        "AC-1 DONE: 1 test marker(s) declared",
        "AC-2 TODO: no test marker or Validation method declared",
    ]


@pytest.mark.covers(
    work=(
        "doc/feat/reviewable-workflow-v2/trial-preparation/"
        "workflow-efficiency/verification-plan/README.md"
    ),
    ac="AC-4",
)
def test_only_decorated_static_test_candidates_are_reported(tmp_path):
    """`ac-check` validates AC declarations, `Validation:` annotations, and literal
    marker references without requiring markers or `Validation:` based on TODO/DONE
    status; neutral summaries do not claim coverage or completion."""
    work = write_work(
        tmp_path,
        "# Work\n\n"
        "- **AC-1 DONE** A collected test covers this.\n"
        "- **AC-2 TODO** Helpers and ordinary calls do not add declarations.\n",
    )
    write_tests(
        tmp_path,
        "import pytest\n\n"
        f"unused = pytest.mark.covers(work={work!r}, ac='AC-2')\n\n"
        f"@pytest.mark.covers(work={work!r}, ac='AC-2')\n"
        "def helper():\n    pass\n\n"
        "def test_body_call_is_not_a_decorator():\n"
        f"    pytest.mark.covers(work={work!r}, ac='AC-2')\n\n"
        "class TestHelpers:\n"
        f"    @pytest.mark.covers(work={work!r}, ac='AC-2')\n"
        "    def helper(self):\n        pass\n\n"
        f"@pytest.mark.covers(work={work!r}, ac='AC-1')\n"
        "def test_supported_candidate():\n    pass\n",
    )

    errors, reports = check_work(tmp_path, work)

    assert reports == [
        "AC-1 DONE: 1 test marker(s) declared",
        "AC-2 TODO: no test marker or Validation method declared",
    ]
    assert errors == []


@pytest.mark.parametrize(
    ("status", "has_validation", "has_marker"),
    [
        (status, has_validation, has_marker)
        for status in ("TODO", "DONE")
        for has_validation in (False, True)
        for has_marker in (False, True)
    ],
)
@pytest.mark.covers(
    work=(
        "doc/feat/reviewable-workflow-v2/trial-preparation/"
        "workflow-efficiency/verification-plan/README.md"
    ),
    ac="AC-4",
)
def test_declaration_reports_do_not_require_status_or_method(
    tmp_path, status, has_validation, has_marker
):
    """`ac-check` validates AC declarations, `Validation:` annotations, and literal
    marker references without requiring markers or `Validation:` based on TODO/DONE
    status; neutral summaries do not claim coverage or completion."""
    validation = (
        "  Validation: compare generated output with the fixture.\n"
        if has_validation
        else ""
    )
    work = write_work(
        tmp_path,
        f"# Work\n\n- **AC-1 {status}** Output remains stable.\n{validation}",
    )
    if has_marker:
        write_tests(
            tmp_path,
            "import pytest\n"
            f"@pytest.mark.covers(work={work!r}, ac='AC-1')\n"
            "def test_output_remains_stable():\n    pass\n",
        )

    errors, reports = check_work(tmp_path, work)

    if has_marker:
        declaration = "1 test marker(s) declared"
    elif has_validation:
        declaration = "Validation method declared"
    else:
        declaration = "no test marker or Validation method declared"
    assert errors == []
    assert reports == [f"AC-1 {status}: {declaration}"]


@pytest.mark.covers(
    work=(
        "doc/feat/reviewable-workflow-v2/trial-preparation/"
        "workflow-efficiency/verification-plan/README.md"
    ),
    ac="AC-4",
)
def test_unknown_marker_reference_fails_with_work_and_ac(tmp_path):
    """`ac-check` validates AC declarations, `Validation:` annotations, and literal
    marker references without requiring markers or `Validation:` based on TODO/DONE
    status; neutral summaries do not claim coverage or completion."""
    work = write_work(tmp_path, "# Work\n\n- **AC-1 TODO** Output is stable.\n")
    write_tests(
        tmp_path,
        "import pytest\n"
        f"@pytest.mark.covers(work={work!r}, ac='AC-9')\n"
        "def test_unknown_criterion():\n    pass\n",
    )

    errors, _ = check_work(tmp_path, work)

    assert errors == [f"{work}: marker refers to undeclared criterion AC-9"]


@pytest.mark.covers(
    work=(
        "doc/feat/reviewable-workflow-v2/trial-preparation/"
        "workflow-efficiency/verification-plan/README.md"
    ),
    ac="AC-4",
)
def test_selected_marker_with_dynamic_ac_fails_clearly(tmp_path):
    """`ac-check` validates AC declarations, `Validation:` annotations, and literal
    marker references without requiring markers or `Validation:` based on TODO/DONE
    status; neutral summaries do not claim coverage or completion."""
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


@pytest.mark.covers(
    work=(
        "doc/feat/reviewable-workflow-v2/trial-preparation/"
        "workflow-efficiency/verification-plan/README.md"
    ),
    ac="AC-4",
)
def test_duplicate_and_malformed_criterion_declarations_are_reported():
    """`ac-check` validates AC declarations, `Validation:` annotations, and literal
    marker references without requiring markers or `Validation:` based on TODO/DONE
    status; neutral summaries do not claim coverage or completion."""
    criteria, errors = parse_criteria(
        "# Work\n"
        "- **AC-1 TODO** First criterion.\n"
        "- **AC-1 DONE** Duplicate criterion.\n"
        "- **AC-0 DONE** Invalid ID.\n"
        "- **AC1 DONE** Malformed ID syntax.\n"
        "- **AC-2 REVIEW** Invalid status.\n"
        "- **AC-3 TODO**   \n",
        "doc/example/README.md",
    )

    assert list(criteria) == ["AC-1", "AC-3"]
    assert any("duplicate criterion AC-1" in error for error in errors)
    assert any("malformed AC declaration" in error for error in errors)
    assert any("AC-3 needs criterion text" in error for error in errors)

    _, empty_errors = parse_criteria("# Empty Work\n", "doc/empty/README.md")
    assert "no AC declarations" in empty_errors[0]


@pytest.mark.covers(
    work=(
        "doc/feat/reviewable-workflow-v2/trial-preparation/"
        "workflow-efficiency/verification-plan/README.md"
    ),
    ac="AC-4",
)
def test_empty_and_duplicate_validation_annotations_are_rejected():
    """`ac-check` validates AC declarations, `Validation:` annotations, and literal
    marker references without requiring markers or `Validation:` based on TODO/DONE
    status; neutral summaries do not claim coverage or completion."""
    _, errors = parse_criteria(
        "# Work\n"
        "- **AC-1 TODO** Output.\n  Validation:\n"
        "- **AC-2 DONE** Output.\n"
        "  Validation: inspect the result.\n"
        "  Validation: compare the result.\n",
        "doc/example/README.md",
    )

    assert len(errors) == 2
    assert any("Validation annotation needs a method" in error for error in errors)
    assert any("multiple Validation annotations" in error for error in errors)


@pytest.mark.covers(
    work=(
        "doc/feat/reviewable-workflow-v2/trial-preparation/"
        "workflow-efficiency/verification-plan/README.md"
    ),
    ac="AC-4",
)
def test_outdented_validation_is_not_reported_as_declared(tmp_path):
    """`ac-check` validates AC declarations, `Validation:` annotations, and literal
    marker references without requiring markers or `Validation:` based on TODO/DONE
    status; neutral summaries do not claim coverage or completion."""
    work = write_work(
        tmp_path,
        "# Work\n"
        "- **AC-1 DONE** Output is stable.\n"
        "Validation: compare generated output with the committed fixture.\n",
    )
    errors, reports = check_work(tmp_path, work)

    assert errors == []
    assert reports == ["AC-1 DONE: no test marker or Validation method declared"]


def test_legacy_annotation_does_not_declare_validation():
    """Only the canonical Validation annotation declares a planned method."""
    criteria, errors = parse_criteria(
        "- **AC-1 TODO** Output stays stable.\n"
        "  Verification: inspect generated output.\n",
        "doc/example/README.md",
    )

    assert errors == []
    assert not criteria["AC-1"].has_validation
