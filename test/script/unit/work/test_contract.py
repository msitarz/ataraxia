# SPDX-License-Identifier: Apache-2.0
"""Exercise structural rules over validated repository-owned Markdown values."""

import pytest

from script.markdown.model import (
    ContainerBlock,
    HeadingBlock,
    MarkdownBlock,
    SourceLocation,
    TextBlock,
)
from script.work.contract import (
    WorkCriterion,
    WorkDiagnostic,
    WorkInspection,
    inspect_work,
)

UNICODE_ZERO_ID = "AC-" + chr(0x660)


def test_valid_work_inspection_retains_title_and_all_criterion_statuses() -> None:
    # Given
    blocks = _contract(
        _heading(10, "**AC-01 TODO** First outcome", 3),
        _text(11, "First body."),
        _heading(12, "**AC-2 DONE** Second outcome", 3),
        _text(13, "Second body."),
        _heading(14, "**AC-3 ABORT** Stopped outcome", 3),
        _text(15, "Stopped with authorization."),
    )

    # When
    inspection = inspect_work(blocks)

    # Then
    assert inspection == WorkInspection(
        "Contract",
        (
            WorkCriterion("AC-1", "TODO"),
            WorkCriterion("AC-2", "DONE"),
            WorkCriterion("AC-3", "ABORT"),
        ),
        (),
    )


def test_malformed_work_inspection_keeps_valid_criteria_and_exact_findings() -> None:
    # Given
    blocks = _contract(
        _heading(10, "**AC-1 TODO** Valid outcome", 3),
        _text(11, "Valid body."),
        _heading(12, "**AC-2 WRONG** Invalid outcome", 3),
        _text(13, "Invalid body."),
    )

    # When
    inspection = inspect_work(blocks)

    # Then
    assert inspection == WorkInspection(
        "Contract",
        (WorkCriterion("AC-1", "TODO"),),
        (
            WorkDiagnostic(
                12,
                "supported status TODO, DONE, or ABORT",
                "**AC-2 WRONG** Invalid outcome",
            ),
        ),
    )


def test_valid_typed_blocks_keep_nested_explanations_inside_the_outcome() -> None:
    # Given
    blocks = _contract(
        _heading(10, "**AC-1 TODO** Outcome", 3),
        _text(11, "The outcome is delivered."),
        _heading(12, "Explanation", 4),
        _text(13, "More context."),
        TextBlock(SourceLocation(15, 18), "fenced_code", "## Purpose\n### AC-9"),
        TextBlock(
            SourceLocation(20, 22),
            "html_block",
            "<!--\n## Goals\n### **AC-8 DONE** Fake\n-->",
        ),
        ContainerBlock(
            SourceLocation(24, 25),
            "blockquote",
            (
                _heading(24, "Acceptance criteria", 2),
                _text(25, "Quoted content."),
            ),
        ),
    )

    # When
    findings = inspect_work(blocks).diagnostics

    # Then
    assert findings == ()


def test_missing_sections_report_complete_file_start_diagnostics() -> None:
    # Given
    blocks = (_heading(1, "Contract", 1),)

    # When
    findings = inspect_work(blocks).diagnostics

    # Then
    assert findings == (
        WorkDiagnostic(
            1, "required top-level section 'Acceptance criteria'", "file start"
        ),
        WorkDiagnostic(1, "required top-level section 'Goals'", "file start"),
        WorkDiagnostic(1, "required top-level section 'Purpose'", "file start"),
    )


def test_level_one_heading_ends_section_and_outcome_context() -> None:
    # Given
    blocks = _contract(
        _heading(10, "**AC-1 TODO** Result", 3),
        _heading(11, "Another Work", 1),
        _text(12, "Text after the new title."),
    )

    # When
    findings = inspect_work(blocks).diagnostics

    # Then
    assert findings == (
        WorkDiagnostic(
            9, "nonempty 'Acceptance criteria' section", "Acceptance criteria"
        ),
        WorkDiagnostic(10, "nonempty criterion outcome body", "**AC-1 TODO** Result"),
    )


def test_criterion_like_headings_outside_acceptance_and_at_wrong_levels_fail() -> None:
    # Given
    blocks = _contract(
        _heading(10, "**AC-1 TODO** Result", 3),
        _text(11, "Result body."),
        _heading(12, "**AC-7 TODO** Wrong title level", 1),
        _text(13, "Wrong-level title body."),
        _heading(14, "Another Work", 1),
        _heading(15, "**AC-9 TODO** Outside", 3),
        _text(16, "Outside body."),
        _heading(17, "**AC-10 TODO** Wrong level", 4),
        _text(18, "Wrong-level body."),
    )

    # When
    findings = inspect_work(blocks).diagnostics

    # Then
    assert findings == (
        WorkDiagnostic(
            12,
            "criterion declaration must use a level-three heading",
            "**AC-7 TODO** Wrong title level",
        ),
        WorkDiagnostic(
            12,
            "criterion must be inside Acceptance criteria",
            "**AC-7 TODO** Wrong title level",
        ),
        WorkDiagnostic(
            15, "criterion must be inside Acceptance criteria", "**AC-9 TODO** Outside"
        ),
        WorkDiagnostic(
            17,
            "criterion declaration must use a level-three heading",
            "**AC-10 TODO** Wrong level",
        ),
        WorkDiagnostic(
            17,
            "criterion must be inside Acceptance criteria",
            "**AC-10 TODO** Wrong level",
        ),
    )


def test_criterion_fields_and_empty_body_report_exact_locations_and_order() -> None:
    # Given
    blocks = _contract(
        _heading(10, "**AC-01 WRONG** First", 3),
        _text(11, "First body."),
        _heading(12, "**AC-1 TODO**", 3),
        TextBlock(SourceLocation(13, 13), "html_block", "<!-- only a comment -->"),
    )

    # When
    findings = inspect_work(blocks).diagnostics

    # Then
    assert findings == (
        WorkDiagnostic(
            10,
            "supported status TODO, DONE, or ABORT",
            "**AC-01 WRONG** First",
        ),
        WorkDiagnostic(12, "nonempty criterion name", "**AC-1 TODO**"),
        WorkDiagnostic(12, "nonempty criterion outcome body", "**AC-1 TODO**"),
        WorkDiagnostic(12, "unique criterion ID AC-1", "**AC-1 TODO**"),
    )


def test_explicitly_aborted_criterion_is_a_supported_stopped_outcome() -> None:
    # Given
    blocks = _contract(
        _heading(10, "**AC-1 ABORT** Stopped", 3),
        _text(11, "Stopped after maintainer confirmation."),
    )

    # When
    findings = inspect_work(blocks).diagnostics

    # Then
    assert findings == ()


@pytest.mark.parametrize(
    ("identifier", "expected"),
    [
        pytest.param(
            UNICODE_ZERO_ID,
            (
                WorkDiagnostic(
                    10,
                    "criterion heading format '### **AC-N STATUS** Outcome name'",
                    f"**{UNICODE_ZERO_ID} TODO** Outcome",
                ),
            ),
            id="unicode-zero",
        ),
        pytest.param(
            "AC-0",
            (
                WorkDiagnostic(
                    10,
                    "positive decimal criterion ID",
                    "**AC-0 TODO** Outcome",
                ),
            ),
            id="zero",
        ),
    ],
)
def test_non_ascii_or_nonpositive_ids_never_pass(
    identifier: str, expected: tuple[WorkDiagnostic, ...]
) -> None:
    # Given
    blocks = _contract(
        _heading(10, f"**{identifier} TODO** Outcome", 3),
        _text(11, "Body."),
    )

    # When
    findings = inspect_work(blocks).diagnostics

    # Then
    assert findings == expected


def test_duplicate_sections_and_empty_acceptance_body_are_located() -> None:
    # Given
    blocks = (
        _heading(1, "Contract", 1),
        _heading(3, "Purpose", 2),
        _text(4, "Why."),
        _heading(6, "Purpose", 2),
        _text(7, "Again."),
        _heading(9, "Goals", 2),
        _text(10, "Goal."),
        _heading(12, "Acceptance criteria", 2),
        _heading(13, "Links", 2),
        _text(14, "More information."),
    )

    # When
    findings = inspect_work(blocks).diagnostics

    # Then
    assert findings == (
        WorkDiagnostic(6, "duplicate top-level section 'Purpose'", "Purpose"),
        WorkDiagnostic(12, "at least one criterion declaration", "Acceptance criteria"),
        WorkDiagnostic(
            12, "nonempty 'Acceptance criteria' section", "Acceptance criteria"
        ),
    )


def _contract(*criterion_blocks: MarkdownBlock) -> tuple[MarkdownBlock, ...]:
    """Return a valid required-section prefix followed by supplied values."""
    return (
        _heading(1, "Contract", 1),
        _heading(3, "Purpose", 2),
        _text(4, "Why."),
        _heading(6, "Goals", 2),
        _text(7, "Goal."),
        _heading(9, "Acceptance criteria", 2),
        *criterion_blocks,
    )


def _heading(line: int, text: str, level: int) -> HeadingBlock:
    return HeadingBlock(SourceLocation(line, line), text, level)


def _text(line: int, text: str) -> TextBlock:
    return TextBlock(SourceLocation(line, line), "paragraph", text)
