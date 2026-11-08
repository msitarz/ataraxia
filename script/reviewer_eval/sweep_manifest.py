# SPDX-License-Identifier: Apache-2.0
"""Generate and verify the public frozen C concurrency sweep selection."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path("doc/feat/reviewer/engineering/evaluation")
INPUT = ROOT / "inputs"
MANIFEST = INPUT / "concurrency-sweep-manifest.json"
SOURCE_REVISION = "db569b5203e618f01a878ef02af059f1bd638cd9"
RULES = ("R1", "R3", "R4")
FILES = ("r1/dispatch.py.txt", "r3/planning.py.txt", "r4/ledger.py.txt")
QUOTAS = ((6, 6, 5), (6, 5, 6), (5, 6, 5))


def digest(data: bytes) -> str:
    """Return the SHA-256 digest of bytes."""
    return sha256(data).hexdigest()


def select_group(rows: list[dict[str, object]], quota: int) -> list[dict[str, object]]:
    """Select a group's members by size bins and identity hashes.

    Returns:
        The selected public pair metadata.

    Raises:
        ValueError: The inventory cannot satisfy the quota.
    """
    rows = sorted(rows, key=lambda r: (r["prompt_bytes"], r["function_name"]))
    bins: list[list[dict[str, object]]] = [[], [], []]
    for index, row in enumerate(rows):
        bin_index = 3 * index // len(rows)
        identity = f"{row['rule_id']}\n{row['file_id']}\n{row['function_name']}"
        bins[bin_index].append({
            **row,
            "size_bin": bin_index,
            "selection_hash": digest(identity.encode()),
        })
    for group in bins:
        group.sort(
            key=lambda r: (
                r["selection_hash"],
                r["rule_id"],
                r["file_id"],
                r["function_name"],
            )
        )
    result: list[dict[str, object]] = []
    while len(result) < quota:
        before = len(result)
        for group in bins:
            if group and len(result) < quota:
                result.append(group.pop(0))
        if len(result) == before:
            raise ValueError("insufficient C inventory")
    return result


def generate() -> bytes:
    """Build a public manifest from public C metadata and exact input bytes.

    Returns:
        The deterministic UTF-8 manifest.
    """
    source = INPUT / "c-manifest.json"
    combinations = json.loads(source.read_bytes())["combinations"]
    selected = []
    for ri, rule in enumerate(RULES):
        for fi, file_id in enumerate(FILES):
            group = [
                r
                for r in combinations
                if r["rule_id"] == rule and r["file_id"] == file_id
            ]
            selected.extend(select_group(group, QUOTAS[ri][fi]))
    selected.sort(key=lambda r: (r["rule_id"], r["file_id"], r["function_name"]))
    files = [source, ROOT / "preparation/min.md"]
    for directory in ("c-shared", "c-rules", "c-functions"):
        files.extend(sorted((INPUT / directory).iterdir()))
    data = {
        "algorithm": "c-size-bin-sha256-round-robin-v1",
        "source_revision": SOURCE_REVISION,
        "files": {str(path): digest(path.read_bytes()) for path in files},
        "pairs": selected,
        "blocks": [
            {"repetition": rep + 1, "concurrency": c}
            for rep, order in enumerate((
                (1, 5, 10, 25),
                (5, 10, 25, 1),
                (10, 25, 1, 5),
            ))
            for c in order
        ],
    }
    return (json.dumps(data, indent=2, sort_keys=True) + "\n").encode()


def main() -> None:
    """Write the manifest, or check the frozen bytes without rewriting.

    Raises:
        ValueError: The manifest or its source inputs differ.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = generate()
    if args.check:
        if MANIFEST.read_bytes() != data:
            raise ValueError("frozen manifest or source inputs drifted")
    else:
        MANIFEST.write_bytes(data)


if __name__ == "__main__":
    main()
