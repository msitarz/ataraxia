# SPDX-License-Identifier: Apache-2.0
"""Pure structural rules for active Work contracts."""

from dataclasses import dataclass
import re
from typing import Literal, get_args

from script.markdown.model import (
    ContainerBlock,
    HeadingBlock,
    MarkdownBlock,
    TextBlock,
    ThematicBreak,
)

type CriterionStatus = Literal["TODO", "DONE"]

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
    findings: tuple[WorkDiagnostic, ...]


def check_work(blocks: tuple[MarkdownBlock, ...]) -> tuple[WorkDiagnostic, ...]:
    """Return deterministic structural findings for one parsed Work contract."""
    headings = _located_headings(blocks)
    findings: list[WorkDiagnostic] = []
    title = next(
        (heading for heading in headings if heading.block.heading_level == 1), None
    )
    if title is None:
        findings.append(WorkDiagnostic(1, "required level-one Work name", "file start"))
    elif not title.text:
        findings.append(
            WorkDiagnostic(
                title.block.location.line_start,
                "nonempty Work name",
                "level-one heading",
            )
        )

    sections: dict[str, list[_LocatedHeading]] = {
        name: [] for name in _REQUIRED_SECTIONS
    }
    for heading in headings:
        if heading.block.heading_level == 2 and heading.text in sections:
            sections[heading.text].append(heading)
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

    findings.extend(
        _criterion_findings(blocks, headings, sections["Acceptance criteria"])
    )
    return tuple(
        sorted(findings, key=lambda item: (item.line, item.rule, item.context))
    )


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
) -> tuple[WorkDiagnostic, ...]:
    findings: list[WorkDiagnostic] = []
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

    if len(acceptance) == 1 and declarations == 0:
        section = acceptance[0]
        findings.append(
            WorkDiagnostic(
                section.block.location.line_start,
                "at least one criterion declaration",
                "Acceptance criteria",
            )
        )
    return tuple(findings)


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
    else:
        identifier, status, name = shape_match.groups()
        normalized_id = identifier.lstrip("0") or "0"
        constraints.extend((
            (normalized_id != "0", "positive decimal criterion ID"),
            (
                normalized_id not in known_identifiers,
                f"unique criterion ID AC-{normalized_id}",
            ),
            (
                status in get_args(CriterionStatus.__value__),
                "supported status TODO or DONE",
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
    return _DeclarationResult(normalized_id, findings)


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
