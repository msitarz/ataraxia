# SPDX-License-Identifier: Apache-2.0
"""Exercise the offline analysis against the retained, verified C archives."""

import json
from pathlib import Path

from script.reviewer_eval.telemetry_c import generate


def test_retained_telemetry_reproduces_and_matches_known_inventory() -> None:
    # Given
    evidence = Path("output/reviewer-evaluation/c-full-001")

    # When
    artifacts = generate(evidence)
    summary = json.loads(artifacts["telemetry.json"])

    # Then
    assert all(
        (evidence / "telemetry" / name).read_bytes() == data
        for name, data in artifacts.items()
    )
    assert summary["all"]["attempts"] == 2232
    assert summary["all"]["states"] == {"complete": 2228, "invalid": 4}
    assert summary["all"]["usage"]["input_tokens"]["total"] == 11633761
    assert {block["timeline"]["peak"] for block in summary["blocks"].values()} == {25}
