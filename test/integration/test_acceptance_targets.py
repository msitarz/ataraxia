# SPDX-License-Identifier: Apache-2.0
"""Verify Make targets select pytest markers against a temporary Work."""

from contextlib import contextmanager
import os
from pathlib import Path
import subprocess
import tempfile

import pytest

ROOT = Path(__file__).resolve().parents[2]


@contextmanager
def make_fixture(root: Path):
    """Create a temporary contract and marked cases beneath the repository."""
    with tempfile.TemporaryDirectory(prefix="acceptance-fixture-", dir=root) as temp:
        fixture = Path(temp)
        work = (fixture / "README.md").relative_to(root).as_posix()
        (fixture / "README.md").write_text(
            "# Temporary acceptance contract\n", encoding="utf-8"
        )
        cases = fixture / "selection_cases.py"
        cases.write_text(
            "import pytest\n"
            f"@pytest.mark.covers(work={work!r}, ac='AC-1')\n"
            "def test_work_first_criterion():\n    pass\n\n"
            f"@pytest.mark.covers(work={work!r}, ac='AC-2')\n"
            "def test_work_second_criterion():\n    pass\n\n"
            "@pytest.mark.covers(work='other/README.md', ac='AC-1')\n"
            "def test_other_work_is_excluded():\n"
            "    raise AssertionError('a different Work was selected')\n",
            encoding="utf-8",
        )
        yield work, cases.relative_to(root).as_posix()


def run_target(target: str, work: str, cases: str, ac: str = ""):
    """Run one Make target against only the temporary marked cases."""
    env = os.environ.copy()
    env["PYTEST_ADDOPTS"] = cases
    args = ["make", target, f"WORK={work}"]
    if ac:
        args.append(f"AC={ac}")
    return subprocess.run(
        args, cwd=ROOT, env=env, capture_output=True, text=True, timeout=30
    )


@pytest.mark.parametrize(
    ("target", "ac", "selected", "excluded"),
    [
        (
            "ac-collect",
            "",
            ("test_work_first_criterion", "test_work_second_criterion"),
            ("test_other_work_is_excluded",),
        ),
        (
            "ac-collect",
            "AC-1",
            ("test_work_first_criterion",),
            ("test_work_second_criterion", "test_other_work_is_excluded"),
        ),
        (
            "ac-test",
            "",
            ("2 passed",),
            ("a different Work was selected",),
        ),
        (
            "ac-test",
            "AC-1",
            ("1 passed",),
            ("a different Work was selected", "test_work_second_criterion"),
        ),
    ],
)
def test_make_targets_select_work_and_optional_criterion(
    target, ac, selected, excluded
):
    with make_fixture(ROOT) as (work, cases):
        result = run_target(target, work, cases, ac)

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert all(text in output for text in selected), output
    assert all(text not in output for text in excluded), output


@pytest.mark.parametrize("target", ["ac-collect", "ac-test"])
def test_make_targets_fail_when_no_criterion_matches(target):
    with make_fixture(ROOT) as (work, cases):
        result = run_target(target, work, cases, "AC-9")

    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "no tests" in output.lower() or "deselected" in output.lower(), output
