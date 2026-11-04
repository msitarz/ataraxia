# SPDX-License-Identifier: Apache-2.0
"""Score one inspected run against an explicitly supplied private reference."""

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict

from script.eval.model import FrozenPlan, PlannedCall
from script.reviewer_eval.context import FILES, RULE, review_context
from script.reviewer_eval.report import CallOutcome, Inspection
from script.reviewer_eval.validation import Assessment, PublicPair, function_inventory

type Label = Literal["PASS", "VIOLATION"]
RULES = ("R1", "R3", "R4")
DIGEST = re.compile(r"^- `([^`]+)`: `([0-9a-f]{64})`$")


@dataclass(frozen=True, order=True)
class Control:
    """One private applicable classification control."""

    key: PublicPair
    expected: Label


@dataclass(frozen=True)
class Reference:
    """Private controls and byte provenance, never model input."""

    digest: str
    controls: tuple[Control, ...]
    source_digests: dict[str, str]
    rule_digests: dict[str, str]


class Rate(BaseModel):
    """An exact rate with its fixed or explicitly reduced denominator."""

    model_config = ConfigDict(frozen=True)
    numerator: int
    denominator: int
    value: float | None


class Measures(BaseModel):
    """Quality counts and secondary observation coverage."""

    model_config = ConfigDict(frozen=True)
    accuracy: Rate
    violation_recall: Rate
    correct_pass_rate: Rate
    pass_false_positive_rate: Rate
    valid_only_accuracy: Rate
    valid_only_violation_recall: Rate
    valid_only_correct_pass_rate: Rate
    valid_only_pass_false_positive_rate: Rate
    indexed_records: int
    determinate_records: int
    unknown: int
    not_applicable: int
    missing_records: int
    public_records: int
    public_expected: int | None
    public_coverage: Rate | None
    public_missing: int | None
    unindexed_records: int
    excluded_opportunities: int


class RuleScore(BaseModel):
    """Measures for one rule within a call or strategy."""

    model_config = ConfigDict(frozen=True)
    rule: str
    measures: Measures


class CallScore(BaseModel):
    """Scoring facts for one planned call."""

    model_config = ConfigDict(frozen=True)
    position: int
    model: str
    effort: str
    strategy: Literal["A", "B"]
    rules: tuple[str, ...]
    state: str
    measures: Measures
    per_rule: tuple[RuleScore, ...]


class StrategyScore(BaseModel):
    """One unambiguous strategy condition or an ambiguity diagnostic."""

    model_config = ConfigDict(frozen=True)
    model: str
    effort: str
    strategy: Literal["A", "B"]
    positions: tuple[int, ...]
    missing_required_rules: tuple[str, ...]
    diagnostic: str | None
    measures: Measures | None
    per_rule: tuple[RuleScore, ...] | None


class ScoreReport(BaseModel):
    """Private score report; draft labels are not independently approved."""

    model_config = ConfigDict(frozen=True)
    version: Literal[1] = 1
    run_id: str
    head_commit: str
    evidence_state: str
    evidence_diagnostic: str | None
    reference_sha256: str
    reference_status: str = "draft; not independently reviewed or frozen"
    source_sha256: dict[str, str]
    rule_sha256: dict[str, str]
    calls: tuple[CallScore, ...]
    strategies: tuple[StrategyScore, ...]
    scope: str = (
        "Classification agreement only; no semantic reasoning, quality screen, "
        "reference approval, or execution-boundary readiness is established."
    )


def read_reference(path: Path) -> Reference:
    """Read the initial private Markdown index and enforce its fixed controls.

    Returns:
        Validated controls and their byte provenance.
    """
    raw = path.read_bytes()
    lines = raw.decode("utf-8").splitlines()
    digests = _digests(lines)
    controls = _controls(lines)
    return _reference(raw, digests, controls)


def _controls(lines: list[str]) -> list[Control]:
    controls: list[Control] = []
    header = "| Rule | File | Function | Expected | Source-grounded rationale |"
    if lines.count(header) != 1:
        raise ValueError("reference must contain exactly one control table")
    start = lines.index(header)
    if start + 1 >= len(lines) or not re.fullmatch(
        r"\|(?:\s*-+\s*\|){5}", lines[start + 1]
    ):
        raise ValueError("invalid reference table separator")
    for line in lines[start + 2 :]:
        if not line.startswith("|"):
            break
        cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
        if len(cells) != 5 or not all(cells):
            raise ValueError("invalid reference control row")
        rule, file, function, expected, _ = cells
        if expected not in ("PASS", "VIOLATION"):
            raise ValueError("unsupported reference label")
        controls.append(Control(PublicPair(rule, file, function), expected))
    return controls


def _digests(lines: list[str]) -> dict[str, str]:
    digests: dict[str, str] = {}
    for line in lines:
        match = DIGEST.fullmatch(line)
        if match:
            name, digest = match.groups()
            if name in digests:
                raise ValueError("duplicate reference digest")
            digests[name] = digest
    return digests


def _reference(
    raw: bytes, digests: dict[str, str], controls: list[Control]
) -> Reference:
    sources = {name: digests[name] for name in FILES if name in digests}
    rule_paths = {rule: f"{rule.lower()}/rule.txt" for rule in RULES}
    rules = {
        rule: digests[path] for rule, path in rule_paths.items() if path in digests
    }
    if set(digests) != set(FILES) | set(rule_paths.values()):
        raise ValueError("reference digest inventory mismatch")
    if len({c.key for c in controls}) != len(controls):
        raise ValueError("duplicate reference control")
    counts = Counter((c.key.rule_id, c.key.file_id, c.expected) for c in controls)
    expected_counts = {
        (rule, file, label): 4
        for rule, file in zip(RULES, FILES, strict=True)
        for label in ("PASS", "VIOLATION")
    }
    if counts != expected_counts:
        raise ValueError("reference controls do not match initial distribution")
    return Reference(sha256(raw).hexdigest(), tuple(sorted(controls)), sources, rules)


def score_inspection(inspection: Inspection, reference: Reference) -> ScoreReport:
    """Bind and score an inspection; never trust an unrelated saved report.

    Returns:
        Private call and strategy scores.

    Raises:
        ValueError: The plan, reference, or response format cannot be scored.
    """
    plan = inspection.plan
    if plan is None or len(inspection.report.calls) != len(plan.calls):
        raise ValueError("unknown or inconsistent planned inventory")
    scored: list[tuple[CallScore, tuple[Control, ...], CallOutcome]] = []
    for planned, outcome in zip(plan.calls, inspection.report.calls, strict=True):
        rules, public_expected = _bind(plan, planned, reference)
        if outcome.response_format != "function-assessments-v2":
            raise ValueError("classification scoring requires function-assessments-v2")
        selected = tuple(c for c in reference.controls if c.key.rule_id in rules)
        strategy: Literal["A", "B"] = "A" if len(rules) == 3 else "B"
        measures = _measures(selected, ((selected, outcome),), public_expected)
        scored.append((
            CallScore(
                position=planned.position,
                model=planned.model,
                effort=planned.effort,
                strategy=strategy,
                rules=tuple(sorted(rules)),
                state=outcome.state,
                measures=measures,
                per_rule=_rule_scores(
                    selected, ((selected, outcome),), public_expected // len(rules)
                ),
            ),
            selected,
            outcome,
        ))
    return ScoreReport(
        run_id=plan.run_id,
        head_commit=plan.head_commit,
        evidence_state=inspection.report.evidence_state,
        evidence_diagnostic=inspection.report.diagnostic,
        reference_sha256=reference.digest,
        source_sha256=reference.source_digests,
        rule_sha256=reference.rule_digests,
        calls=tuple(sorted((c for c, _, _ in scored), key=lambda c: c.position)),
        strategies=_groups(scored, reference),
    )


def _groups(
    scored: list[tuple[CallScore, tuple[Control, ...], CallOutcome]],
    reference: Reference,
) -> tuple[StrategyScore, ...]:
    groups: list[StrategyScore] = []
    keys = sorted({(c.model, c.effort, c.strategy) for c, _, _ in scored})
    for model, effort, strategy in keys:
        members = [
            (c, controls, outcome)
            for c, controls, outcome in scored
            if (c.model, c.effort, c.strategy) == (model, effort, strategy)
        ]
        seen = [rule for c, _, _ in members for rule in c.rules]
        ambiguous = len(seen) != len(set(seen))
        missing = (
            tuple(rule for rule in RULES if rule not in seen) if strategy == "B" else ()
        )
        public_expected = members[0][0].measures.public_expected
        assert public_expected is not None
        groups.append(
            StrategyScore(
                model=model,
                effort=effort,
                strategy=strategy,
                positions=tuple(sorted(c.position for c, _, _ in members)),
                missing_required_rules=missing,
                diagnostic="repeated case; repetition identity is unknown"
                if ambiguous
                else None,
                per_rule=None
                if ambiguous
                else _rule_scores(
                    reference.controls,
                    tuple((controls, outcome) for _, controls, outcome in members),
                    public_expected // (3 if strategy == "A" else 1),
                ),
                measures=None
                if ambiguous
                else _measures(
                    reference.controls,
                    tuple((controls, outcome) for _, controls, outcome in members),
                    public_expected * (3 if strategy == "B" else 1),
                ),
            )
        )
    return tuple(groups)


def _rule_scores(
    controls: tuple[Control, ...],
    calls: tuple[tuple[tuple[Control, ...], CallOutcome], ...],
    public_expected: int,
) -> tuple[RuleScore, ...]:
    results: list[RuleScore] = []
    for rule in RULES:
        selected = tuple(c for c in controls if c.key.rule_id == rule)
        if not selected:
            continue
        rule_calls = tuple(
            _rule_call(rule, subset, outcome)
            for subset, outcome in calls
            if any(c.key.rule_id == rule for c in subset)
        )
        results.append(
            RuleScore(
                rule=rule, measures=_measures(selected, rule_calls, public_expected)
            )
        )
    return tuple(results)


def _rule_call(
    rule: str, subset: tuple[Control, ...], outcome: CallOutcome
) -> tuple[tuple[Control, ...], CallOutcome]:
    return (
        tuple(c for c in subset if c.key.rule_id == rule),
        outcome.model_copy(
            update={
                "assessments": tuple(
                    a for a in outcome.assessments if a.rule_id == rule
                ),
                "missing_pairs": tuple(
                    p for p in outcome.missing_pairs if p.rule_id == rule
                ),
            }
        ),
    )


def _bind(
    plan: FrozenPlan, call: PlannedCall, reference: Reference
) -> tuple[frozenset[str], int]:
    rules, sources = review_context(plan, call)
    function_count = 0
    for name, source in sources.items():
        if sha256(source).hexdigest() != reference.source_digests[name]:
            raise ValueError("reference source digest mismatch")
        names = function_inventory(source)
        function_count += len(names)
        if any(
            c.key.function_name not in names
            for c in reference.controls
            if c.key.file_id == name
        ):
            raise ValueError("reference function missing from source")
    case = plan.snapshots[call.context_indices[1]].content
    markers = list(RULE.finditer(case))
    if not markers or markers[0].start() != len(b"Rules:\n"):
        raise ValueError("invalid case rule envelope")
    for index, marker in enumerate(markers):
        rule = marker.group(1).decode("ascii")
        end = markers[index + 1].start() if index + 1 < len(markers) else len(case)
        if sha256(case[marker.end() : end]).hexdigest() != reference.rule_digests[rule]:
            raise ValueError("reference rule digest mismatch")
    return rules, function_count * len(rules)


def _rate(numerator: int, denominator: int) -> Rate:
    return Rate(
        numerator=numerator,
        denominator=denominator,
        value=numerator / denominator if denominator else None,
    )


def _measures(
    controls: tuple[Control, ...],
    calls: tuple[tuple[tuple[Control, ...], CallOutcome], ...],
    public_expected: int | None = None,
) -> Measures:
    expected = {c.key: c.expected for c in controls}
    counts: Counter[str] = Counter()
    _count_calls(calls, expected, counts)
    total = len(controls)
    passes = sum(c.expected == "PASS" for c in controls)
    violations = total - passes
    return Measures(
        accuracy=_rate(counts["correct"], total),
        violation_recall=_rate(counts["correct_VIOLATION"], violations),
        correct_pass_rate=_rate(counts["correct_PASS"], passes),
        pass_false_positive_rate=_rate(counts["false_positive"], passes),
        valid_only_accuracy=_rate(counts["correct"], counts["valid_total"]),
        valid_only_violation_recall=_rate(
            counts["correct_VIOLATION"], counts["valid_violation"]
        ),
        valid_only_correct_pass_rate=_rate(
            counts["correct_PASS"], counts["valid_pass"]
        ),
        valid_only_pass_false_positive_rate=_rate(
            counts["false_positive"], counts["valid_pass"]
        ),
        indexed_records=counts["indexed"],
        determinate_records=counts["PASS"] + counts["VIOLATION"],
        unknown=counts["UNKNOWN"],
        not_applicable=counts["NOT_APPLICABLE"],
        missing_records=total - counts["indexed"],
        public_records=counts["public"],
        public_expected=public_expected,
        public_coverage=_rate(counts["public"], public_expected)
        if public_expected is not None
        else None,
        public_missing=public_expected - counts["public"]
        if public_expected is not None
        else None,
        unindexed_records=counts["unindexed"],
        excluded_opportunities=total - counts["valid_total"],
    )


def _count_calls(
    calls: tuple[tuple[tuple[Control, ...], CallOutcome], ...],
    expected: dict[PublicPair, Label],
    counts: Counter[str],
) -> None:
    for selected, call in calls:
        selected_keys = {c.key for c in selected}
        if call.state == "complete":
            counts["valid_total"] += len(selected)
            counts["valid_pass"] += sum(c.expected == "PASS" for c in selected)
            counts["valid_violation"] += sum(
                c.expected == "VIOLATION" for c in selected
            )
        counts["public"] += len(call.assessments)
        for assessment in call.assessments:
            _count_assessment(assessment, selected_keys, expected, call.state, counts)


def _count_assessment(
    assessment: Assessment,
    selected_keys: set[PublicPair],
    expected: dict[PublicPair, Label],
    state: str,
    counts: Counter[str],
) -> None:
    key = PublicPair(assessment.rule_id, assessment.file_id, assessment.function_name)
    if key not in selected_keys:
        counts["unindexed"] += 1
        return
    counts["indexed"] += 1
    judgment = assessment.judgement
    counts[judgment] += 1
    if state != "complete":
        return
    if judgment == expected[key]:
        counts["correct"] += 1
        counts["correct_" + judgment] += 1
    if expected[key] == "PASS" and judgment == "VIOLATION":
        counts["false_positive"] += 1
