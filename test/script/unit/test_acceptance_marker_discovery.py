# SPDX-License-Identifier: Apache-2.0
"""Check static discovery of supported and rejected Work marker declarations."""

from pathlib import Path
import shutil
from typing import Literal

import pytest

from test.script.acceptance_support import ROOT
from test.script.acceptance_support import acceptance_coverage as acceptance_coverage

FIXTURE_DIR = ROOT / "test" / "script" / "fixtures"
type MarkerFixtureName = Literal[
    "acceptance_markers_fenced_other_work.py",
    "acceptance_markers_candidate_scope.py",
    "acceptance_markers_unknown_criterion.py",
    "acceptance_markers_dynamic_criterion.py",
]


def write_work(root: Path, content: str) -> str:
    """Create the temporary Work README and return its repository-relative path."""
    contract = root / "doc" / "example" / "README.md"
    contract.parent.mkdir(parents=True, exist_ok=True)
    contract.write_text(content, encoding="utf-8")
    return "doc/example/README.md"


def copy_marker_fixture(root: Path, fixture: MarkerFixtureName) -> Path:
    """Copy a named marker source unchanged into the checker's test root."""
    tests = root / "test"
    tests.mkdir(parents=True, exist_ok=True)
    marker_source = tests / "test_markers.py"
    shutil.copyfile(FIXTURE_DIR / fixture, marker_source)
    return marker_source


@pytest.mark.covers(
    work=(
        "doc/feat/reviewable-workflow-v2/trial-preparation/"
        "workflow-efficiency/verification-plan/README.md"
    ),
    ac="AC-4",
)
@pytest.mark.covers(
    work=("doc/feat/testing-conformance/scripts/acceptance/marker-discovery/README.md"),
    ac="AC-1",
)
def test_discovery_ignores_fenced_and_other_work_markers(tmp_path: Path) -> None:
    """Ignore a fenced AC example and a source marker for a different Work."""
    # Given
    work = write_work(
        tmp_path,
        "# Work\n\n"
        "- **AC-1 DONE** Output remains stable.\n"
        "- **AC-2 TODO** A later behavior.\n\n"
        "```markdown\n"
        "- **AC-99 DONE** This is only an example.\n"
        "```\n",
    )
    copy_marker_fixture(tmp_path, "acceptance_markers_fenced_other_work.py")

    # When
    errors, reports = acceptance_coverage.check_work(tmp_path, work)

    # Then
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
@pytest.mark.covers(
    work=("doc/feat/testing-conformance/scripts/acceptance/marker-discovery/README.md"),
    ac="AC-1",
)
def test_discovery_counts_only_supported_decorated_candidates(tmp_path: Path) -> None:
    """Count a direct test marker while ignoring assignments, helpers, and calls."""
    # Given
    work = write_work(
        tmp_path,
        "# Work\n\n"
        "- **AC-1 DONE** A collected test covers this.\n"
        "- **AC-2 TODO** Helpers and ordinary calls add no declarations.\n",
    )
    copy_marker_fixture(tmp_path, "acceptance_markers_candidate_scope.py")

    # When
    errors, reports = acceptance_coverage.check_work(tmp_path, work)

    # Then
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
@pytest.mark.covers(
    work=("doc/feat/testing-conformance/scripts/acceptance/marker-discovery/README.md"),
    ac="AC-1",
)
def test_discovery_rejects_unknown_marker_criterion(tmp_path: Path) -> None:
    """Reject a marker for an undeclared criterion with its exact diagnostic."""
    # Given
    work = write_work(tmp_path, "# Work\n\n- **AC-1 TODO** Output is stable.\n")
    copy_marker_fixture(tmp_path, "acceptance_markers_unknown_criterion.py")

    # When
    errors, reports = acceptance_coverage.check_work(tmp_path, work)

    # Then
    assert errors == [
        "doc/example/README.md: marker refers to undeclared criterion AC-9"
    ]
    assert reports == ["AC-1 TODO: no test marker or Validation method declared"]


@pytest.mark.covers(
    work=(
        "doc/feat/reviewable-workflow-v2/trial-preparation/"
        "workflow-efficiency/verification-plan/README.md"
    ),
    ac="AC-4",
)
@pytest.mark.covers(
    work=("doc/feat/testing-conformance/scripts/acceptance/marker-discovery/README.md"),
    ac="AC-1",
)
def test_discovery_rejects_dynamic_selected_criterion(tmp_path: Path) -> None:
    """Reject a selected marker with a dynamic criterion ID precisely."""
    # Given
    work = write_work(tmp_path, "# Work\n\n- **AC-1 TODO** Output is stable.\n")
    copy_marker_fixture(tmp_path, "acceptance_markers_dynamic_criterion.py")

    # When
    errors, reports = acceptance_coverage.check_work(tmp_path, work)

    # Then
    assert errors == [
        "test/test_markers.py:9: selected covers marker needs literal work "
        "and ac strings"
    ]
    assert reports == ["AC-1 TODO: no test marker or Validation method declared"]
