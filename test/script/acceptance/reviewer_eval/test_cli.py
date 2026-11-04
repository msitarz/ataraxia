# SPDX-License-Identifier: Apache-2.0
"""Command behavior for saved reviewer reports."""

import json
from pathlib import Path
import subprocess
import sys

from script.eval.model import FrozenPlan
from test.script.integration.reviewer_eval.support import (
    create_run,
    full_current_response,
)


def test_cli_creates_exclusive_report(saved_run: Path, tmp_path: Path) -> None:
    # Given
    output = tmp_path / "report.json"
    command = [
        sys.executable,
        "-m",
        "script.reviewer_eval",
        str(saved_run),
        "--output",
        str(output),
    ]

    # When
    first = subprocess.run(command, capture_output=True, timeout=10, check=False)
    before = output.read_bytes()
    second = subprocess.run(command, capture_output=True, timeout=10, check=False)

    # Then
    assert first.returncode == 0
    assert json.loads(before)["version"] == 2
    assert json.loads(before)["calls"][0]["response_format"] == "findings-v1"
    assert json.loads(before)["counts"]["complete"] == 1
    assert second.returncode == 1
    assert output.read_bytes() == before


def test_help_and_missing_plan_failure(tmp_path: Path) -> None:
    # Given
    root = tmp_path / "run"
    root.mkdir()
    output = tmp_path / "report.json"

    # When
    help_result = subprocess.run(
        [sys.executable, "-m", "script.reviewer_eval", "--help"],
        capture_output=True,
        timeout=10,
        check=False,
    )
    failed = subprocess.run(
        [
            sys.executable,
            "-m",
            "script.reviewer_eval",
            str(root),
            "--output",
            str(output),
        ],
        capture_output=True,
        timeout=10,
        check=False,
    )

    # Then
    assert help_result.returncode == 0
    assert b"original harness run directory" in help_result.stdout
    assert failed.returncode == 1
    assert json.loads(output.read_bytes())["planned_count"] is None


async def test_current_complete_and_partial_reports(tmp_path: Path) -> None:
    # Given
    full_root = tmp_path / "full" / "run"
    partial_root = tmp_path / "partial" / "run"
    full_root.parent.mkdir()
    partial_root.parent.mkdir()
    full_output = tmp_path / "full.json"
    partial_output = tmp_path / "partial.json"
    await create_run(
        full_root, current=True, response=full_current_response(), notice=True
    )
    await create_run(partial_root, current=True, response=[])
    full_command = [
        sys.executable,
        "-m",
        "script.reviewer_eval",
        str(full_root),
        "--output",
        str(full_output),
    ]
    partial_command = [
        sys.executable,
        "-m",
        "script.reviewer_eval",
        str(partial_root),
        "--output",
        str(partial_output),
    ]

    # When
    full = subprocess.run(full_command, capture_output=True, timeout=10, check=False)
    before = full_output.read_bytes()
    repeated = subprocess.run(
        full_command, capture_output=True, timeout=10, check=False
    )
    partial = subprocess.run(
        partial_command, capture_output=True, timeout=10, check=False
    )
    full_report = json.loads(before)
    partial_report = json.loads(partial_output.read_bytes())

    # Then
    assert full.returncode == 0
    assert repeated.returncode == 1
    assert full_output.read_bytes() == before
    assert (full_report["version"], full_report["calls"][0]["response_format"]) == (
        2,
        "function-assessments-v2",
    )
    assert len(full_report["calls"][0]["assessments"]) == 9
    assert full_report["calls"][0]["missing_pairs"] == []
    assert partial.returncode == 1
    assert partial_report["calls"][0]["state"] == "incomplete"
    assert len(partial_report["calls"][0]["missing_pairs"]) == 9


def _scoring_inputs(tmp_path: Path) -> tuple[FrozenPlan, Path, list[dict[str, str]]]:
    from hashlib import sha256

    from script.eval.model import FrozenInputs
    from script.eval.plan import PurePlanBuilder
    from script.reviewer_eval.context import FILES
    from test.script.integration.reviewer_eval.support import plan

    original = plan(current=True)
    sources = tuple(
        "".join(f"def f{i}(): pass\n" for i in range(8)).encode() for _ in FILES
    )
    bundle = b"Context:\n" + b"".join(
        f"\n--- {file} (original lines 1-8) ---\n".encode() + source
        for file, source in zip(FILES, sources, strict=True)
    )
    snapshots = list(original.snapshots)
    snapshots[2] = snapshots[2].model_copy(
        update={"content": bundle, "content_sha256": sha256(bundle).hexdigest()}
    )
    frozen = PurePlanBuilder("run").plan(
        FrozenInputs(
            original.repository_root, original.head_commit, tuple(snapshots), None
        ),
        original.configuration,
    )
    digest_lines = [
        f"- `{file}`: `{sha256(source).hexdigest()}`"
        for file, source in zip(FILES, sources, strict=True)
    ]
    digest_lines.extend(
        f"- `{rule.lower()}/rule.txt`: `{sha256(content).hexdigest()}`"
        for rule, content in (("R1", b"a\n"), ("R3", b"b\n"), ("R4", b"c\n"))
    )
    rows = [
        f"| {rule} | `{file}` | f{i} | {'PASS' if i < 4 else 'VIOLATION'} | synthetic |"
        for rule, file in zip(("R1", "R3", "R4"), FILES, strict=True)
        for i in range(8)
    ]
    index = tmp_path / "private.md"
    index.write_text(
        "\n".join([
            "# Draft",
            *digest_lines,
            "| Rule | File | Function | Expected | Source-grounded rationale |",
            "| --- | --- | --- | --- | --- |",
            *rows,
            "",
        ])
    )
    response = [
        {
            "rule_id": rule,
            "file_id": file,
            "function_name": f"f{i}",
            "judgement": "PASS" if i < 4 else "VIOLATION",
        }
        for rule in ("R1", "R3", "R4")
        for file in FILES
        for i in range(8)
    ]
    return frozen, index, response


async def test_private_scoring_cli_preserves_evidence(tmp_path: Path) -> None:
    # Given
    from test.script.integration.reviewer_eval.support import snapshot

    frozen, index, response = _scoring_inputs(tmp_path)
    root = tmp_path / "run"
    output = tmp_path / "score.json"
    await create_run(root, frozen_plan=frozen, response=response)
    before = snapshot(root)
    command = [
        sys.executable,
        "-m",
        "script.reviewer_eval",
        str(root),
        "--reference-index",
        str(index),
        "--output",
        str(output),
    ]

    # When
    first = subprocess.run(command, capture_output=True, timeout=10, check=False)
    score = json.loads(output.read_bytes())
    second = subprocess.run(command, capture_output=True, timeout=10, check=False)

    # Then
    assert first.returncode == 0
    assert second.returncode == 1
    assert score["calls"][0]["measures"]["accuracy"]["value"] == 1
    assert score["calls"][0]["measures"]["unindexed_records"] == 48
    assert score["calls"][0]["per_rule"][0]["measures"]["accuracy"]["denominator"] == 8
    assert score["reference_status"] == "draft; not independently reviewed or frozen"
    assert snapshot(root) == before


async def test_private_scoring_cli_partial_and_stale_reference(tmp_path: Path) -> None:
    # Given
    frozen, index, response = _scoring_inputs(tmp_path)
    root = tmp_path / "run"
    output = tmp_path / "partial.json"
    stale_output = tmp_path / "stale.json"
    await create_run(root, frozen_plan=frozen, response=response[:1])
    command = [
        sys.executable,
        "-m",
        "script.reviewer_eval",
        str(root),
        "--reference-index",
        str(index),
        "--output",
        str(output),
    ]

    # When
    partial = subprocess.run(command, capture_output=True, timeout=10, check=False)
    score = json.loads(output.read_bytes())
    content = index.read_text()
    digest_start = content.index("`: `") + len("`: `")
    replacement = "0" if content[digest_start] != "0" else "1"
    index.write_text(content[:digest_start] + replacement + content[digest_start + 1 :])
    stale_command = [*command[:-1], str(stale_output)]
    stale = subprocess.run(stale_command, capture_output=True, timeout=10, check=False)

    # Then
    assert partial.returncode == 1
    assert score["calls"][0]["measures"]["accuracy"]["numerator"] == 0
    assert score["calls"][0]["measures"]["indexed_records"] == 1
    assert stale.returncode == 1
    assert not stale_output.exists()
