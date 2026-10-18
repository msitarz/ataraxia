# SPDX-License-Identifier: Apache-2.0
"""Interpret parsed Markdown blocks as checked Work contract structure.

API:
``inspect_work`` returns a ``WorkInspection`` containing the document title,
checked criteria, and located ``WorkDiagnostic`` findings. Each
``WorkCriterion`` pairs a normalized criterion identity with its declared
``CriterionStatus``. ``WorkDiagnostic`` records a structural finding and
source line, while ``WorkInspection`` aggregates the title, valid criteria,
and findings for consumers. ``parse_criterion_status`` interprets one
canonical marker as ``CriterionStatus`` and raises ``ValueError`` for an
unsupported value. Together these values let validation, reporting, and
closure decisions share one interpretation.

Implementation:
The interpretation derives normalized top-level sections and criterion
declarations from the supplied Markdown blocks. It checks required sections,
criterion placement and heading shape, IDs, statuses, names, and outcome body
content, retaining valid criteria even when other declarations produce
findings. This module defines structure over already parsed blocks; it does
not parse Markdown source or read contract files.
"""

from dataclasses import dataclass
import re
from typing import Literal

from script.markdown.model import (
    ContainerBlock,
    HeadingBlock,
    MarkdownBlock,
    TextBlock,
    ThematicBreak,
)

type CriterionStatus = Literal["TODO", "DONE", "ABORT"]

_CRITERION = re.compile(r"^\*\*AC-([0-9]+) (\S+)\*\*(?:\s+(.*))?$")
_AC_LIKE = re.compile(r"^\*{0,2}AC-")
_REQUIRED_SECTIONS = ("Purpose", "Goals", "Acceptance criteria")


@dataclass(frozen=True)
class WorkDiagnostic:
    """A structural finding with a one-based source line."""

    line: int
    rule: str
    context: str


@dataclass(frozen=True)
class WorkCriterion:
    """A checked criterion identity and status."""

    identifier: str
    status: CriterionStatus


@dataclass(frozen=True)
class WorkInspection:
    """One parsed Work interpretation with findings and closure fields."""

    title: str | None
    criteria: tuple[WorkCriterion, ...]
    diagnostics: tuple[WorkDiagnostic, ...]


@dataclass(frozen=True)
class _LocatedHeading:
    """A normalized top-level heading with its structural end positions."""

    index: int
    block: HeadingBlock
    text: str
    section_end: int
    outcome_end: int


@dataclass(frozen=True)
class _DeclarationResult:
    """The fields and findings derived from one criterion-like heading."""

    identifier: str | None
    criterion: WorkCriterion | None
    findings: tuple[WorkDiagnostic, ...]


@dataclass(frozen=True)
class _CriterionInspection:
    """Criterion values and findings from the declaration scan."""

    criteria: tuple[WorkCriterion, ...]
    findings: tuple[WorkDiagnostic, ...]
    declarations: int


def inspect_work(blocks: tuple[MarkdownBlock, ...]) -> WorkInspection:
    """Interpret Work structure once for diagnostics and closure decisions.

    Returns:
        The title, checked criteria, and structural findings from one pass.
    """
    headings = _located_headings(blocks)
    title = _work_title(headings)
    criteria, findings = _structural_findings(blocks, headings, title)
    ordered_findings = tuple(
        sorted(findings, key=lambda item: (item.line, item.rule, item.context))
    )
    return WorkInspection(
        title.text if title is not None and title.text else None,
        criteria,
        ordered_findings,
    )


def _work_title(headings: tuple[_LocatedHeading, ...]) -> _LocatedHeading | None:
    return next(
        (heading for heading in headings if heading.block.heading_level == 1), None
    )


def _structural_findings(
    blocks: tuple[MarkdownBlock, ...],
    headings: tuple[_LocatedHeading, ...],
    title: _LocatedHeading | None,
) -> tuple[tuple[WorkCriterion, ...], list[WorkDiagnostic]]:
    findings = _work_name_findings(title)
    sections = _required_sections(headings)
    findings.extend(_required_section_findings(blocks, sections))
    criteria = _criterion_findings(blocks, headings, sections["Acceptance criteria"])
    findings.extend(criteria.findings)
    return criteria.criteria, findings


def _work_name_findings(title: _LocatedHeading | None) -> list[WorkDiagnostic]:
    if title is None:
        return [WorkDiagnostic(1, "required level-one Work name", "file start")]
    if not title.text:
        return [
            WorkDiagnostic(
                title.block.location.line_start,
                "nonempty Work name",
                "level-one heading",
            )
        ]
    return []


def _required_sections(
    headings: tuple[_LocatedHeading, ...],
) -> dict[str, list[_LocatedHeading]]:
    sections: dict[str, list[_LocatedHeading]] = {
        name: [] for name in _REQUIRED_SECTIONS
    }
    for heading in headings:
        if heading.block.heading_level == 2 and heading.text in sections:
            sections[heading.text].append(heading)
    return sections


def parse_criterion_status(value: str) -> CriterionStatus:
    """Parse one canonical Work criterion status marker.

    Returns:
        The parsed status.

    Raises:
        ValueError: The marker is not supported.
    """
    match value:
        case "TODO":
            return "TODO"
        case "DONE":
            return "DONE"
        case "ABORT":
            return "ABORT"
        case _:
            raise ValueError(f"unsupported criterion status: {value}")


def _required_section_findings(
    blocks: tuple[MarkdownBlock, ...],
    sections: dict[str, list[_LocatedHeading]],
) -> tuple[WorkDiagnostic, ...]:
    """Collect missing, duplicate, and empty required-section findings.

    Returns:
        Findings for all required sections.
    """
    findings: list[WorkDiagnostic] = []
    for name in _REQUIRED_SECTIONS:
        matches = sections[name]
        if not matches:
            findings.append(
                WorkDiagnostic(1, f"required top-level section '{name}'", "file start")
            )
        else:
            findings.extend(
                WorkDiagnostic(
                    duplicate.block.location.line_start,
                    f"duplicate top-level section '{name}'",
                    duplicate.block.text,
                )
                for duplicate in matches[1:]
            )
            for heading in matches:
                findings.extend(_nonempty_section(blocks, heading))
    return tuple(findings)


def _located_headings(blocks: tuple[MarkdownBlock, ...]) -> tuple[_LocatedHeading, ...]:
    raw = tuple(
        (index, block, block.text.strip())
        for index, block in enumerate(blocks)
        if isinstance(block, HeadingBlock)
    )
    located: list[_LocatedHeading] = []
    for position, (index, block, text) in enumerate(raw):
        following = raw[position + 1 :]
        section_end = next(
            (
                later_index
                for later_index, later, _ in following
                if later.heading_level <= 2
            ),
            len(blocks),
        )
        outcome_end = next(
            (
                later_index
                for later_index, later, _ in following
                if later.heading_level <= 3
            ),
            len(blocks),
        )
        located.append(_LocatedHeading(index, block, text, section_end, outcome_end))
    return tuple(located)


def _nonempty_section(
    blocks: tuple[MarkdownBlock, ...], heading: _LocatedHeading
) -> tuple[WorkDiagnostic, ...]:
    if any(
        _has_content(block) for block in blocks[heading.index + 1 : heading.section_end]
    ):
        return ()
    return (
        WorkDiagnostic(
            heading.block.location.line_start,
            f"nonempty '{heading.text}' section",
            heading.block.text,
        ),
    )


def _criterion_findings(
    blocks: tuple[MarkdownBlock, ...],
    headings: tuple[_LocatedHeading, ...],
    acceptance: list[_LocatedHeading],
) -> _CriterionInspection:
    scan = _criterion_declarations(blocks, headings)
    findings: list[WorkDiagnostic] = []
    findings.extend(scan.findings)
    if len(acceptance) == 1 and scan.declarations == 0:
        section = acceptance[0]
        findings.append(
            WorkDiagnostic(
                section.block.location.line_start,
                "at least one criterion declaration",
                "Acceptance criteria",
            )
        )
    return _CriterionInspection(scan.criteria, tuple(findings), scan.declarations)


def _criterion_declarations(
    blocks: tuple[MarkdownBlock, ...], headings: tuple[_LocatedHeading, ...]
) -> _CriterionInspection:
    findings: list[WorkDiagnostic] = []
    criteria: list[WorkCriterion] = []
    identifiers: set[str] = set()
    declarations = 0
    in_acceptance = False
    for heading in headings:
        level = heading.block.heading_level
        if level == 1:
            in_acceptance = False
        elif level == 2:
            in_acceptance = heading.text == "Acceptance criteria"

        looks_like_criterion = bool(_AC_LIKE.match(heading.text))
        inside_acceptance = level > 2 and in_acceptance
        is_declaration = level == 3 and inside_acceptance
        if not is_declaration and not looks_like_criterion:
            continue
        if is_declaration:
            declarations += 1
        body = blocks[heading.index + 1 : heading.outcome_end]
        result = _criterion_result(
            heading.block,
            heading.text,
            body,
            inside_acceptance,
            frozenset(identifiers),
        )
        findings.extend(result.findings)
        if result.identifier is not None:
            identifiers.add(result.identifier)
        if result.criterion is not None:
            criteria.append(result.criterion)

    return _CriterionInspection(tuple(criteria), tuple(findings), declarations)


def _criterion_result(
    heading: HeadingBlock,
    text: str,
    body: tuple[MarkdownBlock, ...],
    inside_acceptance: bool,
    known_identifiers: frozenset[str],
) -> _DeclarationResult:
    line = heading.location.line_start
    context = heading.text
    constraints: list[tuple[bool, str]] = [
        (inside_acceptance, "criterion must be inside Acceptance criteria"),
        (
            heading.heading_level == 3,
            "criterion declaration must use a level-three heading",
        ),
    ]

    shape_match = _CRITERION.fullmatch(text)
    if shape_match is None:
        constraints.append((
            False,
            "criterion heading format '### **AC-N STATUS** Outcome name'",
        ))
        normalized_id = None
        criterion_status = None
    else:
        identifier, status, name = shape_match.groups()
        normalized_id = identifier.lstrip("0") or "0"
        try:
            criterion_status = parse_criterion_status(status)
        except ValueError:
            criterion_status = None
        constraints.extend((
            (normalized_id != "0", "positive decimal criterion ID"),
            (
                normalized_id not in known_identifiers,
                f"unique criterion ID AC-{normalized_id}",
            ),
            (
                criterion_status is not None,
                "supported status TODO, DONE, or ABORT",
            ),
            (bool((name or "").strip()), "nonempty criterion name"),
            (
                any(_has_content(block) for block in body),
                "nonempty criterion outcome body",
            ),
        ))

    findings = tuple(
        WorkDiagnostic(line, rule, context) for valid, rule in constraints if not valid
    )
    criterion = None
    if not findings and normalized_id is not None and criterion_status is not None:
        criterion = WorkCriterion(f"AC-{normalized_id}", criterion_status)
    return _DeclarationResult(normalized_id, criterion, findings)


def _has_content(block: MarkdownBlock) -> bool:
    match block:
        case TextBlock(kind="html_block"):
            return bool(re.sub(r"<!--.*?-->", "", block.text, flags=re.DOTALL).strip())
        case TextBlock(text=text):
            return bool(text.strip())
        case ContainerBlock(children=children):
            return any(_has_content(child) for child in children)
        case HeadingBlock() | ThematicBreak():
            return False
