# SPDX-License-Identifier: Apache-2.0
"""Derive A/B/C validation inputs solely from frozen snapshots."""

from hashlib import sha256
import re
from typing import Literal

from script.eval.model import FrozenPlan, PlannedCall
from script.reviewer_eval.transcript import parse_json
from script.reviewer_eval.validation import PublicPair

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


RULE_DIGESTS = {
    "R1": "360b8eb6a305b79f8fc8894bf756f228eb2ccc4af3560c2ae6149f3a3d85d92d",
    "R3": "923ce9aba269ac4590aa106053f406cd148833e97766396bd2d94b0028eb9531",
    "R4": "bc9235e5533c2ec1b14e28e3213e497aabadd09eda6ddb14cd824b9ac4baebc0",
}


def _metadata(
    content: bytes, marker: bytes, keys: set[str]
) -> tuple[dict[str, str], bytes]:
    """Parse a strict metadata header and return its original body.

    Returns:
        Validated string fields and remaining bytes.

    Raises:
        ValueError: The envelope or metadata is invalid.
    """
    header, separator, body = content.partition(b"\n\n")
    if not separator or not header.startswith(marker):
        raise ValueError("invalid C metadata envelope")
    data = parse_json(header[len(marker) :])
    if (
        not isinstance(data, dict)
        or set(data) != keys
        or any(not isinstance(v, str) for v in data.values())
    ):
        raise ValueError("invalid C metadata fields")
    return data, body


def c_target(plan: FrozenPlan, call: PlannedCall) -> PublicPair:
    """Read the singleton target from the frozen C input snapshots.

    Returns:
        The explicitly supplied rule and function pair.

    Raises:
        ValueError: The C input metadata, rule, or paths are invalid.
    """
    selected = tuple(plan.snapshots[index] for index in call.context_indices)
    if (
        len(selected) != 3
        or selected[0].repository_path
        != PREFIX + "c-shared/review-instructions-and-schema.txt"
    ):
        raise ValueError("unsupported C prepared input paths")
    _, rule, function = selected
    rule_data, rule_body = _metadata(rule.content, b"Rule: ", {"rule_id"})
    function_data, function_body = _metadata(
        function.content, b"Function: ", {"file_id", "function_name"}
    )
    target = PublicPair(
        rule_data["rule_id"], function_data["file_id"], function_data["function_name"]
    )
    if (
        target.rule_id not in RULE_DIGESTS
        or target.file_id not in FILES
        or not target.function_name
    ):
        raise ValueError("invalid C target")
    if (
        rule.repository_path != PREFIX + "c-rules/" + target.rule_id + ".txt"
        or sha256(rule_body).hexdigest() != RULE_DIGESTS[target.rule_id]
    ):
        raise ValueError("C rule provenance mismatch")
    filename = f"{target.file_id.replace('/', '--')}--{target.function_name}.txt"
    if (
        function.repository_path != PREFIX + "c-functions/" + filename
        or not function_body.startswith(b"Context:\n")
    ):
        raise ValueError("C function provenance mismatch")
    return target
