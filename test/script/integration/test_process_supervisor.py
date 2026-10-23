# SPDX-License-Identifier: Apache-2.0
"""Exercise bounded session ownership with disposable real processes."""

import asyncio
from collections.abc import Callable, Coroutine, Iterator
from contextlib import suppress
from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from typing import cast, override

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


@pytest.fixture
def socket_directory() -> Iterator[Path]:
    """Provide short, isolated POSIX socket paths on macOS and Linux."""
    with tempfile.TemporaryDirectory(prefix="ata-", dir="/tmp") as directory:
        yield Path(directory)


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
    return run_bounded_sync(
        [sys.executable, str(FIXTURE), *args],
        timeout_seconds=3,
        cleanup_seconds=1,
        output_limit_bytes=1024,
        env=_environment(),
    )


def run_bounded_sync(
    argv: list[str],
    *,
    timeout_seconds: float,
    cleanup_seconds: float,
    output_limit_bytes: int,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    cancel_event: asyncio.Event | None = None,
    get_process_group_id: Callable[[int], int] = os.getpgid,
    on_data: Callable[[int, bytes], None] | None = None,
) -> process_supervisor.ProcessResult:
    """Adapt one invocation for the synchronous integration cases."""

    async def execute() -> process_supervisor.ProcessResult:
        try:
            return await process_supervisor.run_bounded(
                argv,
                timeout_seconds=timeout_seconds,
                cleanup_seconds=cleanup_seconds,
                output_limit_bytes=output_limit_bytes,
                cwd=cwd,
                env=env,
                cancel_event=cancel_event,
                get_process_group_id=get_process_group_id,
                on_data=on_data,
            )
        finally:
            current = asyncio.current_task()
            pending = [
                task
                for task in asyncio.all_tasks()
                if task is not current and not task.done()
            ]
            assert not pending, f"owned tasks remained pending: {pending!r}"

    return asyncio.run(execute())


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
    result = run_bounded_sync(
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
    result = run_bounded_sync(
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
    result = run_bounded_sync(
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
    result = run_bounded_sync(
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


def test_output_exactly_at_cap_is_not_overflow() -> None:
    """Accept output equal to the shared cap without truncation."""
    # Given

    # When
    result = run_bounded_sync(
        [sys.executable, str(FIXTURE), "burst"],
        timeout_seconds=3,
        cleanup_seconds=1,
        output_limit_bytes=160,
        env=_environment(),
    )

    # Then
    assert len(result.stdout) + len(result.stderr) == 160
    assert not result.output_limit_hit
    assert result.stop_reason == "completed"
    assert result.cleanup_complete


class _CompletionBarrier(asyncio.SubprocessProtocol):
    """Forward subprocess callbacks and report leader-plus-pipe completion."""

    def __init__(self, inner: asyncio.SubprocessProtocol) -> None:
        self.inner = inner
        self.complete = asyncio.Event()
        self.leader_exited = False
        self.stdout_eof = False
        self.stderr_eof = False

    @override
    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.inner.connection_made(transport)

    @override
    def pipe_data_received(self, fd: int, data: bytes) -> None:
        self.inner.pipe_data_received(fd, data)

    @override
    def pipe_connection_lost(self, fd: int, exc: Exception | None) -> None:
        self.inner.pipe_connection_lost(fd, exc)
        if fd == 1:
            self.stdout_eof = True
        elif fd == 2:
            self.stderr_eof = True
        self._set_if_complete()

    @override
    def process_exited(self) -> None:
        self.inner.process_exited()
        self.leader_exited = True
        self._set_if_complete()

    @override
    def connection_lost(self, exc: Exception | None) -> None:
        self.inner.connection_lost(exc)

    def _set_if_complete(self) -> None:
        if self.leader_exited and self.stdout_eof and self.stderr_eof:
            self.complete.set()


async def _run_after_completion_callbacks(
    monkeypatch: pytest.MonkeyPatch,
    output_limit_bytes: int,
    on_data: Callable[[int, bytes], None] | None = None,
) -> process_supervisor.ProcessResult:
    loop = asyncio.get_running_loop()
    original_spawn = loop.subprocess_exec
    barriers: list[_CompletionBarrier] = []

    async def wait_for_callbacks(
        protocol_factory: Callable[[], asyncio.SubprocessProtocol],
        program: str,
        *args: str,
        stdin: int | None = None,
        stdout: int | None = None,
        stderr: int | None = None,
        cwd: str | bytes | os.PathLike[str] | os.PathLike[bytes] | None = None,
        env: dict[str, str] | None = None,
        start_new_session: bool = False,
    ) -> tuple[asyncio.SubprocessTransport, asyncio.SubprocessProtocol]:
        def make_barrier() -> _CompletionBarrier:
            barrier = _CompletionBarrier(protocol_factory())
            barriers.append(barrier)
            return barrier

        result = await original_spawn(
            make_barrier,
            program,
            *args,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            cwd=cwd,
            env=env,
            start_new_session=start_new_session,
        )
        await asyncio.wait_for(barriers[0].complete.wait(), 3)
        return result

    monkeypatch.setattr(loop, "subprocess_exec", wait_for_callbacks)
    return await process_supervisor.run_bounded(
        [sys.executable, str(FIXTURE), "burst"],
        timeout_seconds=3,
        cleanup_seconds=1,
        output_limit_bytes=output_limit_bytes,
        env=_environment(),
        on_data=on_data,
    )


def test_public_run_reports_overflow_after_all_completion_callbacks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Report output overflow even when leader and both pipes finish first."""
    # Given
    output_limit_bytes = 1

    # When
    result = asyncio.run(
        _run_after_completion_callbacks(monkeypatch, output_limit_bytes)
    )

    # Then
    assert result.stop_reason == "output_limit"
    assert result.output_limit_hit
    assert len(result.stdout) + len(result.stderr) == output_limit_bytes
    assert result.cleanup_complete


def test_public_run_preserves_callback_error_after_all_completion_callbacks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep the first output callback error when completion callbacks arrived."""
    # Given
    failure = OSError("output callback failed")

    def fail_output(fd: int, data: bytes) -> None:
        raise failure

    # When
    with pytest.raises(OSError, match="output callback failed") as caught:
        asyncio.run(_run_after_completion_callbacks(monkeypatch, 1024, fail_output))

    # Then
    assert caught.value is failure
    assert vars(caught.value)["cleanup_complete"] is True


def test_concurrent_invocations_keep_output_isolated() -> None:
    """Collect each concurrent command's stdout and stderr independently."""

    async def exercise() -> list[process_supervisor.ProcessResult]:
        async with asyncio.TaskGroup() as group:
            tasks = [
                group.create_task(
                    process_supervisor.run_bounded(
                        [sys.executable, str(FIXTURE), "tagged", tag],
                        timeout_seconds=3,
                        cleanup_seconds=1,
                        output_limit_bytes=1024,
                        env=_environment(),
                    )
                )
                for tag in ("alpha", "beta")
            ]
        return [task.result() for task in tasks]

    # Given

    # When
    results = asyncio.run(exercise())

    # Then
    assert [(result.stdout, result.stderr) for result in results] == [
        (b"out:alpha\n", b"err:alpha\n"),
        (b"out:beta\n", b"err:beta\n"),
    ]


async def _accept_pid(server: socket.socket) -> int:
    loop = asyncio.get_running_loop()
    connection, _ = await asyncio.wait_for(loop.sock_accept(server), 3)
    with connection:
        return int(await loop.sock_recv(connection, 64))


async def _accept_connection(server: socket.socket) -> tuple[socket.socket, int]:
    loop = asyncio.get_running_loop()
    connection, _ = await asyncio.wait_for(loop.sock_accept(server), 3)
    pid = int(await asyncio.wait_for(loop.sock_recv(connection, 64), 3))
    return connection, pid


def _gated_invocation(
    marker: Path, ready_path: Path
) -> Coroutine[None, None, process_supervisor.ProcessResult]:
    return process_supervisor.run_bounded(
        [sys.executable, str(FIXTURE), "gated", str(marker), str(ready_path)],
        timeout_seconds=10,
        cleanup_seconds=1,
        output_limit_bytes=1024,
        env=_environment(),
    )


def _release_connections(connections: list[socket.socket]) -> None:
    for connection in connections:
        with suppress(OSError):
            connection.sendall(b"exit")
        connection.close()


async def _recover_tasks[T](tasks: list[asyncio.Task[T]]) -> None:
    pending = [task for task in tasks if not task.done()]
    for task in pending:
        task.cancel()
    if pending:
        await asyncio.wait(pending, timeout=4)
    remaining = [task for task in tasks if not task.done()]
    assert not remaining, f"owned tasks did not settle: {remaining!r}"


async def _exercise_sibling_cancellation(
    markers: list[Path], ready_path: Path
) -> tuple[int, int, asyncio.CancelledError, process_supervisor.ProcessResult]:
    server = _readiness_server(ready_path, 2)
    connections: list[socket.socket] = []
    tasks = [
        asyncio.create_task(_gated_invocation(marker, ready_path)) for marker in markers
    ]
    pids: list[int] = []
    try:
        for _ in range(2):
            connection, pid = await _accept_connection(server)
            connections.append(connection)
            pids.append(pid)
        tasks[0].cancel()
        _release_connections([connections[1]])
        with pytest.raises(asyncio.CancelledError) as caught:
            await asyncio.wait_for(tasks[0], 3)
        sibling_result = await asyncio.wait_for(tasks[1], 3)
        return pids[0], pids[1], caught.value, sibling_result
    finally:
        _release_connections(connections)
        await _recover_tasks(tasks)
        server.close()
        ready_path.unlink(missing_ok=True)


async def _exercise_taskgroup_cancellation(
    markers: list[Path], ready_path: Path
) -> list[int]:
    server = _readiness_server(ready_path, 2)
    connections: list[socket.socket] = []
    pids: list[int] = []

    async def siblings() -> None:
        async with asyncio.TaskGroup() as group:
            for marker in markers:
                group.create_task(_gated_invocation(marker, ready_path))

    owner = asyncio.create_task(siblings())
    try:
        for _ in range(2):
            connection, pid = await _accept_connection(server)
            connections.append(connection)
            pids.append(pid)
        owner.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(owner, 4)
        return pids
    finally:
        _release_connections(connections)
        await _recover_tasks([owner])
        server.close()
        ready_path.unlink(missing_ok=True)


def test_task_cancellation_isolated_from_concurrent_sibling(
    tmp_path: Path,
    socket_directory: Path,
    cleanup_children: Callable[[Path], None],
) -> None:
    """Cancel one active child while its concurrently active sibling succeeds."""
    # Given
    markers = [tmp_path / "cancel-one", tmp_path / "finish-sibling"]
    ready_path = socket_directory / "i.sock"
    for marker in markers:
        cleanup_children(marker)
    ready_path.unlink(missing_ok=True)

    # When
    cancelled_pid, sibling_pid, cancellation, sibling_result = asyncio.run(
        _exercise_sibling_cancellation(markers, ready_path)
    )

    # Then
    assert vars(cancellation)["cleanup_complete"] is True
    assert sibling_result is not None
    assert sibling_result.returncode == 0
    _assert_pid_absent(cancelled_pid)
    _assert_pid_absent(sibling_pid)


def test_task_group_cancellation_cleans_each_owned_child(
    tmp_path: Path,
    socket_directory: Path,
    cleanup_children: Callable[[Path], None],
) -> None:
    """TaskGroup cancellation settles every independently owned invocation."""
    # Given
    markers = [tmp_path / "group-one", tmp_path / "group-two"]
    ready_path = socket_directory / "g.sock"
    for marker in markers:
        cleanup_children(marker)
    ready_path.unlink(missing_ok=True)

    # When
    pids = asyncio.run(_exercise_taskgroup_cancellation(markers, ready_path))

    # Then
    assert len(pids) == 2
    for pid in pids:
        _assert_pid_absent(pid)


def _readiness_server(path: Path, backlog: int) -> socket.socket:
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(path))
    server.listen(backlog)
    server.setblocking(False)
    return server


async def _limited_worker(
    marker: Path,
    ready_path: Path,
    semaphore: asyncio.BoundedSemaphore,
    cancelled: asyncio.Event,
) -> process_supervisor.ProcessResult:
    async with semaphore:
        return await process_supervisor.run_bounded(
            [
                sys.executable,
                str(FIXTURE),
                "child",
                str(marker),
                "close",
                "normal",
                "socket",
                str(ready_path),
            ],
            timeout_seconds=10,
            cleanup_seconds=1,
            output_limit_bytes=1024,
            env=_environment(),
            cancel_event=cancelled,
        )


async def _exercise_limited_workers(
    markers: list[Path], ready_path: Path
) -> tuple[list[process_supervisor.ProcessResult], list[int]]:
    server = _readiness_server(ready_path, 4)
    semaphore = asyncio.BoundedSemaphore(2)
    cancelled = asyncio.Event()
    tasks = [
        asyncio.create_task(_limited_worker(marker, ready_path, semaphore, cancelled))
        for marker in markers
    ]
    active_pids: list[int] = []
    try:
        for _ in range(2):
            active_pids.append(await _accept_pid(server))
        assert all(markers[index].exists() for index in range(2))
        assert not markers[2].exists()
        cancelled.set()
        results = await asyncio.wait_for(asyncio.gather(*tasks), 5)
        return results, active_pids
    finally:
        cancelled.set()
        await asyncio.wait(tasks, timeout=3)
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.wait(tasks, timeout=3)
        server.close()
        ready_path.unlink(missing_ok=True)


def test_shared_cancellation_respects_caller_concurrency_limit(
    tmp_path: Path,
    socket_directory: Path,
    cleanup_children: Callable[[Path], None],
) -> None:
    """Start only semaphore capacity before shared cancellation releases work."""
    # Given
    markers = [tmp_path / f"capacity-{index}" for index in range(3)]
    ready_path = socket_directory / "c.sock"
    ready_path.unlink(missing_ok=True)
    for marker in markers:
        cleanup_children(marker)

    # When
    results, active_pids = asyncio.run(_exercise_limited_workers(markers, ready_path))

    # Then
    assert len(results) == 3
    assert all(result.stop_reason == "cancelled" for result in results)
    assert all(result.cleanup_complete for result in results)
    assert len(active_pids) == 2
    assert not markers[2].exists()
    for pid in active_pids:
        _assert_pid_absent(pid)


async def _repeated_cancellation_case(
    marker: Path,
    ready_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> int:
    server = _readiness_server(ready_path, 1)
    loop = asyncio.get_running_loop()
    original_killpg = os.killpg
    task: asyncio.Task[process_supervisor.ProcessResult] | None = None

    def cancel_during_term(pgid: int, signum: int) -> None:
        if signum == signal.SIGTERM and task is not None:
            loop.call_soon(task.cancel, "second cancellation")
            loop.call_soon(task.cancel, "third cancellation")
        original_killpg(pgid, signum)

    monkeypatch.setattr(process_supervisor.os, "killpg", cancel_during_term)
    task = asyncio.create_task(
        process_supervisor.run_bounded(
            [
                sys.executable,
                str(FIXTURE),
                "child",
                str(marker),
                "close",
                "resist",
                "socket",
                str(ready_path),
            ],
            timeout_seconds=10,
            cleanup_seconds=1,
            output_limit_bytes=1024,
            env=_environment(),
        )
    )
    try:
        pid = await _accept_pid(server)
        task.cancel("first cancellation")
        with pytest.raises(asyncio.CancelledError) as caught:
            await asyncio.wait_for(task, 4)
        assert vars(caught.value)["cleanup_complete"] is True
        assert vars(caught.value)["cleanup_observation"] == "group_absent"
        return pid
    finally:
        if not task.done():
            task.cancel()
            await asyncio.wait({task}, timeout=3)
        server.close()
        ready_path.unlink(missing_ok=True)


def test_repeated_task_cancellation_waits_for_owned_cleanup(
    tmp_path: Path,
    socket_directory: Path,
    cleanup_children: Callable[[Path], None],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Re-raise the first cancellation only after shielded cleanup completes."""
    marker = tmp_path / "repeated-cancel"
    ready_path = socket_directory / "r.sock"
    ready_path.unlink(missing_ok=True)

    # Given
    cleanup_children(marker)

    # When
    pid = asyncio.run(_repeated_cancellation_case(marker, ready_path, monkeypatch))

    # Then
    _assert_pid_absent(pid)


async def _cancel_during_spawn(marker: Path, monkeypatch: pytest.MonkeyPatch) -> int:
    entered_spawn = asyncio.Event()
    release_spawn = asyncio.Event()
    group_verified = asyncio.Event()
    loop = asyncio.get_running_loop()
    original_spawn = loop.subprocess_exec
    pids: list[int] = []

    async def delayed_spawn(
        protocol_factory: Callable[[], asyncio.SubprocessProtocol],
        program: str,
        *args: str,
        stdin: int | None = None,
        stdout: int | None = None,
        stderr: int | None = None,
        cwd: str | bytes | os.PathLike[str] | os.PathLike[bytes] | None = None,
        env: dict[str, str] | None = None,
        start_new_session: bool = False,
    ) -> tuple[asyncio.SubprocessTransport, asyncio.SubprocessProtocol]:
        entered_spawn.set()
        await release_spawn.wait()
        return await original_spawn(
            protocol_factory,
            program,
            *args,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            cwd=cwd,
            env=env,
            start_new_session=start_new_session,
        )

    def observe_group(pid: int) -> int:
        pids.append(pid)
        group_verified.set()
        return os.getpgid(pid)

    monkeypatch.setattr(loop, "subprocess_exec", delayed_spawn)
    task = asyncio.create_task(
        process_supervisor.run_bounded(
            [sys.executable, str(FIXTURE), "child", str(marker), "close", "normal"],
            timeout_seconds=10,
            cleanup_seconds=1,
            output_limit_bytes=1024,
            env=_environment(),
            get_process_group_id=observe_group,
        )
    )
    try:
        await asyncio.wait_for(entered_spawn.wait(), 3)
        task.cancel()
        release_spawn.set()
        await asyncio.wait_for(group_verified.wait(), 3)
        await _expect_clean_cancellation(task)
        return pids[0]
    finally:
        release_spawn.set()
        await _recover_tasks([task])


async def _expect_clean_cancellation[T](
    task: asyncio.Task[T],
) -> asyncio.CancelledError:
    with pytest.raises(asyncio.CancelledError) as caught:
        await asyncio.wait_for(task, 4)
    assert vars(caught.value)["cleanup_complete"] is True
    assert vars(caught.value)["cleanup_observation"] == "group_absent"
    return caught.value


def test_cancellation_during_process_creation_keeps_late_handle(
    tmp_path: Path,
    cleanup_children: Callable[[Path], None],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Own a process whose async creation completes after caller cancellation."""
    marker = tmp_path / "late-handle"

    # Given
    cleanup_children(marker)

    # When
    pid = asyncio.run(_cancel_during_spawn(marker, monkeypatch))

    # Then
    _assert_pid_absent(pid)


@dataclass
class _DelayedSpawnFailure:
    entered: asyncio.Event
    release: asyncio.Event

    async def __call__(
        self,
        protocol_factory: Callable[[], asyncio.SubprocessProtocol],
        program: str,
        *args: str,
        stdin: int | None = None,
        stdout: int | None = None,
        stderr: int | None = None,
        cwd: str | bytes | os.PathLike[str] | os.PathLike[bytes] | None = None,
        env: dict[str, str] | None = None,
        start_new_session: bool = False,
    ) -> tuple[asyncio.SubprocessTransport, asyncio.SubprocessProtocol]:
        del protocol_factory, program, args, stdin, stdout, stderr, cwd, env
        del start_new_session
        self.entered.set()
        await self.release.wait()
        raise OSError("delayed spawn failure")


async def _exercise_delayed_spawn_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    loop = asyncio.get_running_loop()
    entered = asyncio.Event()
    release = asyncio.Event()
    monkeypatch.setattr(loop, "subprocess_exec", _DelayedSpawnFailure(entered, release))
    task = asyncio.create_task(
        process_supervisor.run_bounded(
            [sys.executable, str(FIXTURE), "burst"],
            timeout_seconds=3,
            cleanup_seconds=1,
            output_limit_bytes=32,
            env=_environment(),
        )
    )
    try:
        await asyncio.wait_for(entered.wait(), 2)
        task.cancel("caller cancellation")
        release.set()
        caught = await _expect_clean_cancellation(task)
        assert any("delayed spawn failure" in note for note in caught.__notes__)
    finally:
        release.set()
        await _recover_tasks([task])


def test_cancellation_remains_primary_when_delayed_creation_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A later spawn failure is diagnostic and cannot replace cancellation."""
    # Given

    # When
    asyncio.run(_exercise_delayed_spawn_failure(monkeypatch))

    # Then: the helper asserts the original cancellation and diagnostic order.


def test_output_error_remains_primary_when_cleanup_is_cancelled(
    tmp_path: Path,
    cleanup_children: Callable[[Path], None],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Late cancellation during TERM cleanup cannot replace an output error."""
    marker = tmp_path / "output-error-cancel"
    cleanup_children(marker)

    def fail_output(fd: int, data: bytes) -> None:
        raise OSError("primary output failure")

    original_killpg = os.killpg

    async def execute() -> None:
        loop = asyncio.get_running_loop()
        owner = asyncio.current_task()
        assert owner is not None

        def cancel_on_term(pgid: int, signum: signal.Signals) -> None:
            if signum == signal.SIGTERM:
                loop.call_soon(owner.cancel, "cleanup cancellation")
            original_killpg(pgid, signum)

        monkeypatch.setattr(process_supervisor.os, "killpg", cancel_on_term)
        await process_supervisor.run_bounded(
            [sys.executable, str(FIXTURE), "leader", "hold", str(marker), "0"],
            timeout_seconds=3,
            cleanup_seconds=1,
            output_limit_bytes=1024,
            env=_environment(),
            on_data=fail_output,
        )

    # When
    with pytest.raises(OSError, match="primary output failure") as caught:
        asyncio.run(execute())

    # Then
    assert vars(caught.value)["cleanup_complete"] is True
    assert any("additional cancellation" in note for note in caught.value.__notes__)
    _assert_pid_absent(int(marker.read_text(encoding="utf-8")))


def test_stdin_is_closed_when_no_input_contract_is_declared() -> None:
    """Do not inherit the test runner's input stream implicitly."""
    # Given

    # When
    result = run_bounded_sync(
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

    monkeypatch.setattr(asyncio.BaseEventLoop, "subprocess_exec", refuse_launch)

    # When / Then
    with pytest.raises(ValueError, match=message):
        run_bounded_sync(
            [sys.executable, str(FIXTURE), "burst"],
            timeout_seconds=timeout,
            cleanup_seconds=cleanup,
            output_limit_bytes=cast(int, output),
            env=_environment(),
        )


@pytest.mark.parametrize("signum", [signal.SIGINT, signal.SIGTERM])
def test_signal_cancellation_cleans_descendant_and_restores_handler(
    tmp_path: Path,
    socket_directory: Path,
    cleanup_children: Callable[[Path], None],
    signum: signal.Signals,
) -> None:
    """Handle real SIGTERM at the owner boundary and restore its prior handler."""
    # Given
    marker = tmp_path / "signal-child"
    ready_path = socket_directory / "s.sock"
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

    def read_then_fail(fd: int, data: bytes) -> None:
        nonlocal reads
        reads += 1
        if reads == 1:
            return
        raise OSError("primary read failure")

    def deny_group_signal(pgid: int, signum: int) -> None:
        raise PermissionError(1, "operation denied", pgid)

    monkeypatch.setattr(process_supervisor.os, "killpg", deny_group_signal)

    # When
    with pytest.raises(OSError, match="primary read failure") as caught:
        run_bounded_sync(
            [sys.executable, str(FIXTURE), "leader", "hold", str(marker), "0"],
            timeout_seconds=3,
            cleanup_seconds=0.2,
            output_limit_bytes=1024,
            env=_environment(),
            on_data=read_then_fail,
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

    def interrupt_read(fd: int, data: bytes) -> None:
        raise KeyboardInterrupt("injected cancellation")

    # When
    with pytest.raises(KeyboardInterrupt, match="injected cancellation") as caught:
        run_bounded_sync(
            [sys.executable, str(FIXTURE), "leader", "hold", str(marker), "0"],
            timeout_seconds=3,
            cleanup_seconds=1,
            output_limit_bytes=1024,
            env=_environment(),
            on_data=interrupt_read,
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
        run_bounded_sync(
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
    result = run_bounded_sync(
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
