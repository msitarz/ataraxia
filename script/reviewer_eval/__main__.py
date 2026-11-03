# SPDX-License-Identifier: Apache-2.0
"""Inspect one saved initial A/B reviewer harness run."""

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any

from script.reviewer_eval.report import inspect_run


def _write(root: Path, output: Path) -> dict[str, Any]:
    destination = output.absolute().parent.resolve(strict=True) / output.name
    if destination.is_relative_to(root):
        raise ValueError("report must be outside the evidence directory")
    report = inspect_run(root)
    data = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode()
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
    return report


def main() -> int:
    """Write an exclusive JSON report.

    Returns:
        Zero for complete evidence, one for incomplete or failed inspection.
    """
    parser = argparse.ArgumentParser(
        description="Validate saved initial A/B reviewer run evidence."
    )
    parser.add_argument("run_root", type=Path, help="original harness run directory")
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="fresh report file outside the run directory",
    )
    args = parser.parse_args()
    try:
        report = _write(args.run_root.resolve(strict=True), args.output)
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"reviewer report: {exc}\n")
        return 1
    return int(
        report["evidence_state"] != "complete"
        or any(c["state"] != "complete" for c in report["calls"])
    )


if __name__ == "__main__":
    raise SystemExit(main())
