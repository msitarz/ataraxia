# SPDX-License-Identifier: Apache-2.0
"""Derive initial A/B validation inputs solely from frozen snapshots."""

import re

from script.eval.model import FrozenPlan, PlannedCall

PREFIX = "doc/feat/reviewer/engineering/evaluation/inputs/"
SHARED = PREFIX + "shared/review-instructions-and-schema.txt"
CORPUS = PREFIX + "corpus/source.txt"
CASES = {
    PREFIX + "cases/A/a.txt": frozenset({"R1", "R3", "R4"}),
    PREFIX + "cases/B/r1.txt": frozenset({"R1"}),
    PREFIX + "cases/B/r3.txt": frozenset({"R3"}),
    PREFIX + "cases/B/r4.txt": frozenset({"R4"}),
}
FILES = ("r1/dispatch.py.txt", "r3/planning.py.txt", "r4/ledger.py.txt")
HEADER = re.compile(rb"\n--- ([^\n]+) \(original lines 1-([0-9]+)\) ---\n")
RULE = re.compile(rb"\n--- (R[0-9]+) ---\n")


def review_context(
    plan: FrozenPlan, call: PlannedCall
) -> tuple[frozenset[str], dict[str, bytes]]:
    """Return case rule IDs and original bundle bytes for this planned call.

    Raises:
        ValueError: The frozen prepared inputs have an unsupported shape.
    """
    selected = tuple(plan.snapshots[index] for index in call.context_indices)
    if len(selected) != 3:
        raise ValueError("expected shared, case and corpus snapshots")
    shared, case, corpus = selected
    if shared.repository_path != SHARED or corpus.repository_path != CORPUS:
        raise ValueError("unsupported prepared input paths")
    allowed = CASES.get(case.repository_path)
    if allowed is None:
        raise ValueError("unsupported prepared case path")
    markers = RULE.findall(case.content)
    if not case.content.startswith(b"Rules:\n") or len(markers) != len(allowed):
        raise ValueError("invalid case rule envelope")
    if frozenset(marker.decode("ascii") for marker in markers) != allowed:
        raise ValueError("case rule markers do not match case")
    return allowed, _sources(corpus.content)


def _sources(bundle: bytes) -> dict[str, bytes]:
    matches = list(HEADER.finditer(bundle))
    if not bundle.startswith(b"Context:\n") or len(matches) != len(FILES):
        raise ValueError("invalid source bundle headers")
    if matches[0].start() != len(b"Context:\n"):
        raise ValueError("unexpected source bundle preamble")
    result: dict[str, bytes] = {}
    for index, (match, expected) in enumerate(zip(matches, FILES, strict=True)):
        if match.group(1) != expected.encode():
            raise ValueError("unexpected source bundle file")
        end = matches[index + 1].start() if index + 1 < len(matches) else len(bundle)
        source = bundle[match.end() : end]
        if source.count(b"\n") + int(
            bool(source) and not source.endswith(b"\n")
        ) != int(match.group(2)):
            raise ValueError(f"source line count mismatch: {expected}")
        result[expected] = source
    return result
