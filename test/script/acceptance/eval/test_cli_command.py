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
    ("fake_exit", "expected"), [("0", 0), ("7", 1)], ids=["success", "failed-attempt"]
)
def test_command_records_fake_attempt_and_maps_outcome(
    tmp_path: Path, fake_exit: str, expected: int
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
    assert record["calls"][0]["state"] == ("complete" if expected == 0 else "failed")


def test_quota_wait_fails_before_provider_binding(tmp_path: Path) -> None:
    # Given
    repo = make_repository(tmp_path / "repo")
    output = tmp_path / "evidence"
    env = environment(tmp_path)

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
