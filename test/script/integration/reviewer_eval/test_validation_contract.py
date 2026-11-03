# SPDX-License-Identifier: Apache-2.0
"""Compare the validator boundary with the published response contract."""

import json
from pathlib import Path

from script.reviewer_eval.validation import ValidatedResponse, validate_response


def test_published_schema_contract_matches_validator() -> None:
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
