# SPDX-License-Identifier: Apache-2.0
"""Disposable real-process support for Make acceptance targets."""

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import sys

from test.make.support import ROOT, MakeResult


@dataclass(frozen=True)
class AcceptanceSandbox:
    """Actual Make/scripts in a disposable checkout with prepared real tools."""

    directory: Path
    environment: dict[str, str]

    def run(self, *arguments: str) -> MakeResult:
        """Run real Make with captured diagnostics and a bounded timeout."""
        result = subprocess.run(
            ["make", *arguments],
            cwd=self.directory,
            env=self.environment,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return MakeResult(result.returncode, result.stdout, result.stderr, ())


def acceptance_sandbox(directory: Path) -> AcceptanceSandbox:
    """Copy only acceptance commands/configuration and their direct dependencies."""
    uv = shutil.which("uv")
    if uv is None:
        raise RuntimeError("real uv is required for acceptance Make boundary tests")
    directory.mkdir()
    for name in ("Makefile", "pyproject.toml"):
        shutil.copyfile(ROOT / name, directory / name)
    script = directory / "script"
    script.mkdir()
    for name in ("acceptance_tests.py", "test_roots.py", "work_paths.py"):
        shutil.copyfile(ROOT / "script" / name, script / name)
    home, scratch = directory / "home", directory / "tmp"
    home.mkdir()
    scratch.mkdir()
    return AcceptanceSandbox(
        directory,
        {
            "PATH": os.pathsep.join((
                str(Path(uv).parent),
                str(Path(sys.executable).parent),
                "/usr/bin",
                "/bin",
            )),
            "HOME": str(home),
            "TMPDIR": str(scratch),
            "UV_PROJECT_ENVIRONMENT": str(ROOT / ".venv"),
            "UV_CACHE_DIR": str(ROOT / ".cache/uv"),
            "UV_PYTHON": sys.executable,
            "UV_OFFLINE": "true",
            "UV_NO_SYNC": "true",
        },
    )
