# SPDX-License-Identifier: Apache-2.0
"""Private scoring with synthetic controls and classifications."""

from pathlib import Path

import pytest

from script.reviewer_eval.report import CallOutcome
from script.reviewer_eval.scoring import Control, _measures, read_reference
from script.reviewer_eval.validation import Assessment, PublicPair


@pytest.fixture
def controls() -> tuple[Control, ...]:
    """Return two synthetic controls."""
    return (
        Control(PublicPair("R1", "file", "good"), "PASS"),
        Control(PublicPair("R1", "file", "bad"), "VIOLATION"),
    )


def test_complete_call_scores_only_indexed_keys(controls: tuple[Control, ...]) -> None:
    """Given complete judgments, count matching labels and false positives."""
    call = CallOutcome(
        position=0,
        model="m",
        effort="e",
        state="complete",
        assessments=(
            Assessment(
                rule_id="R1",
                file_id="file",
                function_name="good",
                judgement="VIOLATION",
            ),
            Assessment(
                rule_id="R1", file_id="file", function_name="bad", judgement="VIOLATION"
            ),
            Assessment(
                rule_id="R1", file_id="file", function_name="other", judgement="PASS"
            ),
        ),
    )

    result = _measures(controls, ((controls, call),))

    assert (result.accuracy.numerator, result.accuracy.denominator) == (1, 2)
    assert result.violation_recall.value == 1
    assert result.pass_false_positive_rate.value == 1
    assert result.unindexed_records == 1


def test_partial_call_has_coverage_but_no_credit(controls: tuple[Control, ...]) -> None:
    """Given a partial call, retain uncertainty without primary credit."""
    call = CallOutcome(
        position=0,
        model="m",
        effort="e",
        state="incomplete",
        assessments=(
            Assessment(
                rule_id="R1", file_id="file", function_name="good", judgement="UNKNOWN"
            ),
            Assessment(
                rule_id="R1",
                file_id="file",
                function_name="bad",
                judgement="NOT_APPLICABLE",
            ),
        ),
    )

    result = _measures(controls, ((controls, call),))

    assert result.accuracy.value == 0
    assert result.unknown == 1
    assert result.not_applicable == 1
    assert result.indexed_records == 2
    assert result.valid_only_accuracy.value is None
    assert result.excluded_opportunities == 2


def test_missing_call_keeps_fixed_denominator(controls: tuple[Control, ...]) -> None:
    """Given absent calls, preserve the controls as unobserved."""
    result = _measures(controls, ())

    assert result.accuracy.denominator == 2
    assert result.missing_records == 2
    assert result.correct_pass_rate.value == 0


def test_reference_without_table_is_rejected(tmp_path: Path) -> None:
    """Given an unrelated file, reject it before scoring."""
    reference = tmp_path / "reference.md"
    reference.write_text("# Synthetic\n")

    with pytest.raises(ValueError, match="control table"):
        read_reference(reference)


def _reference_text() -> str:
    files = ("r1/dispatch.py.txt", "r3/planning.py.txt", "r4/ledger.py.txt")
    rules = ("R1", "R3", "R4")
    digests = "\n".join(
        f"- `{name}`: `{'a' * 64}`"
        for name in (*files, "r1/rule.txt", "r3/rule.txt", "r4/rule.txt")
    )
    rows = "\n".join(
        f"| {rule} | `{file}` | f{index} | {label} | synthetic rationale |"
        for rule, file in zip(rules, files, strict=True)
        for label, start in (("PASS", 0), ("VIOLATION", 4))
        for index in range(start, start + 4)
    )
    return (
        f"# Draft\n{digests}\n"
        "| Rule | File | Function | Expected | Source-grounded rationale |\n"
        f"| --- | --- | --- | --- | --- |\n{rows}\n"
    )


def test_reference_parses_synthetic_initial_inventory(tmp_path: Path) -> None:
    """Given the initial Markdown format, retain its fixed controls."""
    reference = tmp_path / "reference.md"
    reference.write_text(_reference_text())

    parsed = read_reference(reference)

    assert len(parsed.controls) == 24
    assert len(parsed.source_digests) == 3
    assert len(parsed.rule_digests) == 3


def test_reference_rejects_duplicate_control(tmp_path: Path) -> None:
    """Given duplicated keys, reject the reference rather than double count."""
    reference = tmp_path / "reference.md"
    reference.write_text(_reference_text().replace("| f1 |", "| f0 |", 1))

    with pytest.raises(ValueError, match="duplicate reference control"):
        read_reference(reference)


def test_reference_rejects_missing_rule_digest(tmp_path: Path) -> None:
    """Given incomplete provenance, reject the reference."""
    reference = tmp_path / "reference.md"
    reference.write_text(
        _reference_text().replace(f"- `r1/rule.txt`: `{'a' * 64}`\n", "")
    )

    with pytest.raises(ValueError, match="digest inventory"):
        read_reference(reference)


@pytest.mark.parametrize("state", ["failed", "not_started"])
def test_unavailable_call_preserves_public_missing_coverage(
    controls: tuple[Control, ...], state: str
) -> None:
    """Given an unobserved call, its entire public inventory is missing."""
    call = CallOutcome.model_validate({
        "position": 0,
        "model": "m",
        "effort": "e",
        "state": state,
    })

    result = _measures(controls, ((controls, call),), public_expected=6)

    assert result.public_records == 0
    assert result.public_missing == 6
    assert result.public_coverage is not None
    assert result.public_coverage.value == 0
