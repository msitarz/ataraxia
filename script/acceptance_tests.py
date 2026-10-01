# SPDX-License-Identifier: Apache-2.0
"""Run pytest tests selected by Work acceptance-criterion markers."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
_WORK_PATH = re.compile(r"[A-Za-z0-9._/-]+\Z")
_AC_ID = re.compile(r"AC-[1-9][0-9]*\Z")


def build_command(action: str, work: str, ac: str = "") -> list[str]:
    """Validate selection inputs and build the pytest command.

    Returns:
        The pytest command as an argument list.

    Raises:
        ValueError: If the action, Work path, or criterion ID is invalid.
    """
    if action not in {"collect", "test"}:
        raise ValueError("action must be 'collect' or 'test'")
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
    resolved = (ROOT / path).resolve()
    if not resolved.is_relative_to(ROOT) or not resolved.is_file():
        raise ValueError(f"WORK does not identify an existing repository file: {work}")

    if ac and not _AC_ID.fullmatch(ac):
        raise ValueError("AC must be a criterion ID such as AC-8")

    marker = f"covers(work='{work}'"
    if ac:
        marker += f", ac='{ac}'"
    marker += ")"
    command = [sys.executable, "-m", "pytest", "-q"]
    if action == "collect":
        command.append("--collect-only")
    command.extend(["-m", marker])
    return command


def main() -> int:
    """Validate Make inputs and run the corresponding pytest selection.

    Returns:
        The pytest exit status, or 2 for invalid invocation arguments.
    """
    if len(sys.argv) != 2:
        sys.stderr.write("usage: acceptance_tests.py {collect|test}\n")
        return 2
    action = sys.argv[1]
    try:
        command = build_command(
            action, os.environ.get("WORK", ""), os.environ.get("AC", "")
        )
    except ValueError as error:
        sys.stderr.write(f"{error}\n")
        return 2
    if action != "collect":
        return subprocess.run(command, cwd=ROOT, check=False).returncode

    result = subprocess.run(
        command, cwd=ROOT, check=False, capture_output=True, text=True
    )
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    if result.returncode == 0 and re.search(
        r"^no tests collected\b", result.stdout, flags=re.MULTILINE
    ):
        return 5
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
