# SPDX-License-Identifier: Apache-2.0
"""Exercise the commit-message checker through its command-line boundary."""

from pathlib import Path
import shlex
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "script" / "check_commit_message.py"
LONG_TOKEN = "https://example.com/" + "a" * 80


@pytest.mark.parametrize(
    "message",
    [
        "",
        "# Abort this commit\n",
        "fix: short subject\n",
        "fix: " + "long subject " * 10,
        "fix: change\n\nA short explanation.\n",
        "fix: change\n\n" + "a " * 35 + "ab\n",
        "fix: change\n\n- A short bullet.\n  Its continuation.\n",
        "fix: change\n\nWhy: Motivation.\n\nWhat: Behavior.\n\nHow: Approach.\n",
        "fix: change\n\n" + LONG_TOKEN,
        "fix: change\n\n  - " + LONG_TOKEN,
        "fix: change\n\n1. " + LONG_TOKEN,
        "fix: change\n\nSigned-off-by: " + "a" * 80,
        "fix!: change\n\nBREAKING CHANGE: " + LONG_TOKEN,
        "fix: change\n\nBody.\n# " + "comment " * 30,
        "fix: change\r\n\r\nBody.\r\n",
        "Merge branch 'topic'\n",
        "fixup! fix: original\n",
        'Revert "fix: original"\n\nThis reverts commit abc123.\n',
    ],
)
def test_accept_formatted_or_absent_body(tmp_path, message):
    path = tmp_path / "message"
    path.write_text(message)
    result = subprocess.run(
        [sys.executable, CHECKER, path], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    assert path.read_bytes() == message.encode()


@pytest.mark.parametrize(
    ("body", "error"),
    [
        ("Body without separator.", "blank line"),
        ("\n" + "a " * 36 + "b", "72 columns"),
        ("\n- " + "word " * 20, "72 columns"),
        ("\n  " + "word " * 20, "72 columns"),
        ("\n\t" + "a " * 32 + "b", "72 columns"),
        ("\nRead this reference: " + LONG_TOKEN, "72 columns"),
        ("\n" + LONG_TOKEN + " trailing prose", "72 columns"),
    ],
)
def test_reject_unformatted_body(tmp_path, body, error):
    path = tmp_path / "message"
    path.write_text("fix: change\n" + body)
    result = subprocess.run(
        [sys.executable, CHECKER, path], capture_output=True, text=True, check=False
    )
    assert result.returncode == 1
    assert error in result.stderr


def test_git_commit_hook_and_configured_comments(tmp_path):
    def git(*args, check=True):
        return subprocess.run(
            ["git", *args], cwd=tmp_path, capture_output=True, text=True, check=check
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
                "--frozen",
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
        )
        assert result.returncode == expected, result.stdout + result.stderr
        assert "commit message format" in result.stdout
