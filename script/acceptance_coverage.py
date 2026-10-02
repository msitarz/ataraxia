# SPDX-License-Identifier: Apache-2.0
"""Validate Work acceptance declarations without executing tests."""

from __future__ import annotations

import ast
from dataclasses import dataclass
import os
from pathlib import Path
import re
import sys

from test_roots import existing_test_roots
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
        if block and line.strip() and not item:
            leading = len(line) - len(line.lstrip(" "))
            if leading < indent + 2:
                break
        block.append(line)
    return block


def _verification_for_criterion(
    block: list[str], work: str, line_number: int, ac: str
) -> tuple[bool, list[str]]:
    """Validate the optional non-test verification annotation for one criterion.

    Returns:
        Whether a non-empty verification method is declared and any errors.
    """
    annotations = [
        annotation.group(1).strip()
        for candidate in block
        if (annotation := _VERIFICATION.match(candidate))
    ]
    errors: list[str] = []
    if any(not annotation for annotation in annotations):
        errors.append(
            f"{work}:{line_number}: {ac} Verification annotation needs a method"
        )
    if len(annotations) > 1:
        errors.append(
            f"{work}:{line_number}: {ac} has multiple Verification annotations"
        )
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
        has_verification, annotation_errors = _verification_for_criterion(
            block, work, line_number, ac
        )
        errors.extend(annotation_errors)
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


def _test_functions(tree: ast.Module) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    """Return only statically recognizable pytest test functions."""
    functions: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_"):
                functions.append(node)
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            functions.extend(
                child
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                and child.name.startswith("test_")
            )
    return functions


def _test_candidate_files(test_root: Path) -> list[Path]:
    """Return repository test files that may contain collected test functions."""
    return sorted(
        path
        for path in test_root.rglob("*.py")
        if path.name.startswith("test_") or path.name.endswith("_test.py")
    )


def _read_test_module(path: Path, root: Path) -> tuple[ast.Module | None, str | None]:
    """Read and parse one test source.

    Returns:
        The parsed module and no error, or no module and a contextual error.
    """
    relative = path.relative_to(root).as_posix()
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=relative), None
    except (OSError, SyntaxError) as exc:
        return None, f"{relative}: cannot inspect marker declarations: {exc}"


def _selected_marker_criterion(
    decorator: ast.Call, relative: str, work: str
) -> tuple[str | None, str | None]:
    """Validate one marker and return its criterion when it selects this Work.

    Returns:
        The selected criterion and no error, or no criterion and an error.
    """
    marker = f"{relative}:{decorator.lineno}"
    work_args = [item.value for item in decorator.keywords if item.arg == "work"]
    if len(work_args) != 1 or (selected_work := _literal_string(work_args[0])) is None:
        return None, f"{marker}: covers marker needs one literal work path"
    if selected_work != work:
        return None, None

    ac_args = [item.value for item in decorator.keywords if item.arg == "ac"]
    has_unpacking = any(item.arg is None for item in decorator.keywords)
    known_names = {"work", "ac"}
    unsupported = (
        decorator.args
        or has_unpacking
        or any(item.arg not in known_names for item in decorator.keywords)
        or len(ac_args) != 1
    )
    if unsupported or (ac := _literal_string(ac_args[0])) is None:
        return (
            None,
            f"{marker}: selected covers marker needs literal work and ac strings",
        )
    if not _AC_ID.fullmatch(ac):
        return None, f"{marker}: invalid criterion ID {ac!r}"
    return ac, None


def _test_markers(root: Path, work: str) -> tuple[dict[str, int], list[str]]:
    """Count literal covers markers for one Work across repository tests.

    Returns:
        Marker counts by criterion ID and any source or marker diagnostics.
    """
    counts: dict[str, int] = {}
    errors: list[str] = []
    for name in existing_test_roots(root):
        for path in _test_candidate_files(root / name):
            relative = path.relative_to(root).as_posix()
            tree, read_error = _read_test_module(path, root)
            if read_error:
                errors.append(read_error)
                continue
            assert tree is not None

            for function in _test_functions(tree):
                for decorator in function.decorator_list:
                    if not isinstance(decorator, ast.Call) or not _is_covers_call(
                        decorator
                    ):
                        continue
                    ac, marker_error = _selected_marker_criterion(
                        decorator, relative, work
                    )
                    if marker_error:
                        errors.append(marker_error)
                    if ac is None:
                        continue
                    counts[ac] = counts.get(ac, 0) + 1
    return counts, errors


def _criterion_report(ac: str, criterion: Criterion, marker_count: int) -> str:
    """Describe declarations for one criterion without judging its outcome.

    Returns:
        A neutral summary of the criterion's declared markers or method.
    """
    if marker_count:
        declaration = f"{marker_count} test marker(s) declared"
    elif criterion.has_verification:
        declaration = "Verification method declared"
    else:
        declaration = "no test marker or Verification method declared"
    return f"{ac} {criterion.status}: {declaration}"


def check_work(root: Path, work: str) -> tuple[list[str], list[str]]:
    """Validate declarations for one selected Work.

    Returns:
        Validation errors and one declaration summary per criterion.
    """
    contract = resolve_work_file(root, work)
    criteria, errors = parse_criteria(contract.read_text(encoding="utf-8"), work)
    markers, marker_errors = _test_markers(root.resolve(), work)
    errors.extend(marker_errors)

    for ac in markers.keys() - criteria.keys():
        errors.append(f"{work}: marker refers to undeclared criterion {ac}")

    reports = [
        _criterion_report(ac, criterion, markers.get(ac, 0))
        for ac, criterion in criteria.items()
    ]
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
