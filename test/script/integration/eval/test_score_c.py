# SPDX-License-Identifier: Apache-2.0
"""C analysis binds public packets and applies synthetic quality gates."""

import json
from pathlib import Path
from typing import Any

import pytest

from script.reviewer_eval.report import CallOutcome, Inspection, Report
from script.reviewer_eval.score_c import Detail, bind, summarize
from script.reviewer_eval.scoring import Control, Reference
from script.reviewer_eval.validation import PublicPair
from test.script.integration.eval.test_prepared_reviewer_c import (
    FUNCTIONS,
    INPUTS,
    RULE_FILES,
    SHARED,
    _plan,
)


@pytest.fixture
def packet() -> tuple[Inspection, dict[str, Any], Reference]:
    """Compose real public packet bytes with invented private labels."""
    manifest = json.loads((INPUTS / "c-manifest.json").read_bytes())
    plan = _plan([[SHARED], RULE_FILES, FUNCTIONS])
    calls = tuple(
        CallOutcome(
            position=c.position, model=c.model, effort=c.effort, state="complete"
        )
        for c in plan.calls
    )
    report = Report(
        evidence_state="complete",
        diagnostic=None,
        run_id="test",
        head_commit="head",
        planned_count=186,
        counts=None,
        calls=calls,
    )
    entries = manifest["combinations"][:24]
    controls = tuple(
        Control(PublicPair(c["rule_id"], c["file_id"], c["function_name"]), "PASS")
        for c in entries
    )
    ref = Reference(
        "synthetic",
        controls,
        {k: v["sha256"] for k, v in manifest["sources"].items()},
        manifest["rules"],
    )
    return Inspection(plan, report), manifest, ref


def test_binding_accepts_complete_public_plan(
    packet: tuple[Inspection, dict[str, Any], Reference],
) -> None:
    # Given a public plan and synthetic controls.
    inspection, manifest, reference = packet

    # When binding the complete plan.
    result = bind(inspection, manifest, reference, "low")

    # Then it retains all planned calls.
    assert len(result.calls) == 186


def test_binding_rejects_duplicate_target(
    packet: tuple[Inspection, dict[str, Any], Reference],
) -> None:
    # Given a plan containing a duplicated target and a missing target.
    inspection, manifest, reference = packet
    assert inspection.plan is not None
    plan = inspection.plan.model_copy(
        update={
            "calls": (
                inspection.plan.calls[0],
                *inspection.plan.calls[1:-1],
                inspection.plan.calls[0],
            )
        }
    )

    # When binding it, then the incomplete coverage is rejected.
    with pytest.raises(ValueError, match="duplicate"):
        bind(Inspection(plan, inspection.report), manifest, reference, "low")


def test_binding_rejects_foreign_context(
    packet: tuple[Inspection, dict[str, Any], Reference],
) -> None:
    # Given a manifest whose packet hash is foreign to the frozen plan.
    inspection, manifest, reference = packet
    manifest["combinations"][0]["prompt_sha256"] = "0" * 64

    # When binding it, then no score can be returned.
    with pytest.raises(ValueError, match="provenance"):
        bind(inspection, manifest, reference, "low")


def test_binding_rejects_missing_indexed_target(
    packet: tuple[Inspection, dict[str, Any], Reference],
) -> None:
    # Given a synthetic reference key outside the public plan.
    inspection, manifest, reference = packet
    reference = Reference(
        reference.digest,
        (*reference.controls, Control(PublicPair("R1", "foreign", "f"), "PASS")),
        reference.source_digests,
        reference.rule_digests,
    )

    # When binding it, then missing indexed coverage is rejected.
    with pytest.raises(ValueError, match="indexed"):
        bind(inspection, manifest, reference, "low")


def test_exclusions_keep_fixed_denominators_and_uncertainty_distinct() -> None:
    # Given synthetic controls with invalid and boundary exclusions.
    rows: list[Detail] = [
        {
            "position": 0,
            "rule": "R1",
            "expected": "VIOLATION",
            "judgment": "VIOLATION",
            "exclusion": "boundary",
        },
        {
            "position": 1,
            "rule": "R1",
            "expected": "PASS",
            "judgment": None,
            "exclusion": "invalid",
        },
        {
            "position": 2,
            "rule": "R1",
            "expected": "VIOLATION",
            "judgment": "UNKNOWN",
            "exclusion": None,
        },
        {
            "position": 3,
            "rule": "R1",
            "expected": "PASS",
            "judgment": "NOT_APPLICABLE",
            "exclusion": None,
        },
    ]

    # When calculating the counts.
    result = summarize(rows)

    # Then exclusions stay in the fixed totals and uncertainty is not credited.
    assert result == {
        "violation_total": 2,
        "violation_excluded": 1,
        "excluded_boundary": 1,
        "pass_total": 2,
        "pass_excluded": 1,
        "excluded_invalid": 1,
        "judgment_unknown": 1,
        "missed": 1,
        "judgment_not_applicable": 1,
        "pass_other": 1,
    }


def test_binding_rejects_reference_digest_mismatch(
    packet: tuple[Inspection, dict[str, Any], Reference],
) -> None:
    # Given a reference with different source provenance.
    inspection, manifest, reference = packet
    foreign = Reference(
        reference.digest, reference.controls, {}, reference.rule_digests
    )

    # When binding it, then the mismatch is rejected.
    with pytest.raises(ValueError, match="digest mismatch"):
        bind(inspection, manifest, foreign, "low")


def test_block_excludes_invalid_and_denied_calls_before_credit(
    packet: tuple[Inspection, dict[str, Any], Reference],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given valid singleton outputs and two synthetic excluded controls.
    from script.reviewer_eval.context import c_target
    from script.reviewer_eval.score_c import score_block
    from script.reviewer_eval.validation import Assessment

    inspection, manifest, reference = packet
    assert inspection.plan is not None
    outcomes = []
    controlled = {c.key for c in reference.controls}
    positions = []
    for call in inspection.plan.calls:
        key = c_target(inspection.plan, call)
        if key in controlled:
            positions.append(call.position)
        assessment = Assessment(
            rule_id=key.rule_id,
            file_id=key.file_id,
            function_name=key.function_name,
            judgement="PASS",
        )
        outcomes.append(
            CallOutcome(
                position=call.position,
                model=call.model,
                effort=call.effort,
                state="complete",
                assessments=(assessment,),
            )
        )
    outcomes[positions[1]] = outcomes[positions[1]].model_copy(
        update={"state": "invalid", "assessments": ()}
    )
    report = inspection.report.model_copy(update={"calls": tuple(outcomes)})

    def inspect_synthetic(_root: Path) -> Inspection:
        return Inspection(inspection.plan, report)

    monkeypatch.setattr(
        "script.reviewer_eval.score_c.inspect_evidence", inspect_synthetic
    )

    # When scoring with a boundary denial and invalid response.
    details, _ = score_block(Path("unused"), manifest, reference, "low", {positions[0]})

    # Then both remain in the fixed total and receive no correct-PASS credit.
    result = summarize(details)
    assert result["pass_total"] == 24
    assert result["correct_pass"] == 22
    assert result["pass_excluded"] == 2
    assert result["excluded_boundary"] == result["excluded_invalid"] == 1
