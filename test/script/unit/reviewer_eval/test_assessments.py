# SPDX-License-Identifier: Apache-2.0
"""Public boundary of function assessment validation."""

import json

import pytest

from script.reviewer_eval.validation import (
    InvalidResponse,
    PublicPair,
    ValidatedAssessments,
    validate_assessments,
)

SOURCE = {"file.py": b"class C:\n async def f(self):\n  def inner(): pass\n"}
RULES = frozenset({"R1"})


def record(name: str, judgement: str = "PASS") -> dict[str, str]:
    """Build a public assessment for the synthetic source."""
    return {
        "rule_id": "R1",
        "file_id": "file.py",
        "function_name": name,
        "judgement": judgement,
    }


@pytest.mark.parametrize(
    "judgement",
    ["PASS", "VIOLATION", "UNKNOWN", "NOT_APPLICABLE"],
    ids=["pass", "violation", "unknown", "not-applicable"],
)
def test_all_labels_and_missing_pairs(judgement: str) -> None:
    # Given
    raw = json.dumps([record("C.f.inner", judgement)]).encode()

    # When
    result = validate_assessments(raw, allowed_rules=RULES, sources=SOURCE)

    # Then
    assert isinstance(result, ValidatedAssessments)
    assert result.assessments[0].judgement == judgement
    assert result.missing == (PublicPair("R1", "file.py", "C.f"),)


def test_complete_order_independent() -> None:
    # Given
    rows = [record("C.f"), record("C.f.inner", "UNKNOWN")]

    # When
    result = validate_assessments(
        json.dumps(rows[::-1]).encode(), allowed_rules=RULES, sources=SOURCE
    )

    # Then
    assert isinstance(result, ValidatedAssessments)
    assert result.complete


@pytest.mark.parametrize(
    "raw",
    [
        json.dumps([record("C.f"), record("C.f")]).encode(),
        json.dumps([record("C.f"), record("C.f", "VIOLATION")]).encode(),
        json.dumps([{**record("C.f"), "rule_id": "R3"}]).encode(),
        json.dumps([{**record("C.f"), "file_id": "foreign"}]).encode(),
        json.dumps([record("f")]).encode(),
        json.dumps([{**record("C.f"), "extra": "x"}]).encode(),
        json.dumps([{**record("C.f"), "judgement": 1}]).encode(),
        json.dumps([record("C.f", "MAYBE")]).encode(),
        b"{}",
    ],
    ids=[
        "duplicate",
        "conflicting-duplicate",
        "rule",
        "file",
        "function",
        "extra",
        "type",
        "label",
        "envelope",
    ],
)
def test_invalid_records(raw: bytes) -> None:
    # Given
    source = SOURCE

    # When
    result = validate_assessments(raw, allowed_rules=RULES, sources=source)

    # Then
    assert isinstance(result, InvalidResponse)


def test_ambiguous_source_is_invalid_even_for_empty_response() -> None:
    # Given
    source = {"file.py": b"def f(): pass\ndef f(): pass\n"}

    # When
    result = validate_assessments(b"[]", allowed_rules=RULES, sources=source)

    # Then
    assert isinstance(result, InvalidResponse)
    assert "ambiguous" in result.diagnostic


def test_empty_array_retains_all_missing_pairs() -> None:
    # Given
    raw = b"[]"

    # When
    result = validate_assessments(raw, allowed_rules=RULES, sources=SOURCE)

    # Then
    assert isinstance(result, ValidatedAssessments)
    assert len(result.missing) == 2


@pytest.mark.parametrize(
    "raw",
    [b'[{"rule_id":"R1","rule_id":"R1"}]', b"[NaN]", b"\xff", b"[" * 2000],
    ids=["duplicate-key", "nonfinite", "utf8", "depth"],
)
def test_invalid_json_is_rejected(raw: bytes) -> None:
    # Given
    source = SOURCE

    # When
    result = validate_assessments(raw, allowed_rules=RULES, sources=source)

    # Then
    assert isinstance(result, InvalidResponse)
