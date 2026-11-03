# SPDX-License-Identifier: Apache-2.0
"""Compare the validator boundary with the published response contract."""

import json
from pathlib import Path

import pytest

from script.reviewer_eval.validation import (
    InvalidResponse,
    ValidatedResponse,
    validate_response,
)


def test_published_schema_shape() -> None:
    # Given
    shared = Path(
        "doc/feat/reviewer/engineering/evaluation/inputs/shared/review-instructions-and-schema.txt"
    ).read_text()
    schema = json.loads(shared.split("Response JSON contract:\n", 1)[1])
    item = schema["properties"]["findings"]["items"]

    # When
    result = validate_response(
        b'{"complete":true,"findings":[]}', allowed_rules=frozenset(), sources={}
    )

    # Then
    assert isinstance(result, ValidatedResponse)
    assert set(schema["required"]) == {"complete", "findings"}
    assert schema["additionalProperties"] is False
    assert item["additionalProperties"] is False
    assert set(item["required"]) == {
        "rule_id",
        "file_id",
        "start_line",
        "end_line",
        "quote",
        "explanation",
        "consequence",
        "severity",
    }
    assert set(item["properties"]) == {
        "rule_id",
        "file_id",
        "start_line",
        "end_line",
        "quote",
        "explanation",
        "consequence",
        "severity",
    } | {"corrections"}
    assert item["properties"]["rule_id"]["enum"] == ["R1", "R3", "R4"]
    assert item["properties"]["severity"]["enum"] == ["critical", "major", "minor"]
    assert schema["properties"]["complete"] == {"type": "boolean"}
    assert schema["properties"]["findings"]["type"] == "array"
    assert {
        name: item["properties"][name]
        for name in ("file_id", "quote", "explanation", "consequence")
    } == {
        "file_id": {"type": "string", "minLength": 1},
        "quote": {"type": "string", "minLength": 1},
        "explanation": {"type": "string", "minLength": 1},
        "consequence": {"type": "string", "minLength": 1},
    }
    assert {name: item["properties"][name] for name in ("start_line", "end_line")} == {
        "start_line": {"type": "integer", "minimum": 1},
        "end_line": {"type": "integer", "minimum": 1},
    }
    assert item["properties"]["corrections"] == {
        "type": "array",
        "items": {"type": "string", "minLength": 1},
    }


@pytest.mark.parametrize("rule", ["R1", "R3", "R4"], ids=["R1", "R3", "R4"])
@pytest.mark.parametrize(
    "severity", ["critical", "major", "minor"], ids=["critical", "major", "minor"]
)
def test_published_rule_and_severity_members_are_accepted(
    rule: str, severity: str
) -> None:
    # Given
    finding = {
        "rule_id": rule,
        "file_id": "file.py",
        "start_line": 1,
        "end_line": 1,
        "quote": "source",
        "explanation": "reason",
        "consequence": "effect",
        "severity": severity,
    }
    raw = json.dumps({"complete": True, "findings": [finding]}).encode()

    # When
    result = validate_response(
        raw, allowed_rules=frozenset({rule}), sources={"file.py": b"source\n"}
    )

    # Then
    assert isinstance(result, ValidatedResponse)
    assert result.complete
    assert result.findings[0].rule_id == rule
    assert result.findings[0].severity == severity


@pytest.mark.parametrize(
    "missing",
    [
        "rule_id",
        "file_id",
        "start_line",
        "end_line",
        "quote",
        "explanation",
        "consequence",
        "severity",
    ],
    ids=[
        "rule-id",
        "file-id",
        "start-line",
        "end-line",
        "quote",
        "explanation",
        "consequence",
        "severity",
    ],
)
def test_each_published_required_finding_field_is_enforced(missing: str) -> None:
    # Given
    finding = {
        "rule_id": "R1",
        "file_id": "file.py",
        "start_line": 1,
        "end_line": 1,
        "quote": "source",
        "explanation": "reason",
        "consequence": "effect",
        "severity": "minor",
    }
    del finding[missing]
    raw = json.dumps({"complete": True, "findings": [finding]}).encode()

    # When
    result = validate_response(
        raw, allowed_rules=frozenset({"R1"}), sources={"file.py": b"source\n"}
    )

    # Then
    assert isinstance(result, InvalidResponse)
    assert missing in result.diagnostic


@pytest.mark.parametrize(
    ("raw", "missing"),
    [(b'{"findings":[]}', "complete"), (b'{"complete":true}', "findings")],
    ids=["complete", "findings"],
)
def test_each_published_required_envelope_field_is_enforced(
    raw: bytes, missing: str
) -> None:
    # Given
    # The parameter supplies an envelope missing one published required field.

    # When
    result = validate_response(raw, allowed_rules=frozenset(), sources={})

    # Then
    assert isinstance(result, InvalidResponse)
    assert missing in result.diagnostic
