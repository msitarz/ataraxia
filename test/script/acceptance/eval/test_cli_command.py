# SPDX-License-Identifier: Apache-2.0
"""Controlled standalone command checks without provider calls."""

import json
import os
from pathlib import Path
import select
import shutil
import signal
import subprocess
import sys

import pytest

from test.script.integration.eval.support import git_test_environment, make_repository

ROOT = Path(__file__).resolve().parents[4]
FIXTURE = ROOT / "test/script/fixtures/eval/fake_codex.py"


def command(repository: Path, output: Path) -> list[str]:
    return [
        sys.executable,
        "-m",
        "script.eval",
        "-d",
        str(repository / "context"),
        "-m",
        "model",
        "-e",
        "low",
        "-o",
        str(output),
    ]


def environment(tmp_path: Path) -> dict[str, str]:
    binary = tmp_path / "bin"
    binary.mkdir()
    executable = binary / "codex"
    shutil.copyfile(FIXTURE, executable)
    executable.chmod(0o755)
    env = git_test_environment()
    env["PATH"] = str(binary) + os.pathsep + env["PATH"]
    env["PYTHONPATH"] = str(ROOT)
    return env


@pytest.mark.parametrize(
    ("fake_exit", "expected", "expected_state"),
    [("0", 0, "complete"), ("7", 1, "failed")],
    ids=["success", "failed-attempt"],
)
def test_command_records_fake_attempt_and_maps_outcome(
    tmp_path: Path, fake_exit: str, expected: int, expected_state: str
) -> None:
    # Given
    repo = make_repository(tmp_path / "repo")
    output = tmp_path / "evidence"
    env = environment(tmp_path)
    env["FAKE_EXIT"] = fake_exit

    # When
    result = subprocess.run(
        command(repo, output),
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    # Then
    assert result.returncode == expected, result.stderr
    assert "scheduled calls: 1" in result.stdout
    record = json.loads((output / "run.json").read_text())
    assert record["calls"][0]["state"] == expected_state


def test_quota_wait_fails_before_provider_binding(tmp_path: Path) -> None:
    # Given
    repo = make_repository(tmp_path / "repo")
    output = tmp_path / "evidence"
    env = environment(tmp_path)
    marker = tmp_path / "provider-invocations"
    env["FAKE_ARGV_LOG"] = str(marker)

    # When
    result = subprocess.run(
        [*command(repo, output), "--wait-for-quota"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    # Then
    assert result.returncode == 1
    assert "scope is not verified" in result.stderr
    assert not output.exists()
    assert not marker.exists()


@pytest.mark.parametrize(
    "sent_signal", [signal.SIGINT, signal.SIGTERM], ids=["sigint", "sigterm"]
)
def test_signal_cancels_active_attempt_and_settles_evidence(
    tmp_path: Path, sent_signal: signal.Signals
) -> None:
    # Given
    repo = make_repository(tmp_path / "repo")
    output = tmp_path / "evidence"
    env = environment(tmp_path)

    # When
    code, stdout, stderr = run_signalled(repo, output, env, tmp_path, sent_signal)

    # Then
    assert code == 130, stderr.decode()
    assert b"scheduled calls: 1" in stdout
    record = json.loads((output / "run.json").read_text())
    assert record["state"] == "incomplete"
    assert record["calls"][0]["state"] == "failed"
    attempt = record["calls"][0]["attempts"][0]
    assert attempt["outcome_kind"] == "cancelled"
    assert attempt["cleanup"]["direct_wait"] == "reaped"


def test_dry_run_requires_no_provider_or_output(tmp_path: Path) -> None:
    # Given
    repo = make_repository(tmp_path / "repo")
    output = tmp_path / "evidence"
    env = git_test_environment()
    env["PYTHONPATH"] = str(ROOT)
    env["PATH"] = "/usr/bin:/bin"
    arguments = [
        sys.executable,
        "-m",
        "script.eval",
        "-d",
        str(repo / "context"),
        "-m",
        "unsupported-model",
        "-e",
        "low",
        "-n",
    ]

    # When
    result = subprocess.run(
        arguments, cwd=ROOT, env=env, capture_output=True, text=True, timeout=20
    )

    # Then
    assert result.returncode == 0, result.stderr
    assert "scheduled calls: 1" in result.stdout
    assert "compatibility=unknown" in result.stdout
    assert not output.exists()


def run_signalled(
    repo: Path,
    output: Path,
    env: dict[str, str],
    directory: Path,
    sent_signal: signal.Signals,
) -> tuple[int | None, bytes, bytes]:
    """Wait for the fake child to start, then signal the command and join it."""
    fifo = directory / "ready"
    os.mkfifo(fifo)
    fd = os.open(fifo, os.O_RDONLY | os.O_NONBLOCK)
    env["FAKE_READY_FIFO"] = str(fifo)
    process = subprocess.Popen(
        command(repo, output),
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        empty: list[int] = []
        ready, _, _ = select.select([fd], empty, empty, 15)
        assert ready and os.read(fd, 100) == b"ready\n"
        process.send_signal(sent_signal)
        stdout, stderr = process.communicate(timeout=15)
        return process.returncode, stdout, stderr
    finally:
        os.close(fd)
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)


def test_make_entry_exposes_standalone_help(tmp_path: Path) -> None:
    # Given
    env = environment(tmp_path)

    # When
    result = subprocess.run(
        ["make", "eval", "CLI_ARGS=--help"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    # Then
    assert result.returncode == 0, result.stderr
    assert "model_instructions_file=PATH" in result.stdout
    assert "130 cancellation" in result.stdout


def test_recording_obstruction_reports_incomplete_evidence(tmp_path: Path) -> None:
    # Given
    repo = make_repository(tmp_path / "repo")
    output = tmp_path / "evidence"
    env = environment(tmp_path)
    env["FAKE_OBSTRUCT_PATH"] = str(output / "attempts")

    # When
    result = subprocess.run(
        command(repo, output),
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    # Then
    assert result.returncode == 3, result.stderr
    record = json.loads((output / "run.json").read_text())
    assert record["state"] == "incomplete"
    assert record["calls"][0]["state"] == "failed"
    assert record["calls"][0]["attempts"] == []
    assert (output / "attempts").read_text() == "block attempt artifacts"


def test_quiet_preserves_execution_and_evidence(tmp_path: Path) -> None:
    # Given
    repo = make_repository(tmp_path / "repo")
    output = tmp_path / "evidence"
    env = environment(tmp_path)
    marker = tmp_path / "provider-invocations"
    env["FAKE_ARGV_LOG"] = str(marker)

    # When
    result = subprocess.run(
        [*command(repo, output), "--quiet"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    # Then
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert "--version" in marker.read_text()
    assert "exec " in marker.read_text()
    record = json.loads((output / "run.json").read_text())
    assert record["calls"][0]["state"] == "complete"
    assert record["calls"][0]["attempts"][0]["exit_status"] == 0


@pytest.mark.parametrize("tty", [False, True], ids=["redirected", "tty"])
def test_command_reports_live_progress_to_stderr(tmp_path: Path, tty: bool) -> None:
    # Given
    repo = make_repository(tmp_path / "repo")
    output = tmp_path / "evidence"
    env = environment(tmp_path)
    read_fd, target = progress_destination(tty)

    # When
    code, stdout, progress = signal_progress_command(
        repo, output, env, tmp_path, read_fd, target, True
    )

    # Then
    assert code == 130
    assert b"scheduled calls: 1" in stdout
    assert b"phase=running" in progress
    assert (b"\x1b" in progress) == tty


def test_blocked_stderr_does_not_delay_signal_cleanup(tmp_path: Path) -> None:
    # Given
    repo = make_repository(tmp_path / "repo")
    output = tmp_path / "evidence"
    env = environment(tmp_path)
    read_fd, target = full_pipe()

    # When
    code, stdout, _ = signal_progress_command(
        repo, output, env, tmp_path, read_fd, target, False
    )

    # Then
    assert code == 130
    assert b"scheduled calls: 1" in stdout
    record = json.loads((output / "run.json").read_text())
    assert record["state"] == "incomplete"
    assert record["calls"][0]["attempts"][0]["cleanup"]["direct_wait"] == "reaped"


def progress_destination(tty: bool) -> tuple[int, int]:
    """Return a terminal or pipe pair for progress output."""
    if tty:
        import pty

        return pty.openpty()
    return os.pipe()


def full_pipe() -> tuple[int, int]:
    """Fill a pipe before starting the command and restore blocking mode."""
    read_fd, target = os.pipe()
    os.set_blocking(target, False)
    try:
        while True:
            os.write(target, b"x" * 512)
    except BlockingIOError:
        pass
    os.set_blocking(target, True)
    return read_fd, target


def signal_progress_command(
    repo: Path,
    output: Path,
    env: dict[str, str],
    directory: Path,
    read_fd: int,
    target: int,
    read_progress: bool,
) -> tuple[int | None, bytes, bytes]:
    """Wait for the fake child and optionally observe progress before cancelling."""
    ready = directory / "ready"
    os.mkfifo(ready)
    ready_fd = os.open(ready, os.O_RDONLY | os.O_NONBLOCK)
    env["FAKE_READY_FIFO"] = str(ready)
    process = subprocess.Popen(
        command(repo, output), cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=target
    )
    os.close(target)
    try:
        empty: list[int] = []
        assert select.select([ready_fd], empty, empty, 15)[0]
        assert os.read(ready_fd, 100) == b"ready\n"
        progress = b""
        if read_progress:
            assert select.select([read_fd], empty, empty, 5)[0]
            progress = os.read(read_fd, 16384)
        process.send_signal(signal.SIGTERM)
        stdout, _ = process.communicate(timeout=15)
        return process.returncode, stdout, progress
    finally:
        os.close(ready_fd)
        os.close(read_fd)
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)


def test_blocked_stderr_does_not_delay_successful_exit(tmp_path: Path) -> None:
    # Given
    repo = make_repository(tmp_path / "repo")
    output = tmp_path / "evidence"
    env = environment(tmp_path)
    read_fd, target = full_pipe()
    process = subprocess.Popen(
        command(repo, output), cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=target
    )
    os.close(target)

    # When
    try:
        stdout, _ = process.communicate(timeout=15)
    finally:
        os.close(read_fd)
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)

    # Then
    assert process.returncode == 0
    assert b"scheduled calls: 1" in stdout
    record = json.loads((output / "run.json").read_text())
    assert record["state"] == "complete"
    assert record["calls"][0]["state"] == "complete"
