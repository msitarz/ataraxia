# SPDX-License-Identifier: Apache-2.0
"""Scoring from synthetic inspected A/B plans."""

from hashlib import sha256

import pytest

from script.reviewer_eval.context import review_context
from script.reviewer_eval.report import CallOutcome, Inspection, Report
from script.reviewer_eval.scoring import Control, Reference, score_inspection
from script.reviewer_eval.validation import Assessment, PublicPair
from test.script.integration.reviewer_eval.support import plan


def _inspection(*, repeat: bool = False, b_case: bool = False) -> Inspection:
    frozen = plan(current=True, repeat=repeat)
    if b_case:
        snapshots = list(frozen.snapshots)
        snapshots[1] = snapshots[1].model_copy(
            update={
                "repository_path": (
                    "doc/feat/reviewer/engineering/evaluation/inputs/cases/B/r1.txt"
                ),
                "content": b"Rules:\n\n--- R1 ---\na\n",
            }
        )
        frozen = frozen.model_copy(update={"snapshots": tuple(snapshots)})
    calls = tuple(
        CallOutcome(
            position=c.position,
            model=c.model,
            effort=c.effort,
            state="complete",
            response_format="function-assessments-v2",
            assessments=(
                Assessment(
                    rule_id="R1",
                    file_id="r1/dispatch.py.txt",
                    function_name="a",
                    judgement="PASS",
                ),
            ),
        )
        for c in frozen.calls
    )
    report = Report(
        evidence_state="complete",
        diagnostic=None,
        run_id="run",
        head_commit="head",
        planned_count=len(calls),
        counts=None,
        calls=calls,
    )
    return Inspection(frozen, report)


def _reference(inspection: Inspection) -> Reference:
    assert inspection.plan is not None
    _, sources = review_context(inspection.plan, inspection.plan.calls[0])
    return Reference(
        digest="synthetic",
        controls=(
            Control(PublicPair("R1", "r1/dispatch.py.txt", "a"), "PASS"),
            Control(PublicPair("R3", "r3/planning.py.txt", "b"), "VIOLATION"),
            Control(PublicPair("R4", "r4/ledger.py.txt", "c"), "PASS"),
        ),
        source_digests={k: sha256(v).hexdigest() for k, v in sources.items()},
        rule_digests={
            "R1": sha256(b"a\n").hexdigest(),
            "R3": sha256(b"b\n").hexdigest(),
            "R4": sha256(b"c\n").hexdigest(),
        },
    )


def test_b_group_keeps_absent_rule_controls() -> None:
    """Given one B case, missing cases remain unobserved denominator."""
    inspection = _inspection(b_case=True)

    score = score_inspection(inspection, _reference(inspection))

    group = score.strategies[0]
    assert group.missing_required_rules == ("R3", "R4")
    assert group.measures is not None
    assert group.measures.accuracy.denominator == 3
    assert group.measures.excluded_opportunities == 2
    assert group.measures.public_expected == 9
    assert group.measures.public_records == 1
    assert group.measures.public_missing == 8
    assert group.per_rule is not None
    assert group.per_rule[1].measures.missing_records == 1
    assert score.calls[0].measures.accuracy.denominator == 1


def test_repeated_case_preserves_calls_but_not_aggregate() -> None:
    """Given repeated matching conditions, do not infer repetitions."""
    inspection = _inspection(repeat=True)

    score = score_inspection(inspection, _reference(inspection))

    assert len(score.calls) == 2
    assert score.strategies[0].measures is None
    assert score.strategies[0].diagnostic is not None


def test_stale_rule_is_unscorable() -> None:
    """Given a mismatched rule digest, do not issue a score."""
    inspection = _inspection()
    reference = _reference(inspection)
    reference.rule_digests["R1"] = "0" * 64

    with pytest.raises(ValueError, match="rule digest mismatch"):
        score_inspection(inspection, reference)


def test_stale_source_is_unscorable() -> None:
    """Given a mismatched source digest, reject scoring."""
    inspection = _inspection()
    reference = _reference(inspection)
    reference.source_digests["r1/dispatch.py.txt"] = "0" * 64

    with pytest.raises(ValueError, match="source digest mismatch"):
        score_inspection(inspection, reference)


def test_missing_reference_function_is_unscorable() -> None:
    """Given a nonexistent indexed function, reject scoring."""
    inspection = _inspection()
    reference = _reference(inspection)
    broken = Reference(
        digest=reference.digest,
        controls=(Control(PublicPair("R1", "r1/dispatch.py.txt", "absent"), "PASS"),),
        source_digests=reference.source_digests,
        rule_digests=reference.rule_digests,
    )

    with pytest.raises(ValueError, match="reference function missing"):
        score_inspection(inspection, broken)


def _complete_b_inventory() -> tuple[Inspection, Reference]:
    from script.reviewer_eval.context import FILES, PREFIX

    frozen = plan(current=True)
    source = b"".join(f"def f{i}(): pass\n".encode() for i in range(8))
    bundle = b"Context:\n" + b"".join(
        f"\n--- {file} (original lines 1-8) ---\n".encode() + source for file in FILES
    )
    snapshots = list(frozen.snapshots)
    snapshots[2] = snapshots[2].model_copy(
        update={"content": bundle, "content_sha256": sha256(bundle).hexdigest()}
    )
    case_contents = (b"a\n", b"b\n", b"c\n")
    rules = ("R1", "R3", "R4")
    case_snapshots = tuple(
        snapshots[1].model_copy(
            update={
                "repository_path": PREFIX + f"cases/B/{rule.lower()}.txt",
                "content": b"Rules:\n\n--- " + rule.encode() + b" ---\n" + content,
            }
        )
        for rule, content in zip(rules, case_contents, strict=True)
    )
    snapshots[1] = case_snapshots[0]
    snapshots.extend(case_snapshots[1:])
    calls = tuple(
        frozen.calls[0].model_copy(
            update={"position": i, "context_indices": (0, case, 2)}
        )
        for i, case in enumerate((1, 3, 4))
    )
    frozen = frozen.model_copy(update={"snapshots": tuple(snapshots), "calls": calls})
    outcomes = tuple(
        CallOutcome(
            position=position,
            model="model",
            effort="low",
            state="complete",
            response_format="function-assessments-v2",
            assessments=tuple(
                Assessment(
                    rule_id=rule,
                    file_id=file,
                    function_name=f"f{i}",
                    judgement="PASS" if i < 4 else "VIOLATION",
                )
                for file in FILES
                for i in range(8)
            ),
        )
        for position, rule in enumerate(rules)
    )
    report = Report(
        evidence_state="complete",
        diagnostic=None,
        run_id="run",
        head_commit="head",
        planned_count=3,
        counts=None,
        calls=outcomes,
    )
    controls = tuple(
        Control(PublicPair(rule, file, f"f{i}"), "PASS" if i < 4 else "VIOLATION")
        for rule, file in zip(rules, FILES, strict=True)
        for i in range(8)
    )
    reference = Reference(
        digest="synthetic",
        controls=controls,
        source_digests={file: sha256(source).hexdigest() for file in FILES},
        rule_digests={
            rule: sha256(content).hexdigest()
            for rule, content in zip(rules, case_contents, strict=True)
        },
    )
    return Inspection(frozen, report), reference


def test_complete_b_strategy_aggregates_fixed_control_denominators() -> None:
    """Given three distinct B cases, retain the complete strategy inventory."""
    inspection, reference = _complete_b_inventory()

    score = score_inspection(inspection, reference)

    group = score.strategies[0]
    assert group.missing_required_rules == ()
    assert group.measures is not None
    assert group.measures.accuracy.denominator == 24
    assert group.measures.violation_recall.denominator == 12
    assert group.measures.correct_pass_rate.denominator == 12
    assert group.measures.pass_false_positive_rate.denominator == 12
    assert group.measures.public_expected == 72
    assert group.measures.public_missing == 0
    assert group.per_rule is not None
    assert tuple(item.measures.accuracy.denominator for item in group.per_rule) == (
        8,
        8,
        8,
    )


def test_partial_b_strategy_counts_absent_public_inventory() -> None:
    """Given one of three B cases, retain both missing public inventories."""
    inspection, reference = _complete_b_inventory()
    assert inspection.plan is not None
    partial = Inspection(
        inspection.plan.model_copy(update={"calls": inspection.plan.calls[:1]}),
        inspection.report.model_copy(update={"calls": inspection.report.calls[:1]}),
    )

    score = score_inspection(partial, reference)

    group = score.strategies[0]
    assert group.missing_required_rules == ("R3", "R4")
    assert group.measures is not None
    assert group.measures.accuracy.denominator == 24
    assert group.measures.public_expected == 72
    assert group.measures.public_records == 24
    assert group.measures.public_missing == 48
