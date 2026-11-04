# SPDX-License-Identifier: Apache-2.0
"""Inspect one saved initial A/B reviewer harness run."""

import argparse
import os
from pathlib import Path
import sys

from script.reviewer_eval.report import Report, inspect_evidence, inspect_run
from script.reviewer_eval.scoring import read_reference, score_inspection


def _write(
    root: Path, output: Path, reference: Path | None = None
) -> tuple[Report, bool]:
    destination = output.absolute().parent.resolve(strict=True) / output.name
    if destination.is_relative_to(root):
        raise ValueError("report must be outside the evidence directory")
    complete = True
    if reference is None:
        report = inspect_run(root)
        data = (report.model_dump_json(indent=2) + "\n").encode()
    else:
        inspection = inspect_evidence(root)
        report = inspection.report
        score = score_inspection(inspection, read_reference(reference))
        complete = all(
            s.diagnostic is None and not s.missing_required_rules
            for s in score.strategies
        )
        data = (score.model_dump_json(indent=2) + "\n").encode()
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
    return report, complete


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
    parser.add_argument(
        "--reference-index",
        type=Path,
        help="private draft reference index for offline scoring",
    )
    args = parser.parse_args()
    try:
        report, scoring_complete = _write(
            args.run_root.resolve(strict=True), args.output, args.reference_index
        )
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"reviewer report: {exc}\n")
        return 1
    return int(
        not scoring_complete
        or report.evidence_state != "complete"
        or any(c.state != "complete" for c in report.calls)
    )


if __name__ == "__main__":
    raise SystemExit(main())
