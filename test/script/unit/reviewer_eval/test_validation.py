# SPDX-License-Identifier: Apache-2.0
"""Contract tests for the review response boundary."""

import json

import pytest

from script.reviewer_eval.validation import (
    InvalidResponse,
    ValidatedResponse,
    validate_response,
)

SOURCE = b"first\r\nhello \xc3\xa9\r\nlast\n"
SOURCES = {"sample.py": SOURCE}
RULES = frozenset({"R1"})


def finding(**changes: object) -> dict[str, object]:
    """Build one finding with a valid source quotation."""
    value: dict[str, object] = {
        "rule_id": "R1",
        "file_id": "sample.py",
        "start_line": 2,
        "end_line": 2,
        "quote": "hello é",
        "explanation": "reason",
        "consequence": "effect",
        "severity": "major",
    }
    value.update(changes)
    return value


def response(*findings: dict[str, object], complete: bool = True) -> bytes:
    """Encode a response to exercise the raw boundary."""
    return json.dumps({"complete": complete, "findings": findings}).encode()


@pytest.mark.parametrize("complete", [True, False], ids=["complete", "incomplete"])
def test_complete_and_incomplete_retain_findings_without_mutation(
    complete: bool,
) -> None:
    # Given
    item = finding(corrections=["fix"])
    raw = response(item, item, complete=complete)
    sources = dict(SOURCES)

    # When
    result = validate_response(raw, allowed_rules=RULES, sources=sources)

    # Then
    assert isinstance(result, ValidatedResponse)
    assert result.complete is complete
    assert len(result.findings) == 2
    assert result.findings[0].model_dump() == {
        **item,
        "corrections": ("fix",),
    }
    assert result.findings[0].corrections == ("fix",)
    assert isinstance(result.findings[0].corrections, tuple)
    assert sources == SOURCES
    assert raw == response(item, item, complete=complete)


def test_complete_empty_findings_is_valid() -> None:
    # Given
    raw = response()

    # When
    result = validate_response(raw, allowed_rules=RULES, sources=SOURCES)

    # Then
    assert result == ValidatedResponse(True, ())


def test_multiline_quote_preserves_unicode_and_original_newlines() -> None:
    # Given
    raw = response(finding(start_line=1, end_line=2, quote="first\r\nhello é\r\n"))

    # When
    result = validate_response(raw, allowed_rules=RULES, sources=SOURCES)

    # Then
    assert isinstance(result, ValidatedResponse)
    assert result.complete


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"unknown": 1}, "unknown"),
        ({"start_line": "2"}, "start_line"),
        ({"start_line": True}, "start_line"),
        ({"start_line": 0}, "start_line"),
        ({"end_line": -1}, "end_line"),
        ({"end_line": True}, "end_line"),
        ({"end_line": 2.0}, "end_line"),
        ({"quote": "\ud800"}, "quote"),
        ({"rule_id": "R3"}, "not supplied"),
        ({"rule_id": "R2"}, "rule_id"),
        ({"file_id": "other.py"}, "file_id"),
        ({"start_line": 3, "end_line": 2}, "exceeds"),
        ({"end_line": 4}, "line count"),
        ({"quote": "first\nhello é"}, "quote"),
        ({"quote": "first"}, "quote"),
        ({"severity": "high"}, "severity"),
        ({"corrections": [""]}, "corrections"),
        ({"corrections": [1]}, "corrections"),
        ({"corrections": "fix"}, "corrections"),
        ({"explanation": ""}, "explanation"),
    ],
    ids=[
        "unknown-key",
        "string-line",
        "bool-start",
        "zero-start",
        "negative-end",
        "bool-end",
        "float-end",
        "surrogate-quote",
        "unsupplied-rule",
        "unknown-rule",
        "unsupplied-file",
        "reversed-span",
        "out-of-bounds",
        "newline-mismatch",
        "outside-span",
        "invalid-severity",
        "empty-correction",
        "non-string-correction",
        "non-array-corrections",
        "empty-explanation",
    ],
)
def test_rejects_invalid_finding(changes: dict[str, object], reason: str) -> None:
    # Given
    raw = response(finding(**changes))

    # When
    result = validate_response(raw, allowed_rules=RULES, sources=SOURCES)

    # Then
    assert isinstance(result, InvalidResponse)
    assert reason in result.diagnostic


@pytest.mark.parametrize(
    "raw",
    [
        b'{"complete":true,"complete":false,"findings":[]}',
        b'{"complete":true,"findings":[],"extra":1}',
        b'{"complete":1,"findings":[]}',
        b'{"complete":true}',
        b'{"findings":[]}',
        b'{"complete":null,"findings":[]}',
        b'{"complete":true,"findings":null}',
        b"null",
        b'{"complete":true,"findings":[]} trailing',
        b'```json\n{"complete":true,"findings":[]}\n```',
        b'{"complete":true,"findings":[],"x":NaN}',
        b"\xff",
        b'{"complete":true,"findings":[{"rule_id":"R1","rule_id":"R1"}]}',
    ],
    ids=[
        "duplicate-root-key",
        "unknown-root-key",
        "nonboolean-complete",
        "missing-findings",
        "missing-complete",
        "null-complete",
        "null-findings",
        "null-root",
        "trailing-text",
        "code-fence",
        "nan",
        "invalid-utf8",
        "duplicate-finding-key",
    ],
)
def test_rejects_invalid_json_or_envelope(raw: bytes) -> None:
    # Given
    # The parameter supplies raw model output.

    # When
    result = validate_response(raw, allowed_rules=RULES, sources=SOURCES)

    # Then
    assert isinstance(result, InvalidResponse)


def test_excessively_nested_json_is_invalid() -> None:
    # Given
    raw = b"[" * 400000 + b"]" * 400000

    # When
    result = validate_response(raw, allowed_rules=RULES, sources=SOURCES)

    # Then
    assert isinstance(result, InvalidResponse)
    assert "nest" in result.diagnostic
