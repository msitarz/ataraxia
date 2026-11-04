# SPDX-License-Identifier: Apache-2.0
"""Derive initial A/B validation inputs solely from frozen snapshots."""

from hashlib import sha256
import json
import re
from typing import Literal

from script.eval.model import FrozenPlan, PlannedCall

type ResponseFormat = Literal[
    "findings-v1", "function-assessments-v2", "function-assessments-c-v1"
]

FROZEN_FORMAT_DIGESTS: dict[str, ResponseFormat] = {
    "e4c7d5af160bd566f35b165f20617724fdfac665b39c0bbd5653b114323e79e6": (
        "function-assessments-c-v1"
    ),
    "225cbbcd66d1cb8a2d7df16d7810d39a5b06e188ffd0ed4b5ac07d2627246477": "findings-v1",
    "2c464b98b96d562f3dbef2cc5e3d9515ebb0c7b58f9777fa5e1133f11f7c632f": (
        "function-assessments-v2"
    ),
}

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
    if response_format(plan, call) == "function-assessments-c-v1":
        target = c_target(plan, call)
        return frozenset({target.rule_id}), {}
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


def response_format(plan: FrozenPlan, call: PlannedCall) -> ResponseFormat:
    """Select a supported contract from the exact frozen shared prompt bytes.

    Returns:
        The supported response format.

    Raises:
        ValueError: The frozen prompt is unknown or inconsistent.
    """
    shared = plan.snapshots[call.context_indices[0]]
    digest = sha256(shared.content).hexdigest()
    try:
        return FROZEN_FORMAT_DIGESTS[digest]
    except KeyError as exc:
        raise ValueError("unsupported or inconsistent frozen response format") from exc


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


def c_target(plan: FrozenPlan, call: PlannedCall):
    """Read the singleton target from frozen C packet provenance.

    Returns:
        The explicitly supplied public pair.

    Raises:
        ValueError: The C packet or target provenance is invalid.
    """
    from script.reviewer_eval.validation import PublicPair

    selected = tuple(plan.snapshots[index] for index in call.context_indices)
    if (
        len(selected) != 2
        or selected[0].repository_path
        != PREFIX + "c-shared/review-instructions-and-schema.txt"
    ):
        raise ValueError("unsupported C prepared input paths")
    packet = selected[1]
    if not packet.repository_path.startswith(PREFIX + "c-packets/"):
        raise ValueError("unsupported C packet path")
    header, separator, rest = packet.content.partition(b"\n\nRule:\n")
    if (
        not separator
        or not header.startswith(b"Target: ")
        or b"\nContext:\n" not in rest
    ):
        raise ValueError("invalid C packet envelope")
    try:
        pairs = json.loads(
            header[len(b"Target: ") :], object_pairs_hook=lambda values: values
        )
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("invalid C target JSON") from exc
    if (
        not isinstance(pairs, list)
        or len(pairs) != 3
        or any(not isinstance(pair, tuple) or len(pair) != 2 for pair in pairs)
    ):
        raise ValueError("invalid C target metadata")
    if {k for k, _ in pairs} != {"rule_id", "file_id", "function_name"} or any(
        not isinstance(v, str) for _, v in pairs
    ):
        raise ValueError("invalid C target fields")
    target = PublicPair(**dict(pairs))
    if (
        target.rule_id not in {"R1", "R3", "R4"}
        or target.file_id not in FILES
        or not target.function_name
    ):
        raise ValueError("invalid C target")
    filename = (
        f"{target.rule_id}--{target.file_id.replace('/', '--')}--"
        f"{target.function_name}.txt"
    )
    if packet.repository_path != PREFIX + "c-packets/" + filename:
        raise ValueError("C target does not match packet path")
    return target
