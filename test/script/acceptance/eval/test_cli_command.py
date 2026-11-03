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

from script.reviewer_eval.context import CASES, CORPUS, SHARED
from script.reviewer_eval.report import inspect_run
from test.script.integration.eval.support import (
    git,
    git_test_environment,
    make_repository,
)

ROOT = Path(__file__).resolve().parents[4]
FIXTURE = ROOT / "test/script/fixtures/eval/fake_codex.py"


def command(repository: Path, output: Path, model: str = "model") -> list[str]:
    return [
        sys.executable,
        "-m",
        "script.eval",
        "-d",
        str(repository / "context"),
        "-m",
        model,
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


def test_quota_wait_refuses_unsupported_cli_version(tmp_path: Path) -> None:
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
    assert result.returncode == 3
    assert "requires Codex CLI 0.164.0" in result.stderr
    assert output.exists()
    assert marker.read_text().strip() == "--version"


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
    env = environment(tmp_path)
    marker = tmp_path / "provider-invocations"
    env["FAKE_ARGV_LOG"] = str(marker)
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
        "-o",
        str(output),
    ]

    # When
    result = subprocess.run(
        arguments, cwd=ROOT, env=env, capture_output=True, text=True, timeout=20
    )

    # Then
    assert result.returncode == 0, result.stderr
    assert "Dry run: 1 calls; no Codex calls or output directory" in result.stdout
    assert (
        "0: model=unsupported-model effort=low context tokens=UNKNOWN" in result.stdout
    )
    assert "source: 'context/" in result.stdout
    assert "compatibility=unknown" in result.stdout
    assert result.stderr == ""
    assert not output.exists()
    assert not marker.exists()


def run_signalled(
    repo: Path,
    output: Path,
    env: dict[str, str],
    directory: Path,
    sent_signal: signal.Signals,
    controls: tuple[str, ...] = (),
) -> tuple[int | None, bytes, bytes]:
    """Wait for the fake child to start, then signal the command and join it."""
    fifo = directory / "ready"
    os.mkfifo(fifo)
    fd = os.open(fifo, os.O_RDONLY | os.O_NONBLOCK)
    env["FAKE_READY_FIFO"] = str(fifo)
    process = subprocess.Popen(
        [*command(repo, output), *controls],
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
    assert b"Status: running" in progress
    assert progress.endswith(b"\n")


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


def test_quota_wait_resumes_after_two_separate_probes(tmp_path: Path) -> None:
    # Given
    repo = make_repository(tmp_path / "repo")
    output = tmp_path / "evidence"
    env = environment(tmp_path)
    binary = tmp_path / "bin" / "codex"
    shutil.copyfile(ROOT / "test/script/fixtures/eval/fake_quota_codex.py", binary)
    binary.chmod(0o755)
    home = tmp_path / "codex-home"
    home.mkdir()
    env["CODEX_HOME"] = str(home)
    env["FAKE_QUOTA_STATE"] = str(tmp_path / "counts.json")
    env["FAKE_CLI_VERSION"] = "0.165.0"

    # When
    result = subprocess.run(
        [
            *command(repo, output),
            "--wait-for-quota",
            "--quota-poll-interval-seconds",
            "0.01",
            "--quota-probe-budget",
            "2",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    # Then
    assert result.returncode == 0, result.stderr
    assert json.loads(Path(env["FAKE_QUOTA_STATE"]).read_text()) == {
        "eval": 2,
        "probe": 2,
    }
    record = json.loads((output / "run.json").read_text())
    assert record["calls"][0]["state"] == "complete"
    assert len(record["calls"][0]["attempts"]) == 2
    prompts = (
        Path(env["FAKE_QUOTA_STATE"]).with_suffix(".prompts").read_text().splitlines()
    )
    assert len(prompts) == 2 and prompts[0] == prompts[1]
    events = [
        json.loads(line)["event"]
        for line in (output / "events.jsonl").read_text().splitlines()
    ]
    assert [
        event["record"]["quota_state"]
        for event in events
        if event.get("kind") == "settled"
    ] == ["exhausted", "available"]


@pytest.mark.parametrize(
    ("mode", "exit_status", "counts", "diagnostic"),
    [
        (
            "missing-session",
            3,
            {"eval": 1, "probe": 0},
            "quota telemetry is unavailable or unsupported",
        ),
        (
            "wrong-version",
            3,
            {"eval": 1, "probe": 0},
            "quota telemetry is unavailable or unsupported",
        ),
        (
            "out-of-order",
            3,
            {"eval": 1, "probe": 0},
            "quota telemetry is unavailable or unsupported",
        ),
        ("mismatch", 3, {"eval": 1, "probe": 1}, "quota recovery failed"),
        (
            "extra-event",
            3,
            {"eval": 1, "probe": 0},
            "quota telemetry is unavailable or unsupported",
        ),
        (
            "stderr",
            3,
            {"eval": 1, "probe": 0},
            "quota telemetry is unavailable or unsupported",
        ),
    ],
)
def test_quota_wait_refuses_unverified_or_ambiguous_evidence(
    tmp_path: Path, mode: str, exit_status: int, counts: dict[str, int], diagnostic: str
) -> None:
    # Given
    repo = make_repository(tmp_path / "repo")
    output = tmp_path / "evidence"
    env = environment(tmp_path)
    binary = tmp_path / "bin" / "codex"
    shutil.copyfile(ROOT / "test/script/fixtures/eval/fake_quota_codex.py", binary)
    binary.chmod(0o755)
    home = tmp_path / "codex-home"
    home.mkdir()
    env["CODEX_HOME"] = str(home)
    env["FAKE_QUOTA_STATE"] = str(tmp_path / "counts.json")
    env["FAKE_QUOTA_MODE"] = mode
    env["FAKE_CLI_VERSION"] = "0.165.0"

    # When
    result = subprocess.run(
        [
            *command(repo, output),
            "--wait-for-quota",
            "--quiet",
            "--quota-poll-interval-seconds",
            "0.01",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    # Then
    assert result.returncode == exit_status, result.stderr
    assert json.loads(Path(env["FAKE_QUOTA_STATE"]).read_text()) == counts
    assert diagnostic in result.stderr
    events = [
        json.loads(line) for line in (output / "events.jsonl").read_text().splitlines()
    ]
    assert any(event["kind"] == "quota_telemetry" for event in events)
    assert json.loads((output / "run.json").read_text())["state"] == "incomplete"


def test_quota_probe_budget_zero_stops_without_probe(tmp_path: Path) -> None:
    # Given
    repo = make_repository(tmp_path / "repo")
    output = tmp_path / "evidence"
    env = environment(tmp_path)
    binary = tmp_path / "bin" / "codex"
    shutil.copyfile(ROOT / "test/script/fixtures/eval/fake_quota_codex.py", binary)
    binary.chmod(0o755)
    home = tmp_path / "codex-home"
    home.mkdir()
    env["CODEX_HOME"] = str(home)
    env["FAKE_QUOTA_STATE"] = str(tmp_path / "counts.json")

    # When
    result = subprocess.run(
        [*command(repo, output), "--wait-for-quota", "--quota-probe-budget", "0"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    # Then
    assert result.returncode == 3, result.stderr
    assert json.loads(Path(env["FAKE_QUOTA_STATE"]).read_text()) == {
        "eval": 1,
        "probe": 0,
    }
    record = json.loads((output / "run.json").read_text())
    assert record["waits"][0]["end"] == "bound"


@pytest.mark.parametrize("codex_home", ["", "relative", "missing"])
def test_quota_wait_rejects_unsupported_codex_home(
    tmp_path: Path, codex_home: str
) -> None:
    # Given
    repo = make_repository(tmp_path / "repo")
    output = tmp_path / "evidence"
    env = environment(tmp_path)
    binary = tmp_path / "bin" / "codex"
    shutil.copyfile(ROOT / "test/script/fixtures/eval/fake_quota_codex.py", binary)
    binary.chmod(0o755)
    env["CODEX_HOME"] = (
        str(tmp_path / "missing") if codex_home == "missing" else codex_home
    )
    env["FAKE_QUOTA_STATE"] = str(tmp_path / "counts.json")

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
    assert result.returncode == 3, result.stderr
    assert "Codex home" in result.stderr or "CODEX_HOME" in result.stderr
    assert not Path(env["FAKE_QUOTA_STATE"]).exists()


@pytest.mark.parametrize(
    ("mode", "retry_options", "expected_exit", "attempts", "state"),
    [
        ("success", [], 1, 1, "failed"),
        (
            "success",
            [
                "--capacity-backoff-base-seconds",
                "0.001",
                "--capacity-backoff-cap-seconds",
                "0.001",
                "--capacity-retry-limit",
                "1",
            ],
            0,
            2,
            "complete",
        ),
        (
            "exhaust",
            [
                "--capacity-backoff-base-seconds",
                "0.001",
                "--capacity-backoff-cap-seconds",
                "0.001",
                "--capacity-retry-limit",
                "1",
            ],
            1,
            2,
            "failed",
        ),
        (
            "ambiguous",
            [
                "--capacity-backoff-base-seconds",
                "0.001",
                "--capacity-backoff-cap-seconds",
                "0.001",
                "--capacity-retry-limit",
                "1",
            ],
            1,
            1,
            "failed",
        ),
    ],
    ids=["default-zero", "retry-success", "exhausted", "ambiguous"],
)
def test_capacity_retries_use_the_same_frozen_invocation(
    tmp_path: Path,
    mode: str,
    retry_options: list[str],
    expected_exit: int,
    attempts: int,
    state: str,
) -> None:
    # Given
    repo = make_repository(tmp_path / "repo")
    instructions = add_capacity_instructions(repo)
    output = tmp_path / "evidence"
    env = environment(tmp_path)
    binary = tmp_path / "bin" / "codex"
    shutil.copyfile(ROOT / "test/script/fixtures/eval/fake_capacity_codex.py", binary)
    binary.chmod(0o755)
    log = tmp_path / "invocations.jsonl"
    env["FAKE_CAPACITY_LOG"] = str(log)
    env["FAKE_CAPACITY_MODE"] = mode
    settings = ["--instructions-file", str(instructions), *retry_options]

    # When
    result = subprocess.run(
        [*command(repo, output), *settings],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    # Then
    assert result.returncode == expected_exit, result.stderr
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    assert len(calls) == attempts
    assert len({call["pid"] for call in calls}) == attempts
    assert all(call["argv"] == calls[0]["argv"] for call in calls)
    assert all(call["instructions"] == calls[0]["instructions"] for call in calls)
    assert calls[0]["instructions"] == "frozen instructions"
    assert "--model=model" in calls[0]["argv"] and "context" in calls[0]["argv"]
    record = json.loads((output / "run.json").read_text())
    assert record["calls"][0]["state"] == state
    assert len(record["calls"][0]["attempts"]) == attempts


def add_capacity_instructions(repo: Path) -> Path:
    """Commit a frozen instructions input in the disposable repository.

    Returns:
        The committed instructions path.
    """
    instructions = repo / "instructions.txt"
    instructions.write_text("frozen instructions")
    git(repo, "add", "instructions.txt")
    git(repo, "commit", "-qm", "instructions")
    return instructions


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        (
            ["-m", "gpt-6-luna", "-e", "low", "-n"],
            "provide at least one -d/--directory",
        ),
        (
            ["-d", "missing", "-m", "model", "-e", "low", "-n", "--concurency", "2"],
            "Did you mean --concurrency?",
        ),
        ([""], "remove the empty or whitespace argument"),
    ],
    ids=["missing-directory", "unknown-option", "empty-argument"],
)
def test_invalid_command_exits_before_preparation(
    tmp_path: Path, arguments: list[str], message: str
) -> None:
    # Given
    env = environment(tmp_path)
    marker = tmp_path / "provider-invocations"
    env["FAKE_ARGV_LOG"] = str(marker)
    output = tmp_path / "evidence"

    # When
    result = subprocess.run(
        [sys.executable, "-m", "script.eval", *arguments, "-o", str(output)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    # Then
    assert result.returncode == 2
    assert message in result.stderr
    assert "usage:" not in result.stderr
    assert "input_value" not in result.stderr
    assert result.stdout == ""
    assert not output.exists()
    assert not marker.exists()


def test_explicit_subset_rerun_preserves_prior_evidence_and_identity(
    tmp_path: Path,
) -> None:
    # Given
    repo = make_repository(tmp_path / "repo")
    first_output = tmp_path / "first"
    second_output = tmp_path / "subset"
    env = environment(tmp_path)
    first = subprocess.run(
        [*command(repo, first_output), "-m", "another-model"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert first.returncode == 0, first.stderr
    before = {
        path.relative_to(first_output): path.read_bytes()
        for path in first_output.rglob("*")
        if path.is_file()
    }
    first_run = json.loads(before[Path("run.json")])

    # When
    second = subprocess.run(
        command(repo, second_output),
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    # Then
    assert second.returncode == 0, second.stderr
    after = {
        path.relative_to(first_output): path.read_bytes()
        for path in first_output.rglob("*")
        if path.is_file()
    }
    second_run = json.loads((second_output / "run.json").read_bytes())
    assert after == before
    assert len(first_run["calls"]) == 2
    assert len(second_run["calls"]) == 1
    assert first_run["calls"][0]["call_id"] == second_run["calls"][0]["call_id"]
    assert len(second_run["calls"][0]["attempts"]) == 1


@pytest.mark.parametrize(
    ("settings", "colored", "forbidden"),
    [
        ({"TERM": "xterm"}, True, ()),
        ({"TERM": "xterm", "NO_COLOR": "1"}, False, ()),
        ({"TERM": "dumb"}, False, (b"\x1b",)),
    ],
    ids=["color", "no-color", "dumb"],
)
def test_shared_terminal_keeps_final_result_separate(
    tmp_path: Path,
    settings: dict[str, str],
    colored: bool,
    forbidden: tuple[bytes, ...],
) -> None:
    # Given
    import fcntl
    import pty
    import struct
    import termios

    repo = make_repository(tmp_path / "repo")
    output = tmp_path / "evidence"
    env = environment(tmp_path)
    env.pop("NO_COLOR", None)
    env.update(settings)
    read_fd, target = pty.openpty()
    fcntl.ioctl(target, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))

    # When
    code, text = shared_terminal_output(repo, output, env, read_fd, target)

    # Then
    assert code == 0
    assert b"Status: success" in text and b"Completed: 1" in text
    assert text.index(b"Status: success") < text.index(b"\r\nrun ")
    assert text.endswith(b"; 1 scheduled calls\r\n")
    assert (b"\x1b[36m" in text) == colored
    assert all(marker not in text for marker in forbidden)
    assert json.loads((output / "run.json").read_text())["state"] == "complete"


def shared_terminal_output(
    repo: Path, output: Path, env: dict[str, str], read_fd: int, target: int
) -> tuple[int, bytes]:
    """Run the controlled command with both streams on a drained terminal.

    Returns:
        The exit code and terminal transcript.
    """
    process = subprocess.Popen(
        command(repo, output), cwd=ROOT, env=env, stdout=target, stderr=target
    )
    os.close(target)
    chunks: list[bytes] = []
    try:
        while True:
            empty: list[int] = []
            ready, _, _ = select.select([read_fd], empty, empty, 15)
            assert ready, "terminal output timed out"
            try:
                data = os.read(read_fd, 65536)
            except OSError:
                break
            if not data:
                break
            chunks.append(data)
        code = process.wait(timeout=15)
    finally:
        os.close(read_fd)
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
    return code, b"".join(chunks)


def test_dry_run_displays_controls_without_mutating_borrowed_workspace(
    tmp_path: Path,
) -> None:
    # Given
    repo = make_repository(tmp_path / "repo")
    output = tmp_path / "evidence"
    workspace = tmp_path / "workspace"
    workspace.mkdir(mode=0o750)
    marker = workspace / "keep"
    marker.write_text("unchanged")
    permissions = workspace.stat().st_mode
    env = environment(tmp_path)
    provider_log = tmp_path / "provider-invocations"
    env["FAKE_ARGV_LOG"] = str(provider_log)
    arguments = [
        *command(repo, output, "unsupported-model"),
        "-n",
        "--working-directory",
        "workspace",
        "--sandbox-mode",
        "workspace-write",
        "--enable-tools",
    ]

    # When
    result = subprocess.run(
        arguments, cwd=tmp_path, env=env, capture_output=True, text=True, timeout=20
    )

    # Then
    assert result.returncode == 0, result.stderr
    assert f"Working directory: {workspace.resolve()}" in result.stdout
    assert "Sandbox: workspace-write; tools enabled: True" in result.stdout
    assert marker.read_text() == "unchanged"
    assert workspace.stat().st_mode == permissions
    assert not output.exists()
    assert not provider_log.exists()


def test_nondefault_controls_reach_the_fake_codex(tmp_path: Path) -> None:
    # Given
    repo = make_repository(tmp_path / "repo")
    output = tmp_path / "evidence"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    marker = workspace / "marker"
    marker.write_bytes(b"unchanged")
    permissions = workspace.stat().st_mode
    env = environment(tmp_path)
    provider_log = tmp_path / "provider-invocations"
    env["FAKE_ARGV_LOG"] = str(provider_log)

    # When
    result = subprocess.run(
        [
            *command(repo, output),
            "--working-directory",
            "workspace",
            "--sandbox-mode",
            "workspace-write",
            "--enable-tools",
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    # Then
    assert result.returncode == 0, result.stderr
    record = json.loads((output / "run.json").read_text())
    attempt = record["calls"][0]["attempts"][0]
    assert record["effective_settings"][0] == [
        "invocation_profile",
        "execution-controls-v3",
    ]
    assert provider_log.read_text().count("\n") == 2
    assert attempt["cwd"] == str(workspace.resolve())
    assert attempt["argv"][attempt["argv"].index("--sandbox") + 1] == "workspace-write"
    assert attempt["argv"][attempt["argv"].index("shell_tool") - 1] == "--enable"
    assert marker.read_bytes() == b"unchanged"
    assert workspace.stat().st_mode == permissions


def test_borrowed_workspace_survives_failed_attempt(tmp_path: Path) -> None:
    # Given
    repo = make_repository(tmp_path / "repo")
    output = tmp_path / "evidence"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    marker = workspace / "marker"
    marker.write_bytes(b"unchanged")
    permissions = workspace.stat().st_mode
    env = environment(tmp_path)
    env["FAKE_EXIT"] = "7"

    # When
    result = subprocess.run(
        [*command(repo, output), "--working-directory", str(workspace)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    # Then
    assert result.returncode == 1, result.stderr
    assert marker.read_bytes() == b"unchanged"
    assert workspace.stat().st_mode == permissions


def test_borrowed_workspace_survives_cancellation(tmp_path: Path) -> None:
    # Given
    repo = make_repository(tmp_path / "repo")
    output = tmp_path / "evidence"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    marker = workspace / "marker"
    marker.write_bytes(b"unchanged")
    permissions = workspace.stat().st_mode
    env = environment(tmp_path)

    # When
    code, _, stderr = run_signalled(
        repo,
        output,
        env,
        tmp_path,
        signal.SIGTERM,
        ("--working-directory", str(workspace)),
    )

    # Then
    assert code == 130, stderr.decode()
    assert marker.read_bytes() == b"unchanged"
    assert workspace.stat().st_mode == permissions


def copy_reviewer_input(repo: Path, name: str) -> None:
    """Copy one real prepared input into the controlled Git repository."""
    target = repo / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((ROOT / name).read_bytes())


def test_controlled_standalone_evidence_is_read_by_saved_report(tmp_path: Path) -> None:
    # Given
    repo = make_repository(tmp_path / "repo")
    case = next(iter(CASES))
    copy_reviewer_input(repo, SHARED)
    copy_reviewer_input(repo, case)
    copy_reviewer_input(repo, CORPUS)
    git(repo, "add", "--all")
    git(repo, "commit", "-qm", "reviewer inputs")
    workspace = tmp_path / "clone"
    workspace.mkdir()
    output = tmp_path / "evidence"
    env = environment(tmp_path)
    arguments = [
        sys.executable,
        "-m",
        "script.eval",
        "-d",
        str((repo / SHARED).parent),
        "-d",
        str((repo / case).parent),
        "-d",
        str((repo / CORPUS).parent),
        "-m",
        "model",
        "-e",
        "low",
        "-o",
        str(output),
        "--working-directory",
        str(workspace),
        "--sandbox-mode",
        "workspace-write",
        "--enable-tools",
    ]

    # When
    command_result = subprocess.run(
        arguments,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )
    result = inspect_run(output)

    # Then
    assert command_result.returncode == 0, command_result.stderr
    assert result.evidence_state == "complete"
    assert result.calls[0].state == "invalid"  # Fake transcript has no answer.


def test_writable_overlap_refused_before_provider_or_output(tmp_path: Path) -> None:
    # Given
    repo = make_repository(tmp_path / "repo")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (tmp_path / "alias").symlink_to(workspace, target_is_directory=True)
    output = tmp_path / "alias" / "nested" / "evidence"
    env = environment(tmp_path)
    log = tmp_path / "provider-invocations"
    env["FAKE_ARGV_LOG"] = str(log)

    # When
    result = subprocess.run(
        [
            *command(repo, output),
            "--working-directory",
            str(workspace),
            "--sandbox-mode",
            "workspace-write",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    # Then
    assert result.returncode == 1
    assert "--output-directory must be outside" in result.stderr
    assert not output.exists()
    assert not log.exists()


def test_writable_concurrency_refused_before_provider_or_output(tmp_path: Path) -> None:
    # Given
    repo = make_repository(tmp_path / "repo")
    output = tmp_path / "evidence"
    env = environment(tmp_path)
    log = tmp_path / "provider-invocations"
    env["FAKE_ARGV_LOG"] = str(log)

    # When
    result = subprocess.run(
        [*command(repo, output), "--sandbox-mode", "workspace-write", "-c", "2"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    # Then
    assert result.returncode == 2
    assert "--concurrency 1" in result.stderr
    assert not output.exists()
    assert not log.exists()


def test_existing_git_workspace_is_shared_by_calls(tmp_path: Path) -> None:
    # Given
    repo = make_repository(tmp_path / "repo")
    workspace = make_repository(tmp_path / "workspace")
    marker = workspace / "context" / "input.txt"
    permissions = workspace.stat().st_mode
    output = tmp_path / "evidence"
    env = environment(tmp_path)

    # When
    result = subprocess.run(
        [*command(repo, output), "--working-directory", str(workspace), "-m", "other"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    # Then
    assert result.returncode == 0, result.stderr
    calls = json.loads((output / "run.json").read_text())["calls"]
    assert len(calls) == 2
    assert calls[0]["attempts"][0]["cwd"] == str(workspace.resolve())
    assert calls[1]["attempts"][0]["cwd"] == str(workspace.resolve())
    assert marker.read_bytes() == b"context"
    assert workspace.stat().st_mode == permissions
