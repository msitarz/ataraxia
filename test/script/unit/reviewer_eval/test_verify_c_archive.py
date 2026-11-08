# SPDX-License-Identifier: Apache-2.0
"""Archive extraction rejects inconsistent or unsafe evidence."""

from hashlib import sha256
from io import BytesIO
from pathlib import Path
import tarfile

import pytest

from script.reviewer_eval.c_models import InventoryRow
from script.reviewer_eval.verify_c_archive import extract


def archive(path: Path, names: tuple[str, ...]) -> tuple[list[InventoryRow], str]:
    """Create synthetic regular members and their inventory.

    Returns:
        Inventory and archive digest.
    """
    rows: list[InventoryRow] = []
    with tarfile.open(path, "w:gz") as output:
        for name in names:
            data = b"synthetic"
            info = tarfile.TarInfo(name)
            info.size = len(data)
            output.addfile(info, BytesIO(data))
            rows.append(
                InventoryRow(
                    relative_path=name, size=len(data), sha256=sha256(data).hexdigest()
                )
            )
    return rows, sha256(path.read_bytes()).hexdigest()


def test_round_trip_checks_member_bytes(tmp_path: Path) -> None:
    # Given one archived synthetic record.
    source = tmp_path / "block.tar.gz"
    rows, digest = archive(source, ("attempts/one",))

    # When verifying and extracting it.
    extract(source, tmp_path / "restored", rows, digest)

    # Then its exact bytes are available at the relative path.
    assert (tmp_path / "restored/attempts/one").read_bytes() == b"synthetic"


def test_duplicate_archive_member_is_rejected(tmp_path: Path) -> None:
    # Given an archive with duplicate names.
    source = tmp_path / "block.tar.gz"
    rows, digest = archive(source, ("same", "same"))

    # When extracting it, then duplicate inventory is rejected.
    with pytest.raises(ValueError, match="duplicate"):
        extract(source, tmp_path / "restored", rows, digest)


def test_path_escape_is_rejected(tmp_path: Path) -> None:
    # Given a matching but escaping archive path.
    source = tmp_path / "block.tar.gz"
    rows, digest = archive(source, ("../escape",))

    # When extracting it, then the unsafe member is rejected.
    with pytest.raises(ValueError, match="unsafe"):
        extract(source, tmp_path / "restored", rows, digest)
    assert not (tmp_path / "escape").exists()
