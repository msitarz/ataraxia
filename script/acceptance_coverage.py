# SPDX-License-Identifier: Apache-2.0
"""Check declared Work acceptance coverage without executing tests."""

from __future__ import annotations

import ast
from dataclasses import dataclass
import os
from pathlib import Path
import re
import sys

from work_paths import resolve_work_file

ROOT = Path(__file__).resolve().parents[1]
_AC_ID = re.compile(r"AC-[1-9][0-9]*\Z")
_DECLARATION = re.compile(
    r"^ {0,3}-\s+\*\*(AC-[1-9][0-9]*) (TODO|DONE)\*\*(?:\s+(.*))?\s*$"
)
_POSSIBLE_DECLARATION = re.compile(r"^ {0,3}[-*+]\s+\*\*AC(?=[-\s0-9*])")
_LIST_ITEM = re.compile(r"^( *)([-*+])\s+")
_HEADING = re.compile(r"^ {0,3}#{1,6}(?:\s|$)")
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_VERIFICATION = re.compile(r"^\s*Verification:\s*(.*)$")


@dataclass(frozen=True)
class Criterion:
    """A declared Work criterion and its declared verification method."""

    status: str
    has_verification: bool


def _is_covers_call(node: ast.Call) -> bool:
    """Return whether a call uses the documented pytest marker spelling."""
    function = node.func
    return (
        isinstance(function, ast.Attribute)
        and function.attr == "covers"
        and isinstance(function.value, ast.Attribute)
        and function.value.attr == "mark"
        and isinstance(function.value.value, ast.Name)
        and function.value.value.id == "pytest"
    )


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
        block.append(line)
    return block


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
        annotations = [
            value.strip()
            for candidate in block
            if (annotation := _VERIFICATION.match(candidate))
            for value in [annotation.group(1)]
        ]
        has_verification = any(annotations)
        if any(not annotation for annotation in annotations):
            errors.append(
                f"{work}:{line_number}: {ac} Verification annotation needs a method"
            )
        if len(annotations) > 1:
            errors.append(
                f"{work}:{line_number}: {ac} has multiple Verification annotations"
            )
        criteria[ac] = Criterion(status, has_verification)

    if not declarations:
        errors.append(
            f"{work}: no AC declarations; expected one or more "
            "'- **AC-N TODO|DONE** description' list items"
        )
    return criteria, errors


def _literal_string(node: ast.expr) -> str | None:
    """Return a string constant value, if the AST node is one."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _test_markers(root: Path, work: str) -> tuple[dict[str, int], list[str]]:
    """Count literal covers markers for one Work across repository tests.

    Returns:
        Marker counts by criterion ID and any source or marker diagnostics.
    """
    counts: dict[str, int] = {}
    errors: list[str] = []
    test_root = root / "test"
    if not test_root.is_dir():
        return counts, errors

    for path in sorted(test_root.rglob("*.py")):
        relative = path.relative_to(root).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        except (OSError, SyntaxError) as exc:
            errors.append(f"{relative}: cannot inspect marker declarations: {exc}")
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not _is_covers_call(node):
                continue
            marker = f"{relative}:{node.lineno}"
            work_args = [item.value for item in node.keywords if item.arg == "work"]
            if (
                len(work_args) != 1
                or (selected_work := _literal_string(work_args[0])) is None
            ):
                errors.append(f"{marker}: covers marker needs one literal work path")
                continue
            if selected_work != work:
                continue

            ac_args = [item.value for item in node.keywords if item.arg == "ac"]
            has_unpacking = any(item.arg is None for item in node.keywords)
            known_names = {"work", "ac"}
            unsupported = (
                node.args
                or has_unpacking
                or any(item.arg not in known_names for item in node.keywords)
                or len(ac_args) != 1
            )
            if unsupported or (ac := _literal_string(ac_args[0])) is None:
                errors.append(
                    f"{marker}: selected covers marker needs literal work "
                    "and ac strings"
                )
                continue
            if not _AC_ID.fullmatch(ac):
                errors.append(f"{marker}: invalid criterion ID {ac!r}")
                continue
            counts[ac] = counts.get(ac, 0) + 1
    return counts, errors


def check_work(root: Path, work: str) -> tuple[list[str], list[str]]:
    """Validate declarations for one selected Work.

    Returns:
        Validation errors and one coverage summary per declared criterion.
    """
    contract = resolve_work_file(root, work)
    criteria, errors = parse_criteria(contract.read_text(encoding="utf-8"), work)
    markers, marker_errors = _test_markers(root.resolve(), work)
    errors.extend(marker_errors)

    for ac in markers.keys() - criteria.keys():
        errors.append(f"{work}: marker refers to undeclared criterion {ac}")

    reports: list[str] = []
    for ac, criterion in criteria.items():
        marker_count = markers.get(ac, 0)
        if (
            criterion.status == "DONE"
            and not marker_count
            and not criterion.has_verification
        ):
            errors.append(
                f"{work}: {ac} is DONE without a matching test marker or "
                "Verification method"
            )
        if marker_count:
            coverage = f"{marker_count} test marker(s)"
        elif criterion.has_verification:
            coverage = "Verification method declared"
        else:
            coverage = "coverage missing"
        reports.append(f"{ac} {criterion.status}: {coverage}")
    return errors, reports


def main() -> int:
    """Check the Work selected by Make without running tests.

    Returns:
        A process status: zero on success, one for coverage errors, or two for
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
