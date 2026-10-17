# SPDX-License-Identifier: Apache-2.0
"""Validate recorded Make calls at their public file-reading boundary."""

import json
from pathlib import Path

import pytest

from test.make.support import UvCall, read_calls


def test_read_calls_adapts_valid_records_in_log_order(tmp_path: Path) -> None:
    # Given
    log = tmp_path / "calls.jsonl"
    log.write_text(
        json.dumps({"argv": ["sync", "--locked"], "environment": {"UV": None}})
        + "\n"
        + json.dumps({"argv": ["run", "pytest"], "environment": {"CI": "1"}})
        + "\n"
    )

    # When
    calls = read_calls(log)

    # Then
    assert calls == (
        UvCall(("sync", "--locked"), {"UV": None}),
        UvCall(("run", "pytest"), {"CI": "1"}),
    )


@pytest.mark.parametrize(
    ("record", "message"),
    [
        pytest.param([], "uv record must be a mapping", id="non-mapping"),
        pytest.param(
            {"argv": ["run"], "environment": []},
            "uv record must contain arguments and environment",
            id="environment-shape",
        ),
        pytest.param(
            {"argv": [1], "environment": {}},
            "uv argument must be a string",
            id="argument-type",
        ),
        pytest.param(
            {"argv": [], "environment": {"CI": 1}},
            "uv environment must contain string names and values",
            id="environment-value-type",
        ),
    ],
)
def test_read_calls_rejects_malformed_records_at_ingress(
    tmp_path: Path, record: object, message: str
) -> None:
    # Given
    log = tmp_path / "calls.jsonl"
    log.write_text(json.dumps(record) + "\n")

    # When / Then
    with pytest.raises(ValueError, match=message):
        read_calls(log)
