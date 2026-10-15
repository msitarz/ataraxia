# SPDX-License-Identifier: Apache-2.0
"""Exercise the stdin Mermaid validator through its public process boundary."""

from pathlib import Path
import subprocess
import sys

import pytest

from test.script.commit_message_support import isolated_environment

ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = ROOT / "script" / "validate_mermaid.py"


@pytest.mark.parametrize(
    ("source", "expected_exit", "expected_stderr"),
    [
        pytest.param(
            "flowchart LR\n    A[Start] --> B[Finish]\n",
            0,
            "",
            id="valid-source",
        ),
        pytest.param(
            "this is not mermaid\n",
            1,
            "UnknownDiagramError",
            id="malformed-source",
        ),
    ],
)
def test_validator_renders_stdin_without_creating_files(
    tmp_path: Path, source: str, expected_exit: int, expected_stderr: str
) -> None:
    """Force real QuickJS rendering and leave stdout and the cwd empty of SVG."""
    # Given
    process_cwd = tmp_path / "cwd"
    process_cwd.mkdir()
    sentinel = process_cwd / "sentinel.txt"
    sentinel.write_text("unchanged", encoding="utf-8")
    env = isolated_environment(tmp_path)

    # When
    result = subprocess.run(
        (sys.executable, VALIDATOR),
        cwd=process_cwd,
        env=env,
        input=source,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=30,
    )

    # Then
    assert result.returncode == expected_exit, result.stderr
    assert result.stdout == ""
    assert expected_stderr in result.stderr
    assert sorted(path.name for path in process_cwd.iterdir()) == ["sentinel.txt"]
    assert sentinel.read_text(encoding="utf-8") == "unchanged"
