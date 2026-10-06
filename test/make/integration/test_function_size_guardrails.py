# SPDX-License-Identifier: Apache-2.0
"""Exercise advisory and blocking function-size checks through real Make/Ruff."""

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
    ("fixture_name", "diagnostics"),
    [
        ("size_25.py", ()),
        ("size_26.py", ("too-many-statements: Too many statements (26 > 25)",)),
        ("size_50.py", ("too-many-statements: Too many statements (50 > 25)",)),
    ],
    ids=["25-clean", "26-advisory", "50-advisory-ceiling"],
)
@pytest.mark.real_tool
@pytest.mark.covers(
    work="doc/feat/testing-conformance/make/size-guardrails/README.md", ac="AC-1"
)
def test_lint_check_reports_size_advice_without_failing(
    tmp_path: Path,
    fixture_name: str,
    diagnostics: tuple[str, ...],
) -> None:
    """AC-1: Given the four statement-count fixtures, 25 is clean, 26 and 50
    are advisory successes, and 51 blocks lint through real Make/Ruff.

    This case covers the clean/advisory boundaries through unchanged named input.
    """
    # Given: the named fixture contains the independent literal statement count.

    # When
    result = lint_check_fixture(tmp_path, fixture_name)

    # Then
    assert result.exit_code == 0, result.output
    assert "All checks passed!" in result.stdout
    assert "Advisory: review functions with more than 25 statements" in result.stdout
    assert (
        tuple(
            line
            for line in result.output.splitlines()
            if line.startswith("too-many-statements:")
        )
        == diagnostics
    )


@pytest.mark.real_tool
@pytest.mark.covers(
    work="doc/feat/testing-conformance/make/size-guardrails/README.md", ac="AC-1"
)
def test_lint_check_blocks_after_50(tmp_path: Path) -> None:
    """AC-1: Given the four statement-count fixtures, 25 is clean, 26 and 50
    are advisory successes, and 51 blocks lint through real Make/Ruff.

    This case covers the first blocking count and stops before advisory checking.
    """
    # Given: the literal 51-statement fixture is copied outside its root exemption.

    # When
    result = lint_check_fixture(tmp_path, "size_51.py")

    # Then
    assert result.exit_code == 2, result.output
    assert tuple(
        line
        for line in result.output.splitlines()
        if line.startswith("too-many-statements:")
    ) == ("too-many-statements: Too many statements (51 > 50)",)
    assert "Advisory: review functions" not in result.stdout
