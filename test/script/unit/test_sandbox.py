# SPDX-License-Identifier: Apache-2.0
"""Check managed-root ownership records through the public sandbox boundary."""

import json
from pathlib import Path

import pytest

from script.sandbox import METADATA, check_root_owner


def test_root_owner_accepts_matching_top_level_and_nested_records(
    tmp_path: Path,
) -> None:
    # Given
    root = tmp_path / "managed"
    root.mkdir()
    (root / METADATA).write_text(json.dumps({"common_dir": "/repo/.git"}))
    child = root / "sandbox"
    child.mkdir()
    (child / METADATA).write_text(json.dumps({"common_dir": "/repo/.git"}))

    # When / Then
    check_root_owner(root, "/repo/.git")


def test_root_owner_rejects_a_foreign_checkout_record(tmp_path: Path) -> None:
    # Given
    root = tmp_path / "managed"
    root.mkdir()
    child = root / "sandbox"
    child.mkdir()
    (child / METADATA).write_text(json.dumps({"common_dir": "/other/.git"}))

    # When / Then
    with pytest.raises(ValueError, match="another checkout"):
        check_root_owner(root, "/repo/.git")


@pytest.mark.parametrize("nested", [False, True], ids=["top-level", "nested"])
def test_root_owner_refuses_metadata_symlinks(tmp_path: Path, nested: bool) -> None:
    # Given
    root = tmp_path / "managed"
    root.mkdir()
    metadata = root / METADATA
    if nested:
        child = root / "sandbox"
        child.mkdir()
        metadata = child / METADATA
    target = tmp_path / "owner.json"
    target.write_text(json.dumps({"common_dir": "/repo/.git"}))
    metadata.symlink_to(target)

    # When / Then
    with pytest.raises(ValueError, match="metadata is a symlink"):
        check_root_owner(root, "/repo/.git")


def test_root_owner_ignores_unmanaged_entries_including_symlinks(
    tmp_path: Path,
) -> None:
    # Given
    root = tmp_path / "managed"
    root.mkdir()
    (root / "notes.txt").write_text("user data")
    (root / "unmanaged-child").mkdir()
    (root / "unmanaged-link").symlink_to(tmp_path / "missing")

    # When / Then
    check_root_owner(root, "/repo/.git")
