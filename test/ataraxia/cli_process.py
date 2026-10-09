# SPDX-License-Identifier: Apache-2.0
"""Isolated support for running the prepared Ataraxia command."""

from collections.abc import Sequence
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess

PROCESS_TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class CliResult:
    """Captured exit status and text streams from one CLI invocation."""

    exit_code: int
    stdout: str
    stderr: str


def cli_environment(state: Path, project: Path) -> dict[str, str]:
    """Build an offline child environment with isolated home, temp, and caches."""
    path = os.environ.get("PATH")
    if path is None:
        raise RuntimeError("PATH is required to locate the prepared uv command")

    home = state / "home"
    temporary = state / "tmp"
    caches = state / "cache"
    for directory in (home, temporary, caches / "xdg", caches / "uv", caches / "pip"):
        directory.mkdir(parents=True, exist_ok=True)

    return {
        "PATH": path,
        "HOME": str(home),
        "TMPDIR": str(temporary),
        "TMP": str(temporary),
        "TEMP": str(temporary),
        "XDG_CACHE_HOME": str(caches / "xdg"),
        "UV_CACHE_DIR": str(caches / "uv"),
        "PIP_CACHE_DIR": str(caches / "pip"),
        "UV_PROJECT_ENVIRONMENT": str(project / ".venv"),
        "UV_OFFLINE": "true",
        "UV_NO_SYNC": "true",
        "PYTHONUTF8": "1",
    }


def run_cli(
    arguments: Sequence[str | Path],
    *,
    cwd: Path,
    project: Path,
    state: Path,
) -> CliResult:
    """Run the shipped command with explicit project, state, and timeout."""
    command = [
        "uv",
        "run",
        "--project",
        str(project),
        "--no-sync",
        "ataraxia",
        *(str(argument) for argument in arguments),
    ]
    result = subprocess.run(
        command,
        cwd=cwd,
        env=cli_environment(state, project),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=PROCESS_TIMEOUT_SECONDS,
    )
    return CliResult(result.returncode, result.stdout, result.stderr)
