# SPDX-License-Identifier: Apache-2.0
"""Contract tests for the review response boundary."""

import json
from pathlib import Path

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


def test_complete_and_incomplete_retain_findings_without_mutation() -> None:
    # Given
    item = finding(corrections=["fix"])
    raw = response(item, item, complete=False)
    sources = dict(SOURCES)

    # When
    result = validate_response(raw, allowed_rules=RULES, sources=sources)

    # Then
    assert isinstance(result, ValidatedResponse)
    assert result.complete is False
    assert len(result.findings) == 2
    assert result.findings[0].corrections == ["fix"]
    assert sources == SOURCES
    assert raw == response(item, item, complete=False)


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
        ({"rule_id": "R3"}, "not supplied"),
        ({"rule_id": "R2"}, "rule_id"),
        ({"file_id": "other.py"}, "file_id"),
        ({"start_line": 3, "end_line": 2}, "exceeds"),
        ({"end_line": 4}, "line count"),
        ({"quote": "first\nhello é"}, "quote"),
        ({"quote": "first"}, "quote"),
        ({"severity": "high"}, "severity"),
        ({"corrections": [""]}, "corrections"),
        ({"explanation": ""}, "explanation"),
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
        b'{"complete":true,"findings":[]} trailing',
        b'```json\n{"complete":true,"findings":[]}\n```',
        b'{"complete":true,"findings":[],"x":NaN}',
        b"\xff",
        b'{"complete":true,"findings":[{"rule_id":"R1","rule_id":"R1"}]}',
    ],
)
def test_rejects_invalid_json_or_envelope(raw: bytes) -> None:
    # Given
    # The parameter supplies raw model output.

    # When
    result = validate_response(raw, allowed_rules=RULES, sources=SOURCES)

    # Then
    assert isinstance(result, InvalidResponse)


def test_published_schema_contract_matches_validator() -> None:
    # Given
    shared = Path(
        "doc/feat/reviewer/engineering/evaluation/inputs/shared/review-instructions-and-schema.txt"
    ).read_text()
    schema = json.loads(shared.split("Response JSON contract:\n", 1)[1])
    item = schema["properties"]["findings"]["items"]

    # When
    result = validate_response(
        response(finding()), allowed_rules=RULES, sources=SOURCES
    )

    # Then
    assert isinstance(result, ValidatedResponse)
    assert set(schema["required"]) == {"complete", "findings"}
    assert schema["additionalProperties"] is False
    assert item["additionalProperties"] is False
    assert set(item["required"]) == set(finding())
    assert set(item["properties"]) == set(finding()) | {"corrections"}
    assert item["properties"]["rule_id"]["enum"] == ["R1", "R3", "R4"]
    assert item["properties"]["severity"]["enum"] == ["critical", "major", "minor"]
    assert schema["properties"]["complete"] == {"type": "boolean"}
    assert schema["properties"]["findings"]["type"] == "array"
    for name in ("file_id", "quote", "explanation", "consequence"):
        assert item["properties"][name] == {"type": "string", "minLength": 1}
    for name in ("start_line", "end_line"):
        assert item["properties"][name] == {"type": "integer", "minimum": 1}
    assert item["properties"]["corrections"] == {
        "type": "array",
        "items": {"type": "string", "minLength": 1},
    }
