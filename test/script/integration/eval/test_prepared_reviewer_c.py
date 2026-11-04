# SPDX-License-Identifier: Apache-2.0
"""Exercise static C generation and its public singleton boundary."""

from hashlib import sha256
import json
from pathlib import Path

import pytest

from script.eval.model import (
    DirectoryOption,
    FrozenInputs,
    HarnessConfig,
    SourceSnapshot,
)
from script.eval.plan import PurePlanBuilder
from script.reviewer_eval.context import c_target, response_format, review_context
from script.reviewer_eval.prepare_c import CORPUS, INPUTS, prepare
from script.reviewer_eval.validation import (
    InvalidResponse,
    ValidatedAssessments,
    validate_singleton,
)


def test_generated_packets_are_reproducible_and_source_grounded() -> None:
    artifacts = prepare()
    assert artifacts == prepare()
    assert all((INPUTS / name).read_bytes() == data for name, data in artifacts.items())
    manifest = json.loads(artifacts["c-manifest.json"])
    schedule = json.loads(artifacts["c-schedule.json"])
    entries = manifest["packets"]
    assert len(entries) == 186
    assert len(schedule) == 2232
    assert [row["effort"] for row in schedule[::186]] == [
        "none",
        "low",
        "medium",
        "high",
        "low",
        "medium",
        "high",
        "none",
        "medium",
        "high",
        "none",
        "low",
    ]
    assert (
        len({
            (
                e["target"]["rule_id"],
                e["target"]["file_id"],
                e["target"]["function_name"],
            )
            for e in entries
        })
        == 186
    )
    for entry in entries:
        source = (
            (CORPUS / entry["target"]["file_id"]).read_bytes().splitlines(keepends=True)
        )
        packet = artifacts["c-packets/" + entry["packet"]]
        assert (
            CORPUS / entry["target"]["rule_id"].lower() / "rule.txt"
        ).read_bytes() in packet
        for span in entry["spans"]:
            content = b"".join(source[span["start"] - 1 : span["end"]])
            assert sha256(content).hexdigest() == span["sha256"]
            assert content in packet
        assert any(s["role"] == "target" for s in entry["spans"])
    method = next(
        e
        for e in entries
        if e["target"]["function_name"] == "Ledger.add_event"
        and e["target"]["rule_id"] == "R4"
    )
    assert any("class" in reason for s in method["spans"] for reason in s["reasons"])
    assert any("callee" in reason for s in method["spans"] for reason in s["reasons"])


def test_matrix_and_singleton_validation() -> None:
    paths = [
        INPUTS / "c-shared/review-instructions-and-schema.txt",
        *sorted((INPUTS / "c-packets").glob("*.txt")),
    ]
    root = Path(__file__).resolve().parents[4]
    snapshots = tuple(
        SourceSnapshot(
            directory_position=0 if i == 0 else 2,
            repository_path=str(p.relative_to(root)),
            commit_blob_sha="0" * 40,
            content_sha256=sha256(p.read_bytes()).hexdigest(),
            content=p.read_bytes(),
        )
        for i, p in enumerate(paths)
    )
    config = HarnessConfig(
        ordered_options=(
            DirectoryOption(position=0, path=paths[0].parent),
            DirectoryOption(position=2, path=paths[1].parent),
        ),
        models=("model",),
        efforts=("medium",),
        concurrency=1,
        output_directory=None,
        dry_run=True,
        timeout_seconds=1,
        cleanup_timeout_seconds=2,
        grace_seconds=0,
        output_limit_bytes=1000,
        instructions_file_path=None,
    )
    plan = PurePlanBuilder("c").plan(
        FrozenInputs(root, "0" * 40, snapshots, None), config
    )
    assert len(plan.calls) == 186
    for call in plan.calls:
        assert response_format(plan, call) == "function-assessments-c-v1"
        target = c_target(plan, call)
        assert review_context(plan, call)[0] == frozenset({target.rule_id})
        record = {
            "rule_id": target.rule_id,
            "file_id": target.file_id,
            "function_name": target.function_name,
            "judgement": "UNKNOWN",
        }
        assert isinstance(
            validate_singleton(json.dumps([record]).encode(), target=target),
            ValidatedAssessments,
        )
        empty: list[object] = []
        for bad in (
            empty,
            [record, record],
            [{**record, "function_name": "foreign"}],
            [{**record, "extra": 1}],
        ):
            assert isinstance(
                validate_singleton(json.dumps(bad).encode(), target=target),
                InvalidResponse,
            )
        assert isinstance(
            validate_singleton(b'[{"rule_id":"R1","rule_id":"R1"}]', target=target),
            InvalidResponse,
        )


async def test_saved_reader_uses_frozen_target(tmp_path: Path) -> None:
    from script.reviewer_eval.report import inspect_run
    from test.script.integration.reviewer_eval.support import create_run

    shared = INPUTS / "c-shared/review-instructions-and-schema.txt"
    packet = sorted((INPUTS / "c-packets").glob("*.txt"))[0]
    root = Path(__file__).resolve().parents[4]
    paths = (shared, packet)
    snapshots = tuple(
        SourceSnapshot(
            directory_position=i * 2,
            repository_path=str(path.relative_to(root)),
            commit_blob_sha="0" * 40,
            content_sha256=sha256(path.read_bytes()).hexdigest(),
            content=path.read_bytes(),
        )
        for i, path in enumerate(paths)
    )
    config = HarnessConfig(
        ordered_options=tuple(
            DirectoryOption(position=i * 2, path=path.parent)
            for i, path in enumerate(paths)
        ),
        models=("model",),
        efforts=("low",),
        concurrency=1,
        output_directory=Path("run"),
        dry_run=False,
        timeout_seconds=5,
        cleanup_timeout_seconds=2,
        grace_seconds=0,
        output_limit_bytes=10000,
        instructions_file_path=None,
    )
    plan = PurePlanBuilder("run").plan(
        FrozenInputs(Path("/unused"), "head", snapshots, None), config
    )
    target = c_target(plan, plan.calls[0])
    record = {
        "rule_id": target.rule_id,
        "file_id": target.file_id,
        "function_name": target.function_name,
        "judgement": "UNKNOWN",
    }
    await create_run(tmp_path / "run", frozen_plan=plan, response=[record])
    report = inspect_run(tmp_path / "run")
    assert report.calls[0].response_format == "function-assessments-c-v1"
    assert report.calls[0].state == "complete"
    assert len(report.calls[0].assessments) == 1
    await create_run(tmp_path / "missing", frozen_plan=plan, response=[])
    assert inspect_run(tmp_path / "missing").calls[0].state == "invalid"


def test_nested_target_and_crlf_preserve_original_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from script.reviewer_eval import prepare_c

    corpus = tmp_path / "corpus"
    inputs = tmp_path / "inputs"
    for folder in ("r1", "r3", "r4"):
        (corpus / folder).mkdir(parents=True)
        (corpus / folder / "rule.txt").write_bytes(b"unchanged rule\r\n")
    source = (
        b'"""Module contract."""\r\n'
        b"import math\r\n"
        b"def helper(x):\r\n    return x + 1\r\n"
        b"class C:\r\n    field: int\r\n"
        b"    def method(self, value):\r\n"
        b"        def inner():\r\n            return helper(value)\r\n"
        b"        return inner()\r\n"
        b"    def unrelated(self):\r\n        pass\r\n"
    )
    for file_id in prepare_c.FILES:
        (corpus / file_id).write_bytes(source)
    shared = inputs / "c-shared/review-instructions-and-schema.txt"
    shared.parent.mkdir(parents=True)
    shared.write_bytes(b"schema")
    monkeypatch.setattr(prepare_c, "CORPUS", corpus)
    monkeypatch.setattr(prepare_c, "INPUTS", inputs)
    artifacts = prepare_c.prepare()
    packet = artifacts["c-packets/R1--r1--dispatch.py.txt--C.method.inner.txt"]
    assert b"def method(self, value):\r\n" in packet
    assert b"def inner():\r\n            return helper(value)\r\n" in packet
    assert b"def helper(x):\r\n    return x + 1\r\n" in packet
    assert b"def unrelated" not in packet
    manifest = json.loads(artifacts["c-manifest.json"])
    entry = next(
        e for e in manifest["packets"] if e["packet"].endswith("--C.method.inner.txt")
    )
    assert any("nested target" in flag for flag in entry["flags"])
