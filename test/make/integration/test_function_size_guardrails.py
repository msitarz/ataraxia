# SPDX-License-Identifier: Apache-2.0
"""Exercise advisory and blocking function-size checks through Make."""

from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]


def lint_check_source(source: str):
    """Run Make's lint check on temporary Python source inside the repo."""
    with tempfile.TemporaryDirectory(prefix="size-probe-", dir=ROOT / "test") as temp:
        path = Path(temp) / "size_probe.py"
        path.write_text(source, encoding="utf-8")
        selector = path.relative_to(ROOT).as_posix()
        return subprocess.run(
            ["make", "lint-check", f"ARGS={selector}"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )


def function_source(name: str, statement_count: int) -> str:
    """Return one private function with a known number of statements."""
    return f"def _{name}():\n" + "    pass\n" * statement_count


def test_lint_check_warns_after_25_without_failing():
    source = (
        function_source("within_target", 25)
        + "\n\n"
        + function_source("advisory", 26)
        + "\n\n"
        + function_source("advisory_ceiling", 50)
    )

    result = lint_check_source(source)

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "Too many statements (26 > 25)" in output
    assert "Too many statements (50 > 25)" in output
    assert "Too many statements (25 > 25)" not in output


def test_lint_check_blocks_after_50():
    result = lint_check_source(function_source("blocking", 51))

    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "Too many statements (51 > 50)" in output
