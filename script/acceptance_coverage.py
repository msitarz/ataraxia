# SPDX-License-Identifier: Apache-2.0
"""Validate Work acceptance declarations without executing tests."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import sys

from work_paths import resolve_work_file

ROOT = Path(__file__).resolve().parents[1]
_DECLARATION = re.compile(
    r"^ {0,3}-\s+\*\*(AC-[1-9][0-9]*) (TODO|DONE)\*\*(?:\s+(.*))?\s*$"
)
_POSSIBLE_DECLARATION = re.compile(r"^ {0,3}[-*+]\s+\*\*AC(?=[-\s0-9*])")
_LIST_ITEM = re.compile(r"^( *)([-*+])\s+")
_HEADING = re.compile(r"^ {0,3}#{1,6}(?:\s|$)")
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_VALIDATION = re.compile(r"^\s*Validation:\s*(.*)$")


@dataclass(frozen=True)
class Criterion:
    """A declared Work criterion and its declared validation method."""

    status: str
    has_validation: bool


def _markdown_lines(text: str) -> list[tuple[int, str]]:
    """Return source lines outside fenced Markdown code blocks."""
    result: list[tuple[int, str]] = []
    fence_char = ""
    fence_size = 0
    for number, line in enumerate(text.splitlines(), start=1):
        fence = _FENCE.match(line)
        if fence_char:
            if fence:
                marker = fence.group(1)
                if marker[0] == fence_char and len(marker) >= fence_size:
                    fence_char = ""
                    fence_size = 0
            continue
        if fence:
            marker = fence.group(1)
            fence_char = marker[0]
            fence_size = len(marker)
            continue
        result.append((number, line))
    return result


def _criterion_block(
    lines: list[tuple[int, str]], start: int, indent: int
) -> list[str]:
    """Collect one list item, stopping at its next sibling or heading.

    Returns:
        Lines belonging to the selected list item.
    """
    block: list[str] = []
    for _, line in lines[start:]:
        if block and _HEADING.match(line):
            break
        item = _LIST_ITEM.match(line)
        if block and item and len(item.group(1)) <= indent:
            break
        if block and line.strip() and not item:
            leading = len(line) - len(line.lstrip(" "))
            if leading < indent + 2:
                break
        block.append(line)
    return block


def _validation_for_criterion(
    block: list[str], work: str, line_number: int, ac: str
) -> tuple[bool, list[str]]:
    """Validate the optional non-test validation annotation for one criterion.

    Returns:
        Whether a non-empty validation method is declared and any errors.
    """
    annotations = [
        annotation.group(1).strip()
        for candidate in block
        if (annotation := _VALIDATION.match(candidate))
    ]
    errors: list[str] = []
    if any(not annotation for annotation in annotations):
        errors.append(
            f"{work}:{line_number}: {ac} Validation annotation needs a method"
        )
    if len(annotations) > 1:
        errors.append(f"{work}:{line_number}: {ac} has multiple Validation annotations")
    return any(annotations), errors


def parse_criteria(text: str, work: str) -> tuple[dict[str, Criterion], list[str]]:
    """Parse canonical AC list items and explicit non-test annotations.

    Returns:
        Criterion declarations and any malformed declaration diagnostics.
    """
    lines = _markdown_lines(text)
    criteria: dict[str, Criterion] = {}
    errors: list[str] = []
    declarations = 0
    for index, (line_number, line) in enumerate(lines):
        if not _POSSIBLE_DECLARATION.match(line):
            continue
        declarations += 1
        match = _DECLARATION.match(line)
        if not match:
            errors.append(
                f"{work}:{line_number}: malformed AC declaration; expected "
                "'- **AC-N TODO|DONE** description'"
            )
            continue
        ac, status, description = match.groups()
        if not description or not description.strip():
            errors.append(f"{work}:{line_number}: {ac} needs criterion text")
        if ac in criteria:
            errors.append(f"{work}:{line_number}: duplicate criterion {ac}")
            continue

        indent = len(line) - len(line.lstrip(" "))
        block = _criterion_block(lines, index, indent)
        has_validation, annotation_errors = _validation_for_criterion(
            block, work, line_number, ac
        )
        errors.extend(annotation_errors)
        criteria[ac] = Criterion(status, has_validation)

    if not declarations:
        errors.append(
            f"{work}: no AC declarations; expected one or more "
            "'- **AC-N TODO|DONE** description' list items"
        )
    return criteria, errors


def _criterion_report(ac: str, criterion: Criterion) -> str:
    """Describe a declared method without judging its outcome.

    Returns:
        A neutral summary of the criterion's declared method.
    """
    declaration = (
        "Validation method declared"
        if criterion.has_validation
        else "no Validation method declared"
    )
    return f"{ac} {criterion.status}: {declaration}"


def check_work(root: Path, work: str) -> tuple[list[str], list[str]]:
    """Validate declarations for one selected Work.

    Returns:
        Declaration errors and one declaration summary per criterion.
    """
    contract = resolve_work_file(root, work)
    criteria, errors = parse_criteria(contract.read_text(encoding="utf-8"), work)
    reports = [_criterion_report(ac, criterion) for ac, criterion in criteria.items()]
    return errors, reports


def main() -> int:
    """Check the Work selected by Make without running tests.

    Returns:
        A process status: zero on success, one for declaration errors, or two for
        invalid invocation arguments.
    """
    if len(sys.argv) != 2 or sys.argv[1] != "check":
        sys.stderr.write("usage: acceptance_coverage.py check\n")
        return 2
    work = os.environ.get("WORK", "")
    if os.environ.get("AC"):
        sys.stderr.write("AC is not supported; ac-check validates the full WORK\n")
        return 2
    try:
        errors, reports = check_work(ROOT, work)
    except ValueError as error:
        sys.stderr.write(f"{error}\n")
        return 2
    for report in reports:
        sys.stdout.write(f"{report}\n")
    for error in errors:
        sys.stderr.write(f"{error}\n")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
