# SPDX-License-Identifier: Apache-2.0
"""Verify and extract archived C evidence without changing original records."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
import tarfile
from typing import Any

from script.reviewer_eval.report import inspect_evidence


def extract(
    archive: Path, destination: Path, rows: list[dict[str, Any]], expected_hash: str
) -> None:
    """Verify every archive member before placing it in a new directory.

    Raises:
        ValueError: The archive or member inventory does not match.
    """
    if sha256(archive.read_bytes()).hexdigest() != expected_hash:
        raise ValueError("archive digest mismatch")
    expected = {row["relative_path"]: row for row in rows}
    if len(expected) != len(rows):
        raise ValueError("duplicate inventory path")
    with tarfile.open(archive) as source:
        members = source.getmembers()
        names = [member.name for member in members]
        if len(names) != len(set(names)) or set(names) != set(expected):
            raise ValueError("archive inventory mismatch")
        for member in members:
            path = Path(member.name)
            if (
                not member.isfile()
                or path.is_absolute()
                or ".." in path.parts
                or path.as_posix() != member.name
            ):
                raise ValueError("unsafe archive member")
            stream = source.extractfile(member)
            if stream is None:
                raise ValueError("missing archive member")
            data = stream.read()
            row = expected[member.name]
            if len(data) != row["size"] or sha256(data).hexdigest() != row["sha256"]:
                raise ValueError("member digest mismatch")
            target = destination / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)


def verify_launcher(evidence: Path, rows: list[dict[str, Any]]) -> None:
    """Verify retained launcher records.

    Raises:
        ValueError: A launcher record is unsafe or inconsistent.
    """
    for row in rows:
        path = Path(row["relative_path"])
        if path.name != str(path):
            raise ValueError("unsafe launcher evidence path")
        data = (evidence / path).read_bytes()
        if len(data) != row["size"] or sha256(data).hexdigest() != row["sha256"]:
            raise ValueError("launcher evidence digest mismatch")


def main() -> None:
    """Restore all blocks into a fresh directory and inspect them.

    Raises:
        ValueError: A restored block has invalid evidence.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    args.destination.mkdir(parents=True, exist_ok=False)
    inventory = json.loads((args.evidence / "inventory.json").read_bytes())
    verify_launcher(args.evidence, inventory["launcher_evidence"])
    for name, inventory_file in inventory["blocks"].items():
        if Path(name).name != name or name in {".", ".."}:
            raise ValueError("unsafe block name")
        if inventory_file != "inventory/" + name + ".json":
            raise ValueError("unsafe member inventory path")
        rows = json.loads((args.evidence / inventory_file).read_bytes())
        metadata = inventory["archives"][name]
        if metadata["file"] != name + ".tar.gz":
            raise ValueError("unsafe archive name")
        dest = args.destination / name
        extract(args.evidence / metadata["file"], dest, rows, metadata["sha256"])
        report = inspect_evidence(dest).report
        if report.evidence_state == "invalid" or report.counts is None:
            raise ValueError(f"invalid restored evidence: {name}")
        sys.stdout.write(f"{name} {report.counts.model_dump()}\n")


if __name__ == "__main__":
    main()
