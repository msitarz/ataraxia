# SPDX-License-Identifier: Apache-2.0
"""Validate repository-relative Work contract paths used by Make tools."""

from pathlib import Path
import re

_WORK_PATH = re.compile(r"[A-Za-z0-9._/-]+\Z")


def resolve_work_file(root: Path, work: str) -> Path:
    """Validate a Work contract path and return its resolved file path.

    Args:
        root: Repository root.
        work: Repository-relative README.md or spec.md path.

    Returns:
        The resolved Work contract file.

    Raises:
        ValueError: If work is empty, invalid, outside the repository, or absent.
    """
    if not work:
        raise ValueError(
            "WORK is required; provide a repo-relative README.md or spec.md path"
        )
    if not _WORK_PATH.fullmatch(work) or work.startswith("/"):
        raise ValueError("WORK must be a repo-relative README.md or spec.md path")

    path = Path(work)
    if path.as_posix() != work or ".." in path.parts:
        raise ValueError("WORK must be a normalized repo-relative path")
    if path.name not in {"README.md", "spec.md"}:
        raise ValueError("WORK must name an owning README.md or spec.md")

    repository = root.resolve()
    resolved = (repository / path).resolve()
    if not resolved.is_relative_to(repository) or not resolved.is_file():
        raise ValueError(f"WORK does not identify an existing repository file: {work}")
    return resolved
