# SPDX-License-Identifier: Apache-2.0
"""Consistency of draft engineering review prompts and public sources."""

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
from script.reviewer_eval.context import review_context
from script.reviewer_eval.validation import ValidatedAssessments, validate_assessments

ROOT = Path(__file__).resolve().parents[4]
EVALUATION = ROOT / "doc/feat/reviewer/engineering/evaluation"
INPUTS = EVALUATION / "inputs"
SHARED = INPUTS / "shared" / "review-instructions-and-schema.txt"
CORPUS = EVALUATION / "corpus"
BUNDLE = INPUTS / "corpus" / "source.txt"
RULES = ("R1", "R3", "R4")
SOURCES = ("r1/dispatch.py.txt", "r3/planning.py.txt", "r4/ledger.py.txt")


def rule_bytes(rules: tuple[str, ...]) -> bytes:
    return b"".join(
        f"\n--- {rule} ---\n".encode()
        + (CORPUS / rule.lower() / "rule.txt").read_bytes()
        for rule in rules
    )


def whole_bundle() -> bytes:
    return b"".join(
        f"\n--- {path} (original lines 1-{len(data.splitlines())}) ---\n".encode()
        + data
        for path in SOURCES
        for data in [(CORPUS / path).read_bytes()]
    )


def test_exact_prompt_inventory_and_shared_schema() -> None:
    # Given
    cases = INPUTS / "cases"
    shared = SHARED.read_bytes()

    # When
    inventory = {
        str(path.relative_to(cases)) for path in cases.rglob("*") if path.is_file()
    }
    schema = json.loads(shared.split(b"Response JSON contract:\n", 1)[1])

    # Then
    assert inventory == {"A/a.txt", "B/r1.txt", "B/r3.txt", "B/r4.txt"}
    assert {path.name for path in cases.iterdir()} == {"A", "B"}
    assert list((INPUTS / "shared").iterdir()) == [SHARED]
    assert list((INPUTS / "corpus").iterdir()) == [BUNDLE]
    assert BUNDLE.read_bytes() == b"Context:\n" + whole_bundle()
    assert b"Response format: function-assessments-v2" in shared
    assert schema["type"] == "array"
    record = schema["items"]
    assert record["additionalProperties"] is False
    assert set(record["required"]) == {
        "rule_id",
        "file_id",
        "function_name",
        "judgement",
    }
    assert set(record["properties"]) == set(record["required"])
    assert record["properties"]["judgement"]["enum"] == [
        "PASS",
        "VIOLATION",
        "UNKNOWN",
        "NOT_APPLICABLE",
    ]


@pytest.mark.parametrize(
    "strategy,ident,rules",
    [("A", "a", RULES), *(("B", rule.lower(), (rule,)) for rule in RULES)],
    ids=["A", "B-R1", "B-R3", "B-R4"],
)
def test_case_contains_exact_rules(
    strategy: str, ident: str, rules: tuple[str, ...]
) -> None:
    # Given
    actual = (INPUTS / "cases" / strategy / f"{ident}.txt").read_bytes()

    # When
    expected = b"Rules:\n" + rule_bytes(rules)

    # Then
    assert actual == expected
    envelope = actual.split(b"\n--- R", 1)[0]
    assert envelope == b"Rules:\n"
    assert b"Expected assessments:" not in SHARED.read_bytes()
    assert b"{SESSION_ID}" not in SHARED.read_bytes()
    assert b"session_id" not in SHARED.read_bytes()
    assert b"strategy" not in SHARED.read_bytes()
    assert b"input_id" not in SHARED.read_bytes()
    assert b"qualified_function_name" not in SHARED.read_bytes()


@pytest.mark.parametrize("strategy,expected_count", [("A", 1), ("B", 3)])
def test_strategy_directory_composes_through_the_public_plan_builder(
    strategy: str, expected_count: int
) -> None:
    # Given
    shared_directory = INPUTS / "shared"
    case_directory = INPUTS / "cases" / strategy
    case_paths = sorted(case_directory.glob("*.txt"))
    sources = tuple(
        SourceSnapshot(
            directory_position=position,
            repository_path=str(path.relative_to(ROOT)),
            commit_blob_sha="0" * 40,
            content_sha256=sha256(path.read_bytes()).hexdigest(),
            content=path.read_bytes(),
        )
        for position, paths in ((0, [SHARED]), (2, case_paths), (4, [BUNDLE]))
        for path in paths
    )
    config = HarnessConfig(
        ordered_options=(
            DirectoryOption(position=0, path=shared_directory),
            DirectoryOption(position=2, path=case_directory),
            DirectoryOption(position=4, path=INPUTS / "corpus"),
        ),
        models=("model",),
        efforts=("medium",),
        concurrency=1,
        output_directory=None,
        dry_run=True,
        timeout_seconds=1.0,
        cleanup_timeout_seconds=2.0,
        grace_seconds=0.0,
        output_limit_bytes=1000,
        instructions_file_path=None,
    )
    inputs = FrozenInputs(ROOT, "0" * 40, sources, None)

    # When
    plan = PurePlanBuilder("review-contexts").plan(inputs, config)
    calls = plan.calls
    rules, source_bytes = review_context(plan, calls[0])
    response = validate_assessments(b"[]", allowed_rules=rules, sources=source_bytes)

    # Then
    assert isinstance(response, ValidatedAssessments)
    assert len(response.missing) == (186 if strategy == "A" else 62)
    assert len({(pair.file_id, pair.function_name) for pair in response.missing}) == 62
    assert len(calls) == len(case_paths) == expected_count
    assert tuple(call.prompt for call in calls) == tuple(
        SHARED.read_bytes()
        + b"\n\n"
        + path.read_bytes()
        + b"\n\n"
        + BUNDLE.read_bytes()
        for path in case_paths
    )
    assert all(call.context_indices[0] == 0 for call in calls)
