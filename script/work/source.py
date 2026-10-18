# SPDX-License-Identifier: Apache-2.0
"""Discover selected Work contract README files and read their source.

API:
``discover_work_sources`` returns sorted, deduplicated ``WorkSource`` records
pairing resolved paths with UTF-8 Markdown text. Callers may use default Work
tree discovery or select contained contract paths and subtrees with relative
or absolute paths. ``WorkSourceError`` reports invalid selections, unsafe
paths, missing contracts, and read failures.

Implementation:
Discovery resolves selections beneath ``doc/feat``, collects regular contract
README files and reads them in repository-relative order. Recursive traversal
skips linked subdirectories. This module owns source selection and reading;
contract structure is interpreted by ``script.work.contract``.
"""

from collections.abc import Sequence
from dataclasses import dataclass
import os
from pathlib import Path
import stat


@dataclass(frozen=True)
class WorkSource:
    """A discovered contract path and its UTF-8 Markdown source."""

    path: Path
    text: str


class WorkSourceError(ValueError):
    """Raised when contract selections cannot be discovered or read."""


def discover_work_sources(
    repo_root: Path, selections: Sequence[str] = ()
) -> tuple[WorkSource, ...]:
    """Read active Work contracts selected by repository-relative paths.

    With no selections, every ``README.md`` below ``doc/feat`` is included.
    Explicit files must be contract README files under that root; explicit
    directories discover contract README files recursively. Results are
    deduplicated and sorted by repository-relative path.

    Returns:
        Discovered contract paths paired with their UTF-8 source text.

    Raises:
        WorkSourceError: A selection is invalid, escapes the Work root,
            contains no contracts, or cannot be read.
    """
    try:
        return _discover_work_sources(repo_root, selections)
    except OSError as exc:
        raise WorkSourceError(f"Cannot inspect Work contracts: {exc}") from exc


def _discover_work_sources(
    repo_root: Path, selections: Sequence[str]
) -> tuple[WorkSource, ...]:
    """Resolve inputs, discover selections, and read their contract files.

    Returns:
        Discovered contract sources.

    Raises:
        WorkSourceError: A selection is invalid, escapes the Work root,
            or contains no contracts.
    """
    root = repo_root.resolve(strict=True)
    work_root = (root / "doc" / "feat").resolve(strict=True)
    if not work_root.is_relative_to(root) or not stat.S_ISDIR(work_root.stat().st_mode):
        raise WorkSourceError(f"Work root is missing or invalid: {work_root}")
    candidates = _contracts_below(work_root, work_root) if not selections else set()
    for selection in selections:
        selected_contracts = _selection_contracts(root, work_root, selection)
        if not selected_contracts:
            raise WorkSourceError(
                f"Selection contains no Work contract README.md files: {selection}"
            )
        candidates.update(selected_contracts)
    if not candidates:
        raise WorkSourceError(f"No Work contract README.md files found in {work_root}")
    return _read_contracts(root, candidates)


def _selection_contracts(root: Path, work_root: Path, selection: str) -> set[Path]:
    """Resolve and validate one selected contract file or subtree.

    Returns:
        Contract README paths selected by this path.

    Raises:
        WorkSourceError: The selection is outside the Work root or has
            an unsupported shape.
    """
    selected = root / Path(selection)
    lexical = Path(os.path.abspath(selected))
    resolved = selected.resolve(strict=True)
    if not lexical.is_relative_to(root / "doc" / "feat") or not resolved.is_relative_to(
        work_root
    ):
        raise WorkSourceError(f"Selection is outside the Work root: {selection}")
    mode = stat.S_IFMT(resolved.stat().st_mode)
    match mode:
        case stat.S_IFDIR:
            return _contracts_below(work_root, resolved)
        case stat.S_IFREG if lexical.name == "README.md":
            return {resolved}
        case _:
            raise WorkSourceError(f"Select a Work README.md or subtree: {selection}")


def _read_contracts(root: Path, candidates: set[Path]) -> tuple[WorkSource, ...]:
    """Read selected contract files in repository-relative path order.

    Returns:
        Contract sources paired with their UTF-8 Markdown text.

    Raises:
        WorkSourceError: A contract cannot be read as UTF-8 Markdown.
    """
    contracts: list[WorkSource] = []
    for path in sorted(candidates, key=lambda item: item.relative_to(root).as_posix()):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise WorkSourceError(f"Cannot read Work contract {path}: {exc}") from exc
        contracts.append(WorkSource(path, text))
    return tuple(contracts)


def _contracts_below(work_root: Path, directory: Path) -> set[Path]:
    """Find contained regular README files without following linked directories.

    Returns:
        Resolved contract README paths under the Work root.

    Raises:
        WorkSourceError: A discovered README is not a regular file or
            resolves outside the Work root.
    """
    candidates: set[Path] = set()

    def raise_walk_error(error: OSError) -> None:
        raise error

    for current, directories, files in os.walk(
        directory, topdown=True, followlinks=False, onerror=raise_walk_error
    ):
        current_path = Path(current)
        if "README.md" in files:
            path = (current_path / "README.md").resolve(strict=True)
            if not path.is_relative_to(work_root):
                raise WorkSourceError(
                    "Discovered Work contract escapes the Work root: "
                    f"{current_path / 'README.md'}"
                )
            if not stat.S_ISREG(path.stat().st_mode):
                raise WorkSourceError(f"Work contract is not a regular file: {path}")
            candidates.add(path)
        directories.sort()
    return candidates
