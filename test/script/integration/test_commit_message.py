# SPDX-License-Identifier: Apache-2.0
"""Exercise the commit-message checker through its command-line boundary."""

from pathlib import Path
import shlex
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
CHECKER = ROOT / "script" / "check_commit_message.py"


@pytest.mark.parametrize("comment_prefix", ["#", ";", "//"])
@pytest.mark.parametrize("body, expected", [("Body.", 0), ("word " * 20, 1)])
def test_verbose_diff_below_scissors(tmp_path, comment_prefix, body, expected):
    subprocess.run(
        ["git", "init", str(tmp_path)], capture_output=True, check=True, timeout=30
    )
    subprocess.run(
        ["git", "config", "core.commentString", comment_prefix],
        cwd=tmp_path,
        check=True,
        timeout=30,
    )
    message = (
        f"fix: change\n\n{body}\n\n"
        f"{comment_prefix} Changes to be committed:\n"
        f"{comment_prefix} ------------------------ >8 ------------------------\n"
        f"{comment_prefix} Everything below it will be ignored.\n"
        "diff --git a/example.txt b/example.txt\n"
        "--- a/example.txt\n+++ b/example.txt\n@@ -1 +1 @@\n"
        "+" + "long diff content " * 20 + "\n"
    )
    path = tmp_path / "message"
    path.write_text(message)
    result = subprocess.run(
        [sys.executable, CHECKER, path],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == expected, result.stderr
    assert "long diff content" not in result.stderr
    assert path.read_text() == message


def test_git_commit_hook_and_configured_comments(tmp_path):
    def git(*args, check=True):
        return subprocess.run(
            ["git", *args],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=check,
            timeout=30,
        )

    git("init")
    git("config", "user.name", "Hook Test")
    git("config", "user.email", "hook@example.com")
    git("config", "commit.gpgsign", "false")
    git("config", "core.commentChar", ";")
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    git("config", "core.hooksPath", str(hooks))
    hook = hooks / "commit-msg"
    hook.write_text(
        f"#!/bin/sh\nexec {shlex.quote(sys.executable)} "
        f'{shlex.quote(str(CHECKER))} "$1"\n'
    )
    hook.chmod(0o755)
    rejected = git("commit", "--allow-empty", "-m", "fix: change\nNo gap", check=False)
    assert rejected.returncode != 0
    assert "blank line" in rejected.stderr
    assert git("rev-parse", "--verify", "HEAD", check=False).returncode != 0
    accepted = git(
        "commit",
        "--allow-empty",
        "--cleanup=strip",
        "-m",
        "fix: change\n\nBody.\n; " + "comment " * 30,
    )
    assert accepted.returncode == 0
    assert git("log", "-1", "--format=%B").stdout.strip() == "fix: change\n\nBody."


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
