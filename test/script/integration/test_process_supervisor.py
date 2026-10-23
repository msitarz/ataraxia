# SPDX-License-Identifier: Apache-2.0
"""Exercise bounded session ownership with disposable real processes."""

from collections.abc import Callable, Iterator
import json
import math
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import time
from typing import cast

import pytest

from script import process_supervisor

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
FIXTURE = FIXTURES / "bounded_process.py"
WORKER = FIXTURES / "bounded_process_worker.py"


@pytest.fixture
def cleanup_children() -> Iterator[Callable[[Path], None]]:
    """Kill any fixture child left behind by a failing supervisor assertion."""
    markers: list[Path] = []
    yield markers.append
    for marker in markers:
        if marker.exists():
            _kill_pid(int(marker.read_text(encoding="utf-8")))


def _kill_pid(pid: int) -> None:
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + 1
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(0.01, remaining))


def _assert_pid_absent(pid: int) -> None:
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)


def _environment() -> dict[str, str]:
    return dict(os.environ)


def _cancel_worker(
    worker: subprocess.Popen[bytes], server: socket.socket, signum: signal.Signals
) -> tuple[int, bytes, bytes]:
    connection, _ = server.accept()
    with connection:
        child_pid = int(connection.recv(64).decode())
    os.kill(worker.pid, signum)
    stdout, stderr = worker.communicate(timeout=5)
    return child_pid, stdout, stderr


def _verify_signal_result(
    worker: subprocess.Popen[bytes], server: socket.socket, signum: signal.Signals
) -> None:
    child_pid, stdout, stderr = _cancel_worker(worker, server, signum)
    observation = json.loads(stdout.decode())
    assert worker.returncode == 0, stderr.decode()
    assert observation == {
        "stop_reason": "cancelled",
        "cancellation_signal": signum.name,
        "cleanup_complete": True,
        "term_restored": True,
        "int_restored": True,
    }
    _assert_pid_absent(child_pid)


def run_fixture(*args: str) -> process_supervisor.ProcessResult:
    return process_supervisor.run_bounded(
        [sys.executable, str(FIXTURE), *args],
        timeout_seconds=3,
        cleanup_seconds=1,
        output_limit_bytes=1024,
        env=_environment(),
    )


@pytest.mark.parametrize(
    ("exit_code", "expected"),
    [(0, 0), (7, 7)],
    ids=["successful-leader", "known-nonzero-leader"],
)
def test_normal_exit_reaps_leader_and_reports_exact_status(
    tmp_path: Path,
    cleanup_children: Callable[[Path], None],
    exit_code: int,
    expected: int,
) -> None:
    """Prove that leader status is polled and reaped before cleanup."""
    # Given
    marker = tmp_path / "child-ready"
    cleanup_children(marker)

    # When
    result = run_fixture("leader", "closed", str(marker), str(exit_code))

    # Then
    assert result.returncode == expected
    assert result.stop_reason == "completed"
    assert result.cleanup_complete
    assert result.cleanup_observation == "group_absent"
    _assert_pid_absent(int(marker.read_text(encoding="utf-8")))


def test_leader_exit_with_descendant_holding_pipes_still_hits_deadline(
    tmp_path: Path, cleanup_children: Callable[[Path], None]
) -> None:
    """Detect a live descendant after its leader has exited and retain status."""
    # Given
    marker = tmp_path / "child-ready"
    cleanup_children(marker)

    # When
    result = process_supervisor.run_bounded(
        [sys.executable, str(FIXTURE), "leader", "hold", str(marker), "0"],
        timeout_seconds=1.5,
        cleanup_seconds=1,
        output_limit_bytes=1024,
        env=_environment(),
    )

    # Then
    child_pid = int(marker.read_text(encoding="utf-8"))
    assert result.returncode == 0
    assert result.stop_reason == "timeout"
    assert result.cleanup_complete
    _assert_pid_absent(child_pid)


def test_leader_exit_with_closed_descendant_pipes_still_cleans_group(
    tmp_path: Path, cleanup_children: Callable[[Path], None]
) -> None:
    """Do not equate pipe EOF with all owned descendants having exited."""
    # Given
    marker = tmp_path / "child-ready"
    cleanup_children(marker)

    # When
    result = run_fixture("leader", "closed", str(marker), "0")

    # Then
    assert result.returncode == 0
    assert result.cleanup_complete
    assert result.cleanup_observation == "group_absent"
    _assert_pid_absent(int(marker.read_text(encoding="utf-8")))


def test_closed_leader_pipes_do_not_end_operation_before_process_exit(
    tmp_path: Path, cleanup_children: Callable[[Path], None]
) -> None:
    """Keep the deadline active for a live leader that closed both pipes."""
    # Given
    marker = tmp_path / "child-ready"
    cleanup_children(marker)

    # When
    result = process_supervisor.run_bounded(
        [sys.executable, str(FIXTURE), "child", str(marker), "close", "normal"],
        timeout_seconds=0.5,
        cleanup_seconds=1,
        output_limit_bytes=1024,
        env=_environment(),
    )

    # Then
    assert result.stop_reason == "timeout"
    assert result.returncode == -signal.SIGTERM
    assert result.cleanup_complete
    _assert_pid_absent(int(marker.read_text(encoding="utf-8")))


def test_timeout_kills_term_resistant_descendant(
    tmp_path: Path, cleanup_children: Callable[[Path], None]
) -> None:
    """Escalate to KILL when an owned child handles TERM but keeps running."""
    # Given
    marker = tmp_path / "child-ready"
    cleanup_children(marker)
    term_marker = marker.with_suffix(".term")

    # When
    result = process_supervisor.run_bounded(
        [sys.executable, str(FIXTURE), "leader", "resist", str(marker), "0"],
        timeout_seconds=1.5,
        cleanup_seconds=1,
        output_limit_bytes=1024,
        env=_environment(),
    )

    # Then
    assert term_marker.exists()
    assert result.stop_reason == "timeout"
    assert result.returncode == 0
    assert result.cleanup_complete
    _assert_pid_absent(int(marker.read_text(encoding="utf-8")))


def test_combined_output_limit_keeps_exact_bounded_prefix() -> None:
    """Retain exactly the cap as stdout/stderr prefixes and signal overflow."""
    # Given

    # When
    result = process_supervisor.run_bounded(
        [sys.executable, str(FIXTURE), "burst"],
        timeout_seconds=3,
        cleanup_seconds=1,
        output_limit_bytes=100,
        env=_environment(),
    )

    # Then
    assert result.output_limit_hit
    assert result.stop_reason == "output_limit"
    assert len(result.stdout) + len(result.stderr) == 100
    assert set(result.stdout) <= {ord("O")}
    assert set(result.stderr) <= {ord("E")}
    assert result.cleanup_complete


def test_stdin_is_closed_when_no_input_contract_is_declared() -> None:
    """Do not inherit the test runner's input stream implicitly."""
    # Given

    # When
    result = process_supervisor.run_bounded(
        [sys.executable, str(FIXTURE), "stdin"],
        timeout_seconds=3,
        cleanup_seconds=1,
        output_limit_bytes=1024,
        env=_environment(),
    )

    # Then
    assert result.stdout == b"stdin-eof\n"
    assert result.returncode == 0


@pytest.mark.parametrize(
    ("timeout", "cleanup", "output", "message"),
    [
        (math.nan, 1, 10, "timeout_seconds"),
        (math.inf, 1, 10, "timeout_seconds"),
        (0, 1, 10, "timeout_seconds"),
        (301, 1, 10, "timeout_seconds"),
        (1, math.inf, 10, "cleanup_seconds"),
        (1, math.nan, 10, "cleanup_seconds"),
        (1, 11, 10, "cleanup_seconds"),
        (1, 1, 1024 * 1024 + 1, "output_limit_bytes"),
        (1, 1, True, "output_limit_bytes"),
        (1, 1, 1.5, "output_limit_bytes"),
    ],
    ids=[
        "nan-deadline",
        "infinite-deadline",
        "zero-deadline",
        "protocol-timeout-cap",
        "infinite-cleanup",
        "nan-cleanup",
        "cleanup-cap",
        "output-cap",
        "boolean-output-cap",
        "float-output-cap",
    ],
)
def test_invalid_or_unbounded_limits_refuse_before_launch(
    monkeypatch: pytest.MonkeyPatch,
    timeout: float,
    cleanup: float,
    output: object,
    message: str,
) -> None:
    """Reject unsafe limits before creating an external process."""

    # Given
    def refuse_launch(*args: object, **kwargs: object) -> None:
        raise AssertionError("process launch happened before limit validation")

    monkeypatch.setattr(process_supervisor.subprocess, "Popen", refuse_launch)

    # When / Then
    with pytest.raises(ValueError, match=message):
        process_supervisor.run_bounded(
            [sys.executable, str(FIXTURE), "burst"],
            timeout_seconds=timeout,
            cleanup_seconds=cleanup,
            output_limit_bytes=cast(int, output),
            env=_environment(),
        )


@pytest.mark.parametrize("signum", [signal.SIGINT, signal.SIGTERM])
def test_signal_cancellation_cleans_descendant_and_restores_handler(
    tmp_path: Path,
    cleanup_children: Callable[[Path], None],
    signum: signal.Signals,
) -> None:
    """Handle real SIGTERM at the owner boundary and restore its prior handler."""
    # Given
    marker = tmp_path / "signal-child"
    ready_path = Path("/tmp") / f"ataraxia-ready-{os.getpid()}.sock"
    cleanup_children(marker)
    ready_path.unlink(missing_ok=True)
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(ready_path))
    server.listen(1)
    server.settimeout(5)
    worker = subprocess.Popen(
        [sys.executable, str(WORKER), str(FIXTURE), str(marker), str(ready_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_environment(),
        start_new_session=True,
    )
    # When
    try:
        _verify_signal_result(worker, server, signum)
    finally:
        server.close()
        ready_path.unlink(missing_ok=True)
        if worker.poll() is None:
            os.kill(worker.pid, signal.SIGKILL)
            worker.communicate(timeout=3)


def test_permission_denial_fails_closed_and_preserves_primary_error(
    tmp_path: Path,
    cleanup_children: Callable[[Path], None],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep a read error primary when owned-group cleanup receives EPERM."""
    # Given
    marker = tmp_path / "permission-child"
    cleanup_children(marker)
    reads = 0

    def read_then_fail(fd: int, size: int) -> bytes:
        nonlocal reads
        reads += 1
        if reads == 1:
            return os.read(fd, size)
        raise OSError("primary read failure")

    def deny_group_signal(pgid: int, signum: int) -> None:
        raise PermissionError(1, "operation denied", pgid)

    monkeypatch.setattr(process_supervisor.os, "killpg", deny_group_signal)

    # When
    with pytest.raises(OSError, match="primary read failure") as caught:
        process_supervisor.run_bounded(
            [sys.executable, str(FIXTURE), "leader", "hold", str(marker), "0"],
            timeout_seconds=3,
            cleanup_seconds=0.2,
            output_limit_bytes=1024,
            env=_environment(),
            read_chunk=read_then_fail,
        )

    # Then
    child_pid = int(marker.read_text(encoding="utf-8"))
    details = vars(caught.value)
    assert len(details["stdout_prefix"]) + len(details["stderr_prefix"]) > 0
    assert details["cleanup_complete"] is False
    assert "PermissionError" in details["cleanup_error"]
    assert os.kill(child_pid, 0) is None


def test_keyboard_interrupt_is_preserved_after_owned_cleanup(
    tmp_path: Path, cleanup_children: Callable[[Path], None]
) -> None:
    """Keep KeyboardInterrupt primary while cleaning the owned descendant."""
    # Given
    marker = tmp_path / "interrupt-child"
    cleanup_children(marker)

    def interrupt_read(fd: int, size: int) -> bytes:
        raise KeyboardInterrupt("injected cancellation")

    # When
    with pytest.raises(KeyboardInterrupt, match="injected cancellation") as caught:
        process_supervisor.run_bounded(
            [sys.executable, str(FIXTURE), "leader", "hold", str(marker), "0"],
            timeout_seconds=3,
            cleanup_seconds=1,
            output_limit_bytes=1024,
            env=_environment(),
            read_chunk=interrupt_read,
        )

    # Then
    assert marker.exists()
    assert vars(caught.value)["cleanup_complete"] is True
    _assert_pid_absent(int(marker.read_text(encoding="utf-8")))


def test_unverified_group_never_receives_a_signal(
    tmp_path: Path,
    cleanup_children: Callable[[Path], None],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Refuse group cleanup when the process identity check disagrees."""
    # Given
    marker = tmp_path / "unverified-child"
    cleanup_children(marker)
    observed_pid: list[int] = []

    def wrong_group(pid: int) -> int:
        observed_pid.append(pid)
        return pid + 1

    def forbidden_signal(pgid: int, signum: int) -> None:
        raise AssertionError("an unverified group was signalled")

    monkeypatch.setattr(process_supervisor.os, "killpg", forbidden_signal)

    # When
    with pytest.raises(ValueError, match="dedicated session group") as caught:
        process_supervisor.run_bounded(
            [sys.executable, str(FIXTURE), "child", str(marker), "hold", "normal"],
            timeout_seconds=3,
            cleanup_seconds=1,
            output_limit_bytes=1024,
            env=_environment(),
            get_process_group_id=wrong_group,
        )

    # Then
    assert observed_pid
    details = vars(caught.value)
    assert details["cleanup_complete"] is False
    assert details["cleanup_observation"] == "group_unresolved"
    assert "descendants remain unverified" in details["cleanup_error"]
    _assert_pid_absent(observed_pid[0])


@pytest.mark.real_tool
def test_installed_codex_version_runs_through_the_process_owner() -> None:
    """Check installed CLI startup and leader reaping without a model call."""
    # Given
    codex = shutil.which("codex")
    if codex is None:
        pytest.skip("codex CLI is not installed; host process identity is unobserved")

    # When
    result = process_supervisor.run_bounded(
        [codex, "--version"],
        timeout_seconds=10,
        cleanup_seconds=2,
        output_limit_bytes=64 * 1024,
        env=_environment(),
    )

    # Then
    version = result.stdout.decode().strip()
    assert version.startswith("codex-cli ")
    assert result.returncode == 0
    assert result.cleanup_complete
