# SPDX-License-Identifier: Apache-2.0
"""Consistency of draft engineering review prompts and their public sources."""

import ast
import json
from pathlib import Path
import re

from pydantic import BaseModel, TypeAdapter
import pytest

ROOT = Path(__file__).resolve().parents[4]
EVALUATION = ROOT / "doc/feat/reviewer/engineering/evaluation"
INPUTS = EVALUATION / "inputs"
CORPUS = EVALUATION / "corpus"
RULES = ("R1", "R3", "R4")
SOURCES = ("r1/dispatch.py.txt", "r3/planning.py.txt", "r4/ledger.py.txt")


class AssessmentKey(BaseModel, frozen=True):
    rule_id: str
    file_id: str
    qualified_function_name: str


class Packet(BaseModel):
    target: AssessmentKey
    ranges: list[tuple[int, int]]


KEYS = TypeAdapter(list[AssessmentKey]).validate_json(
    (INPUTS / "expected.json").read_bytes()
)
PACKETS = TypeAdapter(dict[str, Packet]).validate_json(
    (INPUTS / "c-ranges.json").read_bytes()
)


def manifest_keys() -> set[AssessmentKey]:
    """Read the target inventory in the public corpus manifest."""
    manifest = (CORPUS / "manifest.md").read_text()
    rows = re.findall(
        r"\| (R[134]) \| \[\w+\]\(([^)]+)\) \| \d+ \| ([^|]+) \|", manifest
    )
    return {
        AssessmentKey(rule_id=rule, file_id=path, qualified_function_name=name)
        for rule, path, names in rows
        for name in re.findall(r"`([^`]+)`", names)
    }


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


def context_bytes(packet: Packet) -> bytes:
    lines = (CORPUS / packet.target.file_id).read_bytes().splitlines(keepends=True)
    return b"".join(
        f"\n--- {packet.target.file_id} original lines {start}-{end} ---\n".encode()
        + b"".join(lines[start - 1 : end])
        for start, end in packet.ranges
    )


def expected_prompt(
    strategy: str,
    ident: str,
    keys: list[AssessmentKey],
    rules: tuple[str, ...],
    context: bytes,
) -> bytes:
    template = (
        (INPUTS / "prompt-template.txt")
        .read_text()
        .format(strategy=strategy, input_id=ident)
        .encode()
    )
    assessments = json.dumps([key.model_dump() for key in keys], indent=2).encode()
    return (
        template
        + b"\nExpected assessments:\n"
        + assessments
        + b"\nResponse JSON contract:\n"
        + (INPUTS / "response.schema.json").read_bytes()
        + b"\nRules:\n"
        + rule_bytes(rules)
        + b"\nContext:\n"
        + context
    )


def node_start(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> int:
    return min([node.lineno, *(decorator.lineno for decorator in node.decorator_list)])


def covered(packet: Packet, start: int, end: int) -> bool:
    return any(first <= start and end <= last for first, last in packet.ranges)


def dependencies(
    node: ast.AST,
    definitions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef],
) -> set[str]:
    """Follow referenced top-level types and helpers through their source."""
    found: set[str] = set()
    pending = [node]
    while pending:
        current = pending.pop()
        names = {
            n.id
            for n in ast.walk(current)
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
        }
        for name in names & definitions.keys() - found:
            found.add(name)
            pending.append(definitions[name])
    return found


def resolve_target(
    packet: Packet,
    definitions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef],
) -> tuple[
    ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
    ast.FunctionDef | ast.AsyncFunctionDef,
]:
    parts = packet.target.qualified_function_name.split(".")
    owner = definitions[parts[0]]
    matches = (
        [owner]
        if len(parts) == 1
        else [
            n
            for n in owner.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and n.name == parts[1]
        ]
    )
    assert len(matches) == 1
    target = matches[0]
    assert isinstance(target, (ast.FunctionDef, ast.AsyncFunctionDef))

    return owner, target


def test_expected_keys_match_public_manifest() -> None:
    # Given
    keys = KEYS

    # When
    actual = set(keys)

    # Then
    assert len(keys) == len(actual) == 24
    assert actual == manifest_keys()
    assert {rule: sum(key.rule_id == rule for key in keys) for rule in RULES} == {
        "R1": 8,
        "R3": 8,
        "R4": 8,
    }


def test_shared_schema_is_json_object() -> None:
    # Given
    schema_bytes = (INPUTS / "response.schema.json").read_bytes()

    # When
    schema = json.loads(schema_bytes)

    # Then
    assert isinstance(schema, dict)


def test_exact_prompt_inventory() -> None:
    # Given
    expected = {"a.txt", "r1.txt", "r3.txt", "r4.txt"} | {
        f"c/{ident}.txt" for ident in PACKETS
    }

    # When
    actual = {str(path.relative_to(INPUTS)) for path in INPUTS.glob("*.txt")} | {
        str(path.relative_to(INPUTS)) for path in (INPUTS / "c").glob("*.txt")
    }

    # Then
    assert len(PACKETS) == 24
    assert actual == expected | {"prompt-template.txt"}
    assert {packet.target for packet in PACKETS.values()} == set(KEYS)


@pytest.mark.parametrize(
    "strategy,ident,rules",
    [("A", "a", RULES), *(("B", f"b-{rule.lower()}", (rule,)) for rule in RULES)],
    ids=["A", "B-R1", "B-R3", "B-R4"],
)
def test_whole_bundle_prompt_bytes(
    strategy: str, ident: str, rules: tuple[str, ...]
) -> None:
    # Given
    path = INPUTS / ("a.txt" if strategy == "A" else f"{rules[0].lower()}.txt")
    keys = [key for key in KEYS if key.rule_id in rules]

    # When
    actual = path.read_bytes()

    # Then
    assert actual == expected_prompt(strategy, ident, keys, rules, whole_bundle())


@pytest.mark.parametrize("ident,packet", list(PACKETS.items()), ids=list(PACKETS))
def test_focused_packet_preserves_source_bytes(ident: str, packet: Packet) -> None:
    # Given
    lines = (CORPUS / packet.target.file_id).read_bytes().splitlines(keepends=True)

    # When
    actual = (INPUTS / "c" / f"{ident}.txt").read_bytes()

    # Then
    assert packet.ranges == sorted(packet.ranges)
    assert all(1 <= start <= end <= len(lines) for start, end in packet.ranges)
    assert all(
        left[1] < right[0]
        for left, right in zip(packet.ranges, packet.ranges[1:], strict=False)
    )
    assert actual == expected_prompt(
        "C", ident, [packet.target], (packet.target.rule_id,), context_bytes(packet)
    )


@pytest.mark.parametrize("packet", list(PACKETS.values()), ids=list(PACKETS))
def test_focused_packet_covers_target_and_local_dependencies(packet: Packet) -> None:
    # Given
    tree = ast.parse((CORPUS / packet.target.file_id).read_bytes())
    nodes = [
        n
        for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]
    definitions = {n.name: n for n in nodes}
    assert len(definitions) == len(nodes)
    _, target = resolve_target(packet, definitions)

    # When
    local_dependencies = dependencies(target, definitions)

    # Then
    assert covered(
        packet, tree.body[0].lineno, tree.body[0].end_lineno or tree.body[0].lineno
    )
    assert covered(packet, node_start(target), target.end_lineno or target.lineno)
    assert all(
        covered(
            packet,
            node_start(definitions[name]),
            definitions[name].end_lineno or definitions[name].lineno,
        )
        for name in local_dependencies
    )
    assert all(
        covered(packet, n.lineno, n.end_lineno or n.lineno)
        for n in tree.body
        if isinstance(n, (ast.Import, ast.ImportFrom))
    )


@pytest.mark.parametrize(
    "packet",
    [packet for packet in PACKETS.values() if packet.target.rule_id == "R4"],
    ids=[ident for ident, packet in PACKETS.items() if packet.target.rule_id == "R4"],
)
def test_ledger_packet_covers_class_context(packet: Packet) -> None:
    # Given
    tree = ast.parse((CORPUS / packet.target.file_id).read_bytes())

    # When
    owner = next(
        n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Ledger"
    )

    # Then
    assert covered(packet, node_start(owner), owner.body[0].lineno)
