# SPDX-License-Identifier: Apache-2.0
"""Exercise the offline analysis against the retained, verified C archives."""

from hashlib import sha256
import json
from pathlib import Path

from script.reviewer_eval.telemetry_c import check_artifact, generate


def test_retained_telemetry_reproduces_and_matches_known_inventory() -> None:
    # Given
    evidence = Path("output/reviewer-evaluation/c-full-001")

    # When
    artifacts = generate(evidence)
    summary = json.loads(artifacts["telemetry.json"])
    retained = json.loads((evidence / "telemetry/telemetry.json").read_bytes())

    # Then
    for name, data in artifacts.items():
        check_artifact(name, data, (evidence / "telemetry" / name).read_bytes())
    historical_code = json.dumps(retained["code_sha256"], sort_keys=True).encode()
    assert sha256(historical_code).hexdigest() == (
        "48081fe799b2374007457ac5248563996983cd83895655dc8d662d33a5731325"
    )
    assert summary["all"]["attempts"] == 2232
    assert summary["all"]["states"] == {"complete": 2228, "invalid": 4}
    assert summary["all"]["usage"]["input_tokens"]["total"] == 11633761
    assert {block["timeline"]["peak"] for block in summary["blocks"].values()} == {25}
