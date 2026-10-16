# SPDX-License-Identifier: Apache-2.0
"""Exercise the real Work checker module and its process contract."""

import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
FIXTURES = ROOT / "test/script/fixtures/work_check"


def test_module_reports_complete_sorted_diagnostics_without_writing(
    tmp_path: Path,
) -> None:
    # Given
    earlier = tmp_path / "doc/feat/a/README.md"
    later = tmp_path / "doc/feat/z/README.md"
    earlier.parent.mkdir(parents=True)
    later.parent.mkdir(parents=True)
    shutil.copyfile(FIXTURES / "broken_sections.txt", earlier)
    shutil.copyfile(FIXTURES / "broken_boundaries.txt", later)
    before = {path: path.read_bytes() for path in (earlier, later)}

    # When
    result = _run(tmp_path)

    # Then
    assert result.returncode == 1
    assert result.stdout.splitlines() == [
        (
            "doc/feat/a/README.md:1: required top-level section "
            "'Acceptance criteria': file start"
        ),
        ("doc/feat/a/README.md:1: required top-level section 'Goals': file start"),
        ("doc/feat/a/README.md:1: required top-level section 'Purpose': file start"),
        (
            "doc/feat/z/README.md:9: nonempty 'Acceptance criteria' section: "
            "Acceptance criteria"
        ),
        (
            "doc/feat/z/README.md:10: nonempty criterion outcome body: "
            "**AC-1 TODO** Result"
        ),
        (
            "doc/feat/z/README.md:14: criterion must be inside Acceptance criteria: "
            "**AC-9 TODO** Outside"
        ),
        (
            "doc/feat/z/README.md:17: criterion declaration must use a "
            "level-three heading: **AC-10 TODO** Wrong level"
        ),
        (
            "doc/feat/z/README.md:17: criterion must be inside Acceptance criteria: "
            "**AC-10 TODO** Wrong level"
        ),
    ]
    assert result.stderr == ""
    assert {path: path.read_bytes() for path in before} == before


def test_module_accepts_real_markdown_fixture_with_nested_syntax(
    tmp_path: Path,
) -> None:
    # Given
    contract = tmp_path / "doc/feat/valid/README.md"
    contract.parent.mkdir(parents=True)
    shutil.copyfile(FIXTURES / "valid.txt", contract)
    before = contract.read_bytes()

    # When
    result = _run(tmp_path, "doc/feat/valid/README.md")

    # Then
    assert result.returncode == 0
    assert result.stdout == result.stderr == ""
    assert contract.read_bytes() == before


def test_module_reports_missing_selection_as_input_failure(tmp_path: Path) -> None:
    # Given
    (tmp_path / "doc/feat").mkdir(parents=True)

    # When
    result = _run(tmp_path, "doc/feat/missing")

    # Then
    assert result.returncode == 2
    assert "doc/feat/missing" in result.stderr
    assert result.stdout == ""


def test_module_reports_malformed_invocation_with_status_two(tmp_path: Path) -> None:
    # Given
    (tmp_path / "doc/feat").mkdir(parents=True)

    # When
    result = _run(tmp_path, "--unexpected")

    # Then
    assert result.returncode == 2
    assert "unrecognized arguments: --unexpected" in result.stderr
    assert result.stdout == ""


def _run(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    """Run the shipped module against an isolated repository root."""
    environment = os.environ | {"PYTHONPATH": str(ROOT)}
    return subprocess.run(
        [sys.executable, "-m", "script.work_check", *arguments],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
