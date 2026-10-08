# SPDX-License-Identifier: Apache-2.0
"""Test parsing malformed and noncanonical acceptance declarations."""

from pathlib import Path

import pytest

from test.script.acceptance_support import (
    acceptance_coverage as acceptance_coverage,
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
        "doc/feat/testing-conformance/scripts/acceptance/declaration-parsing/README.md"
    ),
    ac="AC-1",
)
def test_parser_reports_duplicate_malformed_and_empty_criteria() -> None:
    """Reject duplicate, malformed, and textless criteria with exact diagnostics."""
    # Given
    markdown = (
        "# Work\n"
        "- **AC-1 TODO** First criterion.\n"
        "- **AC-1 DONE** Duplicate criterion.\n"
        "- **AC-0 DONE** Invalid ID.\n"
        "- **AC1 DONE** Malformed ID syntax.\n"
        "- **AC-2 REVIEW** Invalid status.\n"
        "- **AC-3 TODO**   \n"
    )

    # When
    criteria, errors = acceptance_coverage.parse_criteria(
        markdown, "doc/example/README.md"
    )
    empty_criteria, empty_errors = acceptance_coverage.parse_criteria(
        "# Empty Work\n", "doc/empty/README.md"
    )

    # Then
    assert criteria == {
        "AC-1": acceptance_coverage.Criterion("TODO", False),
        "AC-3": acceptance_coverage.Criterion("TODO", False),
    }
    assert errors == [
        "doc/example/README.md:3: duplicate criterion AC-1",
        "doc/example/README.md:4: malformed AC declaration; expected "
        "'- **AC-N TODO|DONE** description'",
        "doc/example/README.md:5: malformed AC declaration; expected "
        "'- **AC-N TODO|DONE** description'",
        "doc/example/README.md:6: malformed AC declaration; expected "
        "'- **AC-N TODO|DONE** description'",
        "doc/example/README.md:7: AC-3 needs criterion text",
    ]
    assert empty_criteria == {}
    assert empty_errors == [
        "doc/empty/README.md: no AC declarations; expected one or more "
        "'- **AC-N TODO|DONE** description' list items"
    ]


@pytest.mark.covers(
    work=(
        "doc/feat/reviewable-workflow-v2/trial-preparation/"
        "workflow-efficiency/verification-plan/README.md"
    ),
    ac="AC-4",
)
@pytest.mark.covers(
    work=(
        "doc/feat/testing-conformance/scripts/acceptance/declaration-parsing/README.md"
    ),
    ac="AC-1",
)
def test_parser_rejects_empty_and_duplicate_validation_methods() -> None:
    """Reject empty and repeated Validation methods with exact diagnostics."""
    # Given
    markdown = (
        "# Work\n"
        "- **AC-1 TODO** Output.\n  Validation:\n"
        "- **AC-2 DONE** Output.\n"
        "  Validation: inspect the result.\n"
        "  Validation: compare the result.\n"
    )

    # When
    criteria, errors = acceptance_coverage.parse_criteria(
        markdown, "doc/example/README.md"
    )

    # Then
    assert criteria == {
        "AC-1": acceptance_coverage.Criterion("TODO", False),
        "AC-2": acceptance_coverage.Criterion("DONE", True),
    }
    assert errors == [
        "doc/example/README.md:2: AC-1 Validation annotation needs a method",
        "doc/example/README.md:4: AC-2 has multiple Validation annotations",
    ]


@pytest.mark.covers(
    work=(
        "doc/feat/reviewable-workflow-v2/trial-preparation/"
        "workflow-efficiency/verification-plan/README.md"
    ),
    ac="AC-4",
)
@pytest.mark.covers(
    work=(
        "doc/feat/testing-conformance/scripts/acceptance/declaration-parsing/README.md"
    ),
    ac="AC-1",
)
def test_check_work_ignores_outdented_validation_text(tmp_path: Path) -> None:
    """Ignore an outdented Validation line when reporting a temporary Work."""
    # Given
    work = "doc/example/README.md"
    contract = tmp_path / work
    contract.parent.mkdir(parents=True)
    contract.write_text(
        "# Work\n"
        "- **AC-1 DONE** Output is stable.\n"
        "Validation: compare generated output with the committed fixture.\n",
        encoding="utf-8",
    )

    # When
    errors, reports = acceptance_coverage.check_work(tmp_path, work)

    # Then
    assert errors == []
    assert reports == ["AC-1 DONE: no test marker or Validation method declared"]


@pytest.mark.covers(
    work=(
        "doc/feat/testing-conformance/scripts/acceptance/declaration-parsing/README.md"
    ),
    ac="AC-1",
)
def test_parser_does_not_treat_legacy_verification_as_validation() -> None:
    """Ignore legacy Verification text when detecting a declared method."""
    # Given
    markdown = (
        "- **AC-1 TODO** Output stays stable.\n"
        "  Verification: inspect generated output.\n"
    )

    # When
    criteria, errors = acceptance_coverage.parse_criteria(
        markdown, "doc/example/README.md"
    )

    # Then
    assert criteria == {
        "AC-1": acceptance_coverage.Criterion("TODO", False),
    }
    assert errors == []
