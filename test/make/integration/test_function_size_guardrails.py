# SPDX-License-Identifier: Apache-2.0
"""Exercise the blocking function-size boundary through real Make/Ruff."""

import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from test.make.support import ROOT, MakeResult


def lint_check_fixture(tmp_path: Path, name: str) -> MakeResult:
    """Copy named input unchanged outside fixture exemptions and run actual Make."""
    uv = shutil.which("uv")
    if uv is None:
        raise RuntimeError("real uv is required for Make/Ruff size boundary tests")
    directory = tmp_path / "repo"
    directory.mkdir()
    for config in ("Makefile", "pyproject.toml"):
        shutil.copyfile(ROOT / config, directory / config)
    selected = directory / "test/size_probe.py"
    selected.parent.mkdir()
    shutil.copyfile(ROOT / "test/make/fixtures" / name, selected)
    before = selected.read_bytes()
    home, scratch = tmp_path / "home", tmp_path / "tmp"
    home.mkdir()
    scratch.mkdir()
    environment = {
        "PATH": os.pathsep.join((str(Path(uv).parent), "/usr/bin", "/bin")),
        "HOME": str(home),
        "TMPDIR": str(scratch),
        "UV_PROJECT_ENVIRONMENT": str(ROOT / ".venv"),
        "UV_CACHE_DIR": str(ROOT / ".cache/uv"),
        "UV_PYTHON": sys.executable,
        "UV_OFFLINE": "true",
        "UV_NO_SYNC": "true",
    }
    result = subprocess.run(
        ["make", "lint-check", "ARGS=test/size_probe.py"],
        cwd=directory,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert selected.read_bytes() == before
    return MakeResult(result.returncode, result.stdout, result.stderr, ())


@pytest.mark.parametrize(
    ("fixture_name", "exit_code", "diagnostics"),
    [
        ("size_25.py", 0, ()),
        ("size_26.py", 2, ("too-many-statements: Too many statements (26 > 25)",)),
    ],
    ids=["25-passes", "26-blocks"],
)
@pytest.mark.real_tool
def test_lint_check_enforces_the_25_statement_limit(
    tmp_path: Path,
    fixture_name: str,
    exit_code: int,
    diagnostics: tuple[str, ...],
) -> None:
    """The real Make lint path accepts 25 statements and blocks at 26."""
    # Given: the named fixture contains an independent literal statement count.

    # When
    result = lint_check_fixture(tmp_path, fixture_name)

    # Then
    assert result.exit_code == exit_code, result.output
    assert (
        tuple(
            line
            for line in result.output.splitlines()
            if line.startswith("too-many-statements:")
        )
        == diagnostics
    )
