# SPDX-License-Identifier: Apache-2.0
"""Generate the static C public inputs without executing corpus code."""

import ast
from hashlib import sha256
import json
from pathlib import Path
from typing import TypedDict

from script.reviewer_eval.context import FILES
from script.reviewer_eval.validation import function_inventory

ROOT = Path(__file__).resolve().parents[2]
EVALUATION = ROOT / "doc/feat/reviewer/engineering/evaluation"
INPUTS = EVALUATION / "inputs"
CORPUS = EVALUATION / "corpus"
RULES = ("R1", "R3", "R4")
ORDERS = (
    ("none", "low", "medium", "high"),
    ("low", "medium", "high", "none"),
    ("medium", "high", "none", "low"),
)


class _Selection(TypedDict):
    start: int
    end: int
    role: str
    reasons: set[str]


class _Span(TypedDict):
    start: int
    end: int
    role: str
    reasons: list[str]
    sha256: str


class _Target(TypedDict):
    rule_id: str
    file_id: str
    function_name: str


class _Entry(TypedDict):
    packet: str
    target: _Target
    packet_sha256: str
    prompt_sha256: str
    prompt_bytes: int
    estimated_tokens: int
    spans: list[_Span]
    flags: list[str]


def _digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def _span(node: ast.stmt) -> tuple[int, int]:
    start = min([node.lineno, *(d.lineno for d in getattr(node, "decorator_list", []))])
    assert node.end_lineno is not None
    return start, node.end_lineno


def _add(
    node: ast.stmt,
    reason: str,
    role: str = "context",
    *,
    selection: dict[tuple[int, int], _Selection],
) -> None:
    start, end = _span(node)
    key = (start, end)
    if key in selection:
        selection[key]["reasons"].add(reason)
        if role == "target":
            selection[key]["role"] = role
    else:
        selection[key] = {
            "start": start,
            "end": end,
            "role": role,
            "reasons": {reason},
        }


def _add_dependencies(
    target: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
    module_names: dict[str, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef],
    selected: dict[tuple[int, int], _Selection],
) -> None:
    queue = [target]
    visited = set()
    while queue:
        node = queue.pop()
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                dep = module_names.get(child.id)
                if dep is not None and dep is not target and child.id not in visited:
                    visited.add(child.id)
                    _add(
                        dep,
                        "referenced module declaration or callee",
                        selection=selected,
                    )
                    queue.append(dep)


def _select_context(
    name: str,
    defs: dict[str, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef],
    parents: dict[str, tuple[str, ...]],
    globals_: list[ast.stmt],
    module_names: dict[str, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef],
) -> tuple[dict[tuple[int, int], _Selection], list[str]]:
    target = defs[name]
    selected: dict[tuple[int, int], _Selection] = {}
    flags = ["independent rule-specific context review required"]

    for node in globals_:
        _add(node, "module contract, import, or global declaration", selection=selected)
    for index in range(len(parents[name])):
        parent_name = ".".join(parents[name][: index + 1])
        parent = defs[parent_name]
        if isinstance(parent, ast.ClassDef):
            # Preserve the class header and declarations, excluding siblings.
            start, _ = _span(parent)
            first = parent.body[0].lineno
            selected[start, first - 1] = {
                "start": start,
                "end": first - 1,
                "role": "context",
                "reasons": {"enclosing class header"},
            }
            for item in parent.body:
                if not isinstance(
                    item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                ):
                    _add(item, "enclosing class declaration", selection=selected)
        else:
            _add(parent, "enclosing function and runtime control", selection=selected)
            flags.append(
                "nested target includes enclosing function; review granularity"
            )
    _add(target, "explicit target", "target", selection=selected)
    _add_dependencies(target, module_names, selected)

    return selected, flags


def _render_context(
    file_id: str,
    lines: list[bytes],
    selected: dict[tuple[int, int], _Selection],
    flags: list[str],
) -> tuple[bytes, list[_Span]]:
    spans: list[_Span] = []
    chunks = []
    for _, item in sorted(selected.items()):
        start, end = item["start"], item["end"]
        if end < start:
            continue
        data = b"".join(lines[start - 1 : end])
        spans.append({
            "start": start,
            "end": end,
            "role": item["role"],
            "reasons": sorted(item["reasons"]),
            "sha256": _digest(data),
        })
        chunks.append(
            (f"\n--- {file_id} lines {start}-{end} ({item['role']}) ---\n").encode()
            + data
        )
    context = b"".join(chunks)
    if sum(x["end"] - x["start"] + 1 for x in spans) >= len(lines) * 0.8:
        flags.append("context approaches whole module; review granularity")

    return context, spans


def _definitions(
    tree: ast.Module,
) -> tuple[
    dict[str, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef],
    dict[str, tuple[str, ...]],
]:
    defs: dict[str, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef] = {}
    parents: dict[str, tuple[str, ...]] = {}

    def visit(
        node: ast.AST,
        scope: tuple[str, ...] = (),
        *,
        definitions: dict[
            str, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
        ] = defs,
        enclosing: dict[str, tuple[str, ...]] = parents,
    ) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = ".".join((*scope, node.name))
            definitions[name] = node
            enclosing[name] = scope
            scope = (*scope, node.name)
        for child in ast.iter_child_nodes(node):
            visit(child, scope)

    visit(tree)
    return defs, parents


def _packet_entries(
    sources: dict[str, bytes], rules: dict[str, bytes], shared: bytes
) -> tuple[list[_Entry], dict[str, bytes]]:
    entries: list[_Entry] = []
    artifacts = {}
    for file_id, source in sources.items():
        lines = source.splitlines(keepends=True)
        tree = ast.parse(source)
        inventory = function_inventory(source)
        defs, parents = _definitions(tree)
        module_names = {
            n.name: n
            for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        }
        globals_: list[ast.stmt] = [
            n
            for n in tree.body
            if isinstance(n, (ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign))
            or (
                isinstance(n, ast.Expr)
                and isinstance(n.value, ast.Constant)
                and isinstance(n.value.value, str)
            )
        ]
        for name in sorted(inventory):
            selected, flags = _select_context(
                name, defs, parents, globals_, module_names
            )
            context, spans = _render_context(file_id, lines, selected, flags)
            for rule in RULES:
                meta: _Target = {
                    "rule_id": rule,
                    "file_id": file_id,
                    "function_name": name,
                }
                packet_name = f"{rule}--{file_id.replace('/', '--')}--{name}.txt"
                packet = (
                    b"Target: "
                    + json.dumps(meta, sort_keys=True, separators=(",", ":")).encode()
                    + b"\n\nRule:\n"
                    + rules[rule]
                    + b"\nContext:\n"
                    + context
                )
                artifacts["c-packets/" + packet_name] = packet
                prompt = shared + b"\n\n" + packet
                entries.append({
                    "packet": packet_name,
                    "target": meta,
                    "packet_sha256": _digest(packet),
                    "prompt_sha256": _digest(prompt),
                    "prompt_bytes": len(prompt),
                    "estimated_tokens": (len(prompt) + 3) // 4,
                    "spans": spans,
                    "flags": flags,
                })
    return entries, artifacts


def prepare() -> dict[str, bytes]:
    """Return deterministic public artifacts from frozen sources and rules."""
    sources = {name: (CORPUS / name).read_bytes() for name in FILES}
    rules = {r: (CORPUS / r.lower() / "rule.txt").read_bytes() for r in RULES}
    shared = (INPUTS / "c-shared/review-instructions-and-schema.txt").read_bytes()
    entries, artifacts = _packet_entries(sources, rules, shared)
    entries.sort(
        key=lambda e: (
            e["target"]["rule_id"],
            e["target"]["file_id"],
            e["target"]["function_name"],
        )
    )
    manifest = {
        "version": "static-c-context-v1",
        "sources": {
            name: {"sha256": _digest(data), "bytes": len(data)}
            for name, data in sources.items()
        },
        "rules": {r: _digest(data) for r, data in rules.items()},
        "shared_sha256": _digest(shared),
        "estimate_method": (
            "utf8-bytes-divided-by-four-v1: rough supplied-context "
            "proxy, not observed usage; excludes instructions and model framing"
        ),
        "per_effort_repetition_estimated_tokens": sum(
            e["estimated_tokens"] for e in entries
        ),
        "matrix_estimated_tokens": 12 * sum(e["estimated_tokens"] for e in entries),
        "packets": entries,
    }
    schedule = [
        {
            "position": i,
            "repetition": rep,
            "effort": effort,
            "packet": e["packet"],
            "prompt_sha256": e["prompt_sha256"],
        }
        for i, (rep, effort, e) in enumerate(
            (rep, effort, e)
            for rep, order in enumerate(ORDERS, 1)
            for effort in order
            for e in entries
        )
    ]
    artifacts["c-manifest.json"] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode()
    artifacts["c-schedule.json"] = (
        json.dumps(schedule, indent=2, sort_keys=True) + "\n"
    ).encode()
    return artifacts


def main() -> None:
    """Generate artifacts, or check retained bytes with --check.

    Raises:
        SystemExit: Retained artifacts disagree or extraneous packets exist.
    """
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    artifacts = prepare()
    expected = {INPUTS / p for p in artifacts}
    existing = set((INPUTS / "c-packets").glob("*.txt"))
    if args.check:
        if existing != {p for p in expected if p.parent.name == "c-packets"} or any(
            not p.is_file() or p.read_bytes() != content
            for p, content in ((INPUTS / n, b) for n, b in artifacts.items())
        ):
            raise SystemExit("C artifacts differ from deterministic generation")
    else:
        if existing - expected:
            raise SystemExit("unexpected packet files; refusing to remove them")
        for name, content in artifacts.items():
            path = INPUTS / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    print(  # ruff: ignore[print]
        f"Verified {len(artifacts) - 2} packets and 2232 prospective calls"
        if args.check
        else f"Generated {len(artifacts) - 2} packets and 2232 prospective calls"
    )


if __name__ == "__main__":
    main()
