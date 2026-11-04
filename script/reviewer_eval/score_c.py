# SPDX-License-Identifier: Apache-2.0
"""Score retained C blocks offline against an explicitly frozen reference."""

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, TypedDict

from script.eval.model import FrozenPlan, PlannedCall
from script.reviewer_eval.context import c_target
from script.reviewer_eval.report import Inspection, Report, inspect_evidence
from script.reviewer_eval.scoring import Reference, read_reference
from script.reviewer_eval.validation import PublicPair


def digest(data: bytes) -> str:
    """Return the SHA-256 of bytes."""
    return sha256(data).hexdigest()


def bind(
    inspection: Inspection, manifest: dict[str, Any], reference: Reference, effort: str
) -> FrozenPlan:
    """Bind all reviewed packets.

    Returns:
        The bound plan.

    Raises:
        ValueError: Inventory or context is inconsistent.
    """
    plan = inspection.plan
    if plan is None or len(plan.calls) != 186 or len(inspection.report.calls) != 186:
        raise ValueError("unknown or incomplete plan inventory")
    if (
        manifest["rules"] != reference.rule_digests
        or {k: v["sha256"] for k, v in manifest["sources"].items()}
        != reference.source_digests
    ):
        raise ValueError("reference source or rule digest mismatch")
    functions = {f["function_file"]: f["sha256"] for f in manifest["functions"]}
    combinations = {
        PublicPair(c["rule_id"], c["file_id"], c["function_name"]): c
        for c in manifest["combinations"]
    }
    if len(functions) != 62 or len(combinations) != 186:
        raise ValueError("duplicate or incomplete manifest inventory")
    seen = set()
    for call in plan.calls:
        key = c_target(plan, call)
        if key in seen or key not in combinations or call.effort != effort:
            raise ValueError("duplicate, foreign, or wrong-effort target")
        seen.add(key)
        verify_packet(plan, call, combinations[key], functions, manifest)
    if seen != set(combinations) or not {c.key for c in reference.controls} <= seen:
        raise ValueError("missing public or indexed target")
    return plan


def verify_packet(
    plan: FrozenPlan,
    call: PlannedCall,
    combo: dict[str, Any],
    functions: dict[str, str],
    manifest: dict[str, Any],
) -> None:
    """Validate the exact public input snapshots and composed prompt.

    Raises:
        ValueError: A byte or path does not match the manifest.
    """
    shared, rule, function = (plan.snapshots[i] for i in call.context_indices)
    if (
        digest(shared.content) != manifest["shared_sha256"]
        or digest(function.content) != functions[combo["function_file"]]
        or Path(function.repository_path).name != combo["function_file"]
        or Path(rule.repository_path).name != combo["rule_file"]
    ):
        raise ValueError("C packet provenance mismatch")
    if (
        digest(call.prompt) != combo["prompt_sha256"]
        or call.prompt_sha256 != combo["prompt_sha256"]
        or len(call.prompt) != combo["prompt_bytes"]
    ):
        raise ValueError("C packet provenance mismatch")


class Detail(TypedDict):
    """Private result for one indexed opportunity."""

    position: int
    rule: str
    expected: str
    judgment: str | None
    exclusion: str | None


def score_block(
    root: Path,
    manifest: dict[str, Any],
    reference: Reference,
    effort: str,
    flags: set[int],
) -> tuple[list[Detail], Report]:
    """Apply boundary exclusions to one block.

    Returns:
        Private details and public inspection.

    Raises:
        ValueError: The block cannot be bound.
    """
    inspection = inspect_evidence(root)
    plan = bind(inspection, manifest, reference, effort)
    controls = {c.key: c.expected for c in reference.controls}
    details: list[Detail] = []
    for call, outcome in zip(plan.calls, inspection.report.calls, strict=True):
        key = c_target(plan, call)
        if key not in controls:
            continue
        exclusion = (
            "boundary"
            if call.position in flags
            else (None if outcome.state == "complete" else outcome.state)
        )
        judgment = outcome.assessments[0].judgement if outcome.assessments else None
        details.append({
            "position": call.position,
            "rule": key.rule_id,
            "expected": controls[key],
            "judgment": judgment,
            "exclusion": exclusion,
        })
    if len(details) != 24:
        raise ValueError("missing indexed control")
    return details, inspection.report


def summarize(details: list[Detail]) -> dict[str, int]:
    """Count fixed and eligible opportunities.

    Returns:
        Aggregate counts.
    """
    c: Counter[str] = Counter()
    for row in details:
        label = row["expected"]
        c[label.lower() + "_total"] += 1
        if row["exclusion"]:
            c[label.lower() + "_excluded"] += 1
            c["excluded_" + row["exclusion"]] += 1
            continue
        judgment = row["judgment"]
        c["judgment_" + str(judgment).lower()] += 1
        if label == "VIOLATION":
            c["caught" if judgment == label else "missed"] += 1
        else:
            c["correct_pass" if judgment == label else "pass_other"] += 1
            if judgment == "VIOLATION":
                c["false_positive"] += 1
    return dict(c)


def write_scores(
    runs: Path,
    output: Path,
    policy: dict[str, Any],
    manifest: dict[str, Any],
    reference: Reference,
    manifest_digest: str,
) -> None:
    """Write the bound private results to a new file.

    Raises:
        ValueError: A block has invalid evidence.
    """
    result: dict[str, Any] = {}
    for name in policy["blocks"]:
        details, report = score_block(
            runs / name,
            manifest,
            reference,
            name.split("-")[1],
            set(policy["boundary_affected_positions"][name]),
        )
        if report.counts is None or report.evidence_state == "invalid":
            raise ValueError("unknown or invalid run inventory")
        result[name] = {
            "details": details,
            "summary": summarize(details),
            "public_counts": report.counts.model_dump(),
        }
    with output.open("x") as stream:
        json.dump(
            {
                "manifest_sha256": manifest_digest,
                "reference_sha256": reference.digest,
                "blocks": result,
            },
            stream,
            indent=2,
        )
        stream.write("\n")


def main() -> None:
    """Write a fresh private score file.

    Raises:
        ValueError: A supplied digest is inconsistent.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    policy_raw = args.policy.read_bytes()
    if (
        digest(policy_raw)
        != "54b53c50aeadb554a2d46e36949e5b9647b1f09b36d99f52020fa422cbe0de57"
    ):
        raise ValueError("predeclared policy digest mismatch")
    policy = json.loads(policy_raw)
    raw = args.manifest.read_bytes()
    if digest(raw) != policy["manifest_sha256"]:
        raise ValueError("manifest digest mismatch")
    reference = read_reference(args.reference)
    if reference.digest != policy["private_index_sha256"]:
        raise ValueError("private reference digest mismatch")
    manifest = json.loads(raw)
    write_scores(args.runs, args.output, policy, manifest, reference, digest(raw))


if __name__ == "__main__":
    main()
