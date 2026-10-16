# SPDX-License-Identifier: Apache-2.0
"""Discover and read contract files under the active Work root."""

from collections.abc import Sequence
from dataclasses import dataclass
import os
from pathlib import Path
import stat


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
            contains no contracts, or cannot be read.
    """
    try:
        return _discover_contracts(repo_root, selections)
    except OSError as exc:
        raise ContractDiscoveryError(f"Cannot inspect Work contracts: {exc}") from exc


def _discover_contracts(
    repo_root: Path, selections: Sequence[str]
) -> tuple[ContractSource, ...]:
    """Resolve inputs, discover selections, and read their contract files.

    Returns:
        Discovered contract sources.

    Raises:
        ContractDiscoveryError: A selection is invalid, escapes the Work root,
            or contains no contracts.
    """
    root = repo_root.resolve(strict=True)
    work_root = (root / "doc" / "feat").resolve(strict=True)
    if not work_root.is_relative_to(root) or not stat.S_ISDIR(work_root.stat().st_mode):
        raise ContractDiscoveryError(f"Work root is missing or invalid: {work_root}")
    candidates = _contracts_below(work_root, work_root) if not selections else set()
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


def _selection_contracts(root: Path, work_root: Path, selection: str) -> set[Path]:
    """Resolve and validate one selected contract file or subtree.

    Returns:
        Contract README paths selected by this path.

    Raises:
        ContractDiscoveryError: The selection is outside the Work root or has
            an unsupported shape.
    """
    selected = root / Path(selection)
    lexical = Path(os.path.abspath(selected))
    resolved = selected.resolve(strict=True)
    if not lexical.is_relative_to(root / "doc" / "feat") or not resolved.is_relative_to(
        work_root
    ):
        raise ContractDiscoveryError(f"Selection is outside the Work root: {selection}")
    mode = stat.S_IFMT(resolved.stat().st_mode)
    match mode:
        case stat.S_IFDIR:
            return _contracts_below(work_root, resolved)
        case stat.S_IFREG if lexical.name == "README.md":
            return {resolved}
        case _:
            raise ContractDiscoveryError(
                f"Select a Work README.md or subtree: {selection}"
            )


def _read_contracts(root: Path, candidates: set[Path]) -> tuple[ContractSource, ...]:
    """Read selected contract files in repository-relative path order.

    Returns:
        Contract sources paired with their UTF-8 Markdown text.

    Raises:
        ContractDiscoveryError: A contract cannot be read as UTF-8 Markdown.
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


def _contracts_below(work_root: Path, directory: Path) -> set[Path]:
    """Find contained regular README files without following linked directories.

    Returns:
        Resolved contract README paths under the Work root.

    Raises:
        ContractDiscoveryError: A discovered README is not a regular file or
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
                raise ContractDiscoveryError(
                    "Discovered Work contract escapes the Work root: "
                    f"{current_path / 'README.md'}"
                )
            if not stat.S_ISREG(path.stat().st_mode):
                raise ContractDiscoveryError(
                    f"Work contract is not a regular file: {path}"
                )
            candidates.add(path)
        directories.sort()
    return candidates
