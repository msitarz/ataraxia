# SPDX-License-Identifier: Apache-2.0
"""Discover and read contract files under the active Work root."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class ContractSource:
    """A discovered contract path and its UTF-8 Markdown source."""

    path: Path
    text: str


class ContractDiscoveryError(ValueError):
    """Raised when contract selections cannot be discovered or read."""


def discover_contracts(
    repo_root: Path, selections: Sequence[str] = ()
) -> tuple[ContractSource, ...]:
    """Read active Work contracts selected by repository-relative paths.

    With no selections, every ``README.md`` below ``doc/feat`` is included.
    Explicit files must be contract README files under that root; explicit
    directories discover contract README files recursively. Results are
    deduplicated and sorted by repository-relative path.

    Returns:
        Discovered contract paths paired with their UTF-8 source text.

    Raises:
        ContractDiscoveryError: A selection is invalid, escapes the Work root,
            contains no contracts, encounters a symlink, or cannot be read.
    """
    root = repo_root.resolve()
    work_root = root / "doc" / "feat"
    _validate_work_root(root, work_root)
    candidates = _contracts_below(work_root) if not selections else set()
    for selection in selections:
        selected_contracts = _selection_contracts(root, work_root, selection)
        if not selected_contracts:
            raise ContractDiscoveryError(
                f"Selection contains no Work contract README.md files: {selection}"
            )
        candidates.update(selected_contracts)
    if not candidates:
        raise ContractDiscoveryError(
            f"No Work contract README.md files found in {work_root}"
        )
    return _read_contracts(root, candidates)


def _validate_work_root(root: Path, work_root: Path) -> None:
    """Ensure the active Work root is a real repository directory.

    Raises:
        ContractDiscoveryError: The Work root is missing, invalid, or outside
            the repository.
    """
    if work_root.is_symlink() or not work_root.is_dir():
        raise ContractDiscoveryError(f"Work root is missing or invalid: {work_root}")
    if not work_root.resolve().is_relative_to(root):
        raise ContractDiscoveryError(f"Work root escapes the repository: {work_root}")


def _selection_contracts(root: Path, work_root: Path, selection: str) -> set[Path]:
    """Resolve and validate one selected contract file or subtree.

    Returns:
        Contract paths contained by the selection.

    Raises:
        ContractDiscoveryError: The selection is invalid or outside the Work
            root.
    """
    selected = Path(selection)
    if not selected.is_absolute():
        selected = root / selected
    if selected.is_symlink():
        raise ContractDiscoveryError(f"Selection is a symlink: {selection}")
    resolved = _resolve_selection(selected, selection)
    if not resolved.is_relative_to(work_root.resolve()):
        raise ContractDiscoveryError(f"Selection is outside the Work root: {selection}")
    if resolved.is_dir():
        return _contracts_below(resolved)
    if resolved.is_file() and resolved.name == "README.md":
        return {resolved}
    if resolved.is_file():
        raise ContractDiscoveryError(
            f"Selection is not a Work contract README.md: {selection}"
        )
    raise ContractDiscoveryError(f"Selection is not a file or directory: {selection}")


def _read_contracts(root: Path, candidates: set[Path]) -> tuple[ContractSource, ...]:
    """Read and sort selected contract files.

    Returns:
        Contract source values in repository-relative path order.

    Raises:
        ContractDiscoveryError: A contract cannot be read as UTF-8 text.
    """
    contracts = []
    for path in sorted(candidates, key=lambda item: item.relative_to(root).as_posix()):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise ContractDiscoveryError(
                f"Cannot read Work contract {path}: {exc}"
            ) from exc
        contracts.append(ContractSource(path, text))
    return tuple(contracts)


def _contracts_below(directory: Path) -> set[Path]:
    """Find contract README files without following symlinks.

    Returns:
        Paths to regular contract README files.

    Raises:
        ContractDiscoveryError: A traversal error or symlink is encountered.
    """
    candidates: set[Path] = set()

    def raise_walk_error(error: OSError) -> None:
        raise ContractDiscoveryError(
            f"Cannot inspect Work selection {error.filename}: {error}"
        ) from error

    for current, directories, files in os.walk(
        directory, topdown=True, followlinks=False, onerror=raise_walk_error
    ):
        current_path = Path(current)
        for name in directories:
            child = current_path / name
            if child.is_symlink():
                raise ContractDiscoveryError(
                    f"Work selection contains a symlink directory: {child}"
                )
        if "README.md" in files:
            path = current_path / "README.md"
            if path.is_symlink():
                raise ContractDiscoveryError(f"Work contract is a symlink: {path}")
            if not path.is_file():
                raise ContractDiscoveryError(
                    f"Work contract is not a regular file: {path}"
                )
            candidates.add(path.resolve())
        directories.sort()
    return candidates


def _resolve_selection(path: Path, original: str) -> Path:
    try:
        return path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ContractDiscoveryError(
            f"Cannot resolve selection {original}: {exc}"
        ) from exc
