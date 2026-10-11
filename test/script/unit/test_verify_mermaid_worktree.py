# SPDX-License-Identifier: Apache-2.0
"""Bound external verification processes without leaving descendants."""

from pathlib import Path
import subprocess

import pytest

from script import verify_mermaid_worktree


class TimedOutProcess:
    """Record waits while simulating an already-expired child process."""

    pid = 13579

    def __init__(self) -> None:
        self.waits = 0

    def wait(self, timeout: float = 0.0) -> int:
        """Require termination and return a reaped signal status afterward."""
        self.waits += 1
        if self.waits <= 2:
            raise subprocess.TimeoutExpired("make", timeout)
        return -9


@pytest.mark.covers(
    work="doc/feat/mermaid-adoption/setup/worktree/README.md", ac="AC-3"
)
def test_timed_out_child_group_is_killed_and_reaped(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A timeout sends TERM then KILL and waits for the command leader."""
    # Given
    child = TimedOutProcess()
    signals: list[int] = []

    def kill_group(process_group: int, signal_number: int) -> None:
        assert process_group == child.pid
        signals.append(signal_number)
        if signal_number == 0:
            raise ProcessLookupError

    def popen(
        arguments: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
        start_new_session: bool,
    ) -> TimedOutProcess:
        assert arguments == ["make", "verify-mermaid-worktree"]
        assert cwd == verify_mermaid_worktree.ROOT
        assert env["UV_OFFLINE"] == "true"
        assert start_new_session
        return child

    monkeypatch.setattr(
        verify_mermaid_worktree.subprocess,
        "Popen",
        popen,
    )
    monkeypatch.setattr(verify_mermaid_worktree.os, "killpg", kill_group)

    # When
    status = verify_mermaid_worktree.run(["make", "verify-mermaid-worktree"])

    # Then
    assert status == 124
    assert signals == [15, 9, 0]
    assert child.waits == 3
    assert "Timed out after 300s" in capsys.readouterr().err
