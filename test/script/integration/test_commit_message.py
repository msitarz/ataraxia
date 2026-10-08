# SPDX-License-Identifier: Apache-2.0
"""Exercise the commit-message checker through its command-line boundary."""

from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]


def test_prek_passes_message_filename(tmp_path):
    path = tmp_path / "message"
    for message, expected in [("fix: change", 0), ("fix: change\nNo gap", 1)]:
        path.write_text(message)
        result = subprocess.run(
            [
                "uv",
                "run",
                "--no-sync",
                "prek",
                "run",
                "commit-message-format",
                "--all-files",
                "--hook-stage",
                "commit-msg",
                "--commit-msg-filename",
                str(path),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        assert result.returncode == expected, result.stdout + result.stderr
        assert "commit message format" in result.stdout
