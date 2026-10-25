# SPDX-License-Identifier: Apache-2.0
"""Disposable real-process regressions for native supervisor behavior."""

import asyncio
from asyncio.transports import ReadTransport
from collections.abc import Callable, Coroutine
from contextlib import suppress
from dataclasses import replace
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
from time import monotonic
from time import sleep as time_sleep
from typing import Any, cast, override

import pytest

import script.process_supervisor as process_supervisor
from script.process_supervisor import (
    AttemptCancelled,
    AttemptRequest,
    AttemptResult,
    CleanupOutcome,
    Clock,
    Completed,
    NativeProcessEffects,
    NotLaunched,
    OutputLimitExceeded,
    ProcessHandle,
    TimedOut,
    failure_evidence,
    run_attempt,
)

FIXTURE = Path(__file__).parents[1] / "fixtures" / "process_supervisor_child.py"
CALLER_FIXTURE = Path(__file__).parents[1] / "fixtures" / "process_supervisor_caller.py"


def request(
    tmp_path: Path, cap: int, *args: str, timeout: float = 3.0, grace: float = 0.0
) -> AttemptRequest:
    """Build a bounded request for the disposable CLI fixture."""
    return AttemptRequest(
        (sys.executable, str(FIXTURE), *args),
        tmp_path,
        timeout,
        2.0,
        cap,
        "devnull",
        grace,
    )


def capture_subprocesses(
    monkeypatch: pytest.MonkeyPatch,
) -> list[asyncio.subprocess.Process]:
    """Observe actual asyncio-owned children through its acquisition boundary."""
    created: list[asyncio.subprocess.Process] = []
    original_create = asyncio.create_subprocess_exec

    async def record_create(*args: Any, **kwargs: Any) -> asyncio.subprocess.Process:
        process = await original_create(*args, **kwargs)
        created.append(process)
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", record_create)
    return created


@pytest.mark.parametrize(
    ("term_mode", "burst_stream"),
    [
        pytest.param("burst", "stdout", id="cooperative-stdout-drain"),
        pytest.param("burst", "stderr", id="cooperative-stderr-drain"),
        pytest.param("ignore", "stdout", id="ignored-term"),
    ],
)
def test_positive_grace_escalates_and_freezes_captured_prefix(
    tmp_path: Path, term_mode: str, burst_stream: str
) -> None:
    """TERM is honored or escalated, while cleanup drains without retaining."""
    # Given: a long-running child and a bounded output prefix.
    marker = tmp_path / "term-handler-finished"
    attempt = request(
        tmp_path,
        8,
        "sleep",
        "--term-mode",
        term_mode,
        "--term-burst-stream",
        burst_stream,
        "--term-marker",
        str(marker),
        grace=0.25,
    )

    # When
    result = asyncio.run(run_attempt(attempt))

    # Then
    assert isinstance(result, TimedOut)
    assert result.observation.output == process_supervisor.CapturedOutput(b"", b"")
    assert marker.exists() is (term_mode == "burst")
    assert tuple(item.signal for item in result.observation.cleanup.signals) == (
        "SIGTERM",
        "SIGKILL",
    )
    assert result.observation.cleanup.signals[0].outcome == "sent"
    assert result.observation.cleanup.signals[1].outcome in {"sent", "no_target"}
    assert result.observation.cleanup.direct_wait == "reaped"


def test_eof_during_grace_does_not_shorten_term_wait(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given: TERM closes both output streams but leaves the child alive.
    ready = tmp_path / "ready"
    marker = tmp_path / "term-received"
    attempt = request(
        tmp_path,
        0,
        "sleep",
        "--term-mode",
        "close-streams",
        "--ready-file",
        str(ready),
        "--term-marker",
        str(marker),
        timeout=1.0,
        grace=0.35,
    )
    real_killpg = os.killpg
    signal_times: list[tuple[signal.Signals, float]] = []

    def observe_signals(pgid: int, sig: signal.Signals) -> None:
        signal_times.append((sig, monotonic()))
        real_killpg(pgid, sig)

    monkeypatch.setattr(process_supervisor.os, "killpg", observe_signals)

    # When
    result = asyncio.run(run_attempt(attempt))

    # Then
    assert ready.exists() and marker.exists()
    assert isinstance(result, TimedOut)
    assert tuple(sig.name for sig, _ in signal_times) == ("SIGTERM", "SIGKILL")
    assert signal_times[1][1] - signal_times[0][1] >= 0.30
    assert result.observation.cleanup.direct_wait == "reaped"


def test_grace_expiry_retrieves_all_reader_failures(tmp_path: Path) -> None:
    # Given: an ignored TERM and a loop handler observing unhandled failures.
    attempt = request(
        tmp_path,
        100,
        "sleep",
        "--term-mode",
        "ignore",
        timeout=0.1,
        grace=0.2,
    )
    loop_contexts: list[dict[str, object]] = []

    async def run_with_exception_handler() -> TimedOut:
        loop = asyncio.get_running_loop()
        loop.set_exception_handler(lambda _loop, context: loop_contexts.append(context))

        # When
        result = await run_attempt(attempt)
        await asyncio.sleep(0)
        assert isinstance(result, TimedOut)
        return result

    # When
    result = asyncio.run(run_with_exception_handler())

    # Then
    assert isinstance(result, TimedOut)
    assert tuple(item.signal for item in result.observation.cleanup.signals) == (
        "SIGTERM",
        "SIGKILL",
    )
    assert result.observation.cleanup.direct_wait == "reaped"
    assert not any(
        context.get("message") == "_GatheringFuture exception was never retrieved"
        for context in loop_contexts
    )


class OffsetClock:
    def __init__(self, offset_seconds: float = -1_000.0) -> None:
        self.offset_seconds = offset_seconds

    def monotonic(self) -> float:
        return monotonic() + self.offset_seconds


class ClockAdvancingNativeEffects(NativeProcessEffects):
    def __init__(self, clock: OffsetClock) -> None:
        self.clock = clock

    @override
    async def acquire(self, attempt: AttemptRequest, /) -> ProcessHandle | NotLaunched:
        acquired = await super().acquire(attempt)
        if not isinstance(acquired, NotLaunched):
            self.clock.offset_seconds += attempt.timeout_seconds + 1.0
        return acquired


def _caller_environment(repository_root: Path) -> dict[str, str]:
    environment = dict(os.environ)
    inherited_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = os.pathsep.join(
        [str(repository_root)]
        if inherited_pythonpath is None
        else [str(repository_root), inherited_pythonpath]
    )
    return environment


def _send_signal_when_ready(
    process: subprocess.Popen[bytes], signal_to_send: signal.Signals
) -> None:
    assert process.stdout is not None
    deadline = monotonic() + 6.0
    ready_line = bytearray()
    while not ready_line.endswith(b"\n"):
        remaining = deadline - monotonic()
        if remaining <= 0:
            raise TimeoutError("representative caller did not become active")
        no_files: tuple[int, ...] = ()
        readable, _, _ = select.select([process.stdout], no_files, no_files, remaining)
        if not readable:
            raise TimeoutError("representative caller readiness line expired")
        byte = os.read(process.stdout.fileno(), 1)
        if not byte:
            raise EOFError("representative caller exited before readiness")
        ready_line.extend(byte)
    assert bytes(ready_line).strip() == b"READY"
    process.send_signal(signal_to_send)


def _collect_caller_report(process: subprocess.Popen[bytes]) -> dict[str, object]:
    stdout, stderr = process.communicate(timeout=8.0)
    assert process.returncode == 0, stderr.decode(errors="replace")
    result = json.loads(stdout.decode().splitlines()[-1])
    assert isinstance(result, dict)
    return result


def _emergency_stop_caller(process: subprocess.Popen[bytes], ready_file: Path) -> None:
    cleanup_error: BaseException | None = None
    try:
        stop_and_reap_caller(process)
    except BaseException as error:
        cleanup_error = error
    finally:
        kill_known_child_group(ready_file)
    if cleanup_error is not None:
        raise RuntimeError(
            "could not reap representative caller within bounds"
        ) from cleanup_error


def stop_and_reap_caller(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    process.send_signal(signal.SIGTERM)
    try:
        process.communicate(timeout=2.0)
    except subprocess.TimeoutExpired:
        process.kill()
        collect_killed_caller(process)


def collect_killed_caller(process: subprocess.Popen[bytes]) -> None:
    try:
        process.communicate(timeout=2.0)
    except subprocess.TimeoutExpired as error:
        raise TimeoutError("representative caller did not reap after kill") from error


def kill_known_child_group(ready_file: Path) -> None:
    if not ready_file.exists():
        return
    try:
        child_pid = int(ready_file.read_text(encoding="utf-8"))
        os.killpg(child_pid, signal.SIGKILL)
    except ProcessLookupError:
        return


def run_representative_caller(
    tmp_path: Path,
    *arguments: str,
    signal_to_send: signal.Signals | None = None,
) -> dict[str, object]:
    """Run the caller fixture and contain its known child on failures."""
    ready_file = tmp_path / "caller-ready"
    command = [sys.executable, str(CALLER_FIXTURE), *arguments]
    for option, path in (("--workdir", tmp_path), ("--ready-file", ready_file)):
        command.extend((option, str(path)))
    process = subprocess.Popen(
        command,
        cwd=tmp_path,
        env=_caller_environment(Path(__file__).parents[3]),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        if signal_to_send is not None:
            _send_signal_when_ready(process, signal_to_send)
        result = _collect_caller_report(process)
    except BaseException:
        _emergency_stop_caller(process, ready_file)
        raise
    return result


def test_completion_preserves_actual_exit_and_distinct_streams(
    tmp_path: Path,
) -> None:
    # Given
    attempt = request(
        tmp_path,
        100,
        "emit",
        "--stdout",
        "6f6b0a",
        "--stderr",
        "7761726e696e670a",
    )

    # When
    result = asyncio.run(run_attempt(attempt))

    # Then
    assert isinstance(result, Completed)
    assert result.exit_status == 0
    assert result.observation.output is not None
    assert result.observation.output.stdout == b"ok\n"
    assert result.observation.output.stderr == b"warning\n"
    assert tuple(item.signal for item in result.observation.cleanup.signals) == (
        "SIGKILL",
    )
    assert result.observation.cleanup.signals[0].outcome in {"sent", "no_target"}
    assert result.observation.cleanup.direct_wait == "reaped"


def test_nonzero_completion_preserves_status_and_output(tmp_path: Path) -> None:
    # Given
    attempt = request(
        tmp_path, 100, "emit", "--stdout", "7061727469616c0a", "--status", "7"
    )

    # When
    result = asyncio.run(run_attempt(attempt))

    # Then
    assert isinstance(result, Completed)
    assert result.exit_status == 7
    assert result.observation.output is not None
    assert result.observation.output.stdout == b"partial\n"


@pytest.mark.parametrize(
    "effects",
    [
        pytest.param(None, id="default-native"),
        pytest.param(NativeProcessEffects(), id="explicit-native"),
    ],
)
def test_native_capture_uses_run_attempt_clock_domain(
    tmp_path: Path, effects: NativeProcessEffects | None
) -> None:
    # Given
    attempt = request(tmp_path, 100, "emit", "--stdout", "6f6b0a")
    clock = OffsetClock()

    # When
    result = asyncio.run(run_attempt(attempt, effects, clock))

    # Then
    assert isinstance(result, Completed)
    assert result.observation.output is not None
    assert result.observation.output.stdout == b"ok\n"


def test_native_capture_keeps_acquisition_inside_execution_timeout(
    tmp_path: Path,
) -> None:
    # Given
    attempt = request(tmp_path, 100, "sleep")
    clock = OffsetClock()
    effects = ClockAdvancingNativeEffects(clock)

    # When
    result = asyncio.run(run_attempt(attempt, effects, clock))

    # Then
    assert isinstance(result, TimedOut)
    assert result.observation.elapsed_seconds is not None
    assert result.observation.elapsed_seconds >= attempt.timeout_seconds


@pytest.mark.parametrize(
    ("stdout", "stderr", "cap", "expected_type"),
    [
        pytest.param("31323334", "35363738", 8, Completed, id="exact-cap"),
        pytest.param("3132333435", "36373839", 8, OutputLimitExceeded, id="overflow"),
    ],
)
def test_combined_cap_and_overflow(
    tmp_path: Path,
    stdout: str,
    stderr: str,
    cap: int,
    expected_type: type[Completed] | type[OutputLimitExceeded],
) -> None:
    # Given
    attempt = request(tmp_path, cap, "emit", "--stdout", stdout, "--stderr", stderr)
    expected_stdout = bytes.fromhex(stdout)
    expected_stderr = bytes.fromhex(stderr)

    # When
    result = asyncio.run(run_attempt(attempt))

    # Then
    assert isinstance(result, expected_type)
    assert result.observation.output is not None
    captured = result.observation.output
    assert expected_stdout.startswith(captured.stdout)
    assert expected_stderr.startswith(captured.stderr)
    total = len(captured.stdout) + len(captured.stderr)
    if expected_type is Completed:
        assert captured.stdout == expected_stdout
        assert captured.stderr == expected_stderr
        assert total == cap
    else:
        assert total == cap


def test_overflow_kills_live_process_and_closes_output_pipes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given
    attempt = request(tmp_path, 1, "emit", "--burst-bytes", "200000", timeout=3.0)

    # When
    result = asyncio.run(_run_overflow_after_backpressure(attempt, monkeypatch))

    # Then
    assert isinstance(result, OutputLimitExceeded)
    assert result.exit_status == -int(signal.SIGKILL)
    assert result.observation.output == process_supervisor.CapturedOutput(b"p", b"")
    assert result.observation.cleanup.signals[-1].outcome == "sent"
    assert result.observation.cleanup.direct_wait == "reaped"


async def _run_overflow_after_backpressure(
    attempt: AttemptRequest, monkeypatch: pytest.MonkeyPatch
) -> AttemptResult:
    """Run capture only after the real child has backlogged and paused stdout."""
    create_subprocess_exec = asyncio.create_subprocess_exec
    acquired: asyncio.subprocess.Process | None = None

    async def acquire_after_backpressure(
        *args: str, **kwargs: Any
    ) -> asyncio.subprocess.Process:
        nonlocal acquired
        acquired = await create_subprocess_exec(*args, **kwargs)
        await _wait_for_stdout_backpressure(acquired)
        assert acquired.returncode is None
        return acquired

    monkeypatch.setattr(asyncio, "create_subprocess_exec", acquire_after_backpressure)
    try:
        result = await run_attempt(attempt)
        assert acquired is not None
        stdout_pipe, stderr_pipe = _process_output_pipes(acquired)
        assert stdout_pipe.is_closing()
        assert stderr_pipe.is_closing()
        return result
    finally:
        if acquired is not None:
            await _emergency_stop_process(acquired)


async def _wait_for_stdout_backpressure(process: asyncio.subprocess.Process) -> None:
    stdout_pipe, _ = _process_output_pipes(process)
    deadline = asyncio.get_running_loop().time() + 2.0
    while stdout_pipe.is_reading():
        if asyncio.get_running_loop().time() >= deadline:
            raise TimeoutError("noisy child did not pause its stdout pipe")
        await asyncio.sleep(0)


def _process_output_pipes(
    process: asyncio.subprocess.Process,
) -> tuple[ReadTransport, ReadTransport]:
    transport = cast(asyncio.SubprocessTransport, vars(process)["_transport"])
    stdout_pipe = transport.get_pipe_transport(1)
    stderr_pipe = transport.get_pipe_transport(2)
    assert stdout_pipe is not None and stderr_pipe is not None
    return cast(ReadTransport, stdout_pipe), cast(ReadTransport, stderr_pipe)


async def _emergency_stop_process(process: asyncio.subprocess.Process) -> None:
    for pipe in _process_output_pipes(process):
        pipe.close()
    if process.returncode is not None:
        return
    with suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGKILL)
    with suppress(TimeoutError):
        await asyncio.wait_for(process.wait(), timeout=2.0)


def test_zero_cap_retains_unbounded_separate_streams(tmp_path: Path) -> None:
    # Given
    attempt = request(
        tmp_path,
        0,
        "emit",
        "--stdout",
        "7374646f75740a",
        "--stderr",
        "7374646572720a",
    )

    # When
    result = asyncio.run(run_attempt(attempt))

    # Then
    assert isinstance(result, Completed)
    assert result.observation.output is not None
    assert result.observation.output.stdout == b"stdout\n"
    assert result.observation.output.stderr == b"stderr\n"


@pytest.mark.parametrize("cap", [6, 0])
@pytest.mark.parametrize("grace", [0.0, 0.2], ids=["immediate-kill", "term-grace-kill"])
def test_timeout_when_exited_leader_child_holds_output_pipe(
    tmp_path: Path, cap: int, grace: float
) -> None:
    # Given
    leader_file = tmp_path / "leader.pid"
    grandchild_file = tmp_path / "grandchild.pid"
    grandchild_ready = tmp_path / "grandchild.ready"
    attempt = request(
        tmp_path,
        cap,
        "hold-pipe",
        "--stdout",
        "7365656e0a",
        "--ready-file",
        str(leader_file),
        "--grandchild-file",
        str(grandchild_file),
        "--grandchild-ready",
        str(grandchild_ready),
        timeout=2.0,
        grace=grace,
    )
    effects = _ObservePipeHolder(grandchild_file)

    # When
    grandchild_stopped_after_cleanup = False
    try:
        result = asyncio.run(run_attempt(attempt, effects))
        grandchild_pid = int(grandchild_file.read_text(encoding="utf-8"))
        grandchild_stopped_after_cleanup = _wait_for_process_stop(grandchild_pid)
    finally:
        _emergency_stop_fixture_group(leader_file, grandchild_file)

    # Then
    assert isinstance(result, TimedOut)
    assert result.exit_status == 0
    assert result.observation.output is not None
    assert result.observation.output.stdout == b"seen\n"
    expected_signals = ("SIGTERM", "SIGKILL") if grace else ("SIGKILL",)
    assert (
        tuple(item.signal for item in result.observation.cleanup.signals)
        == expected_signals
    )
    assert result.observation.cleanup.direct_wait == "reaped"
    assert effects.grandchild_was_running_at_cleanup
    assert grandchild_stopped_after_cleanup


class _ObservePipeHolder(NativeProcessEffects):
    def __init__(self, grandchild_file: Path) -> None:
        self.grandchild_file = grandchild_file
        self.grandchild_was_running_at_cleanup = False

    @override
    async def cleanup(
        self,
        handle: ProcessHandle,
        timeout_seconds: float,
        grace_seconds: float,
        /,
    ) -> CleanupOutcome:
        grandchild_pid = int(self.grandchild_file.read_text(encoding="utf-8"))
        self.grandchild_was_running_at_cleanup = _process_state(grandchild_pid) not in {
            None,
            "Z",
        }
        return await super().cleanup(handle, timeout_seconds, grace_seconds)


def _process_state(pid: int) -> str | None:
    result = subprocess.run(
        ["ps", "-o", "stat=", "-p", str(pid)],
        capture_output=True,
        check=False,
        text=True,
        timeout=1.0,
    )
    if result.returncode == 1 and not result.stdout.strip() and not result.stderr:
        return None
    assert result.returncode == 0, result.stderr
    state = result.stdout.strip()
    return state[0] if state else None


def _wait_for_process_stop(pid: int) -> bool:
    deadline = monotonic() + 3.0
    while True:
        state = _process_state(pid)
        if state is None or state == "Z":
            return True
        if monotonic() >= deadline:
            return False
        time_sleep(0.05)


def _emergency_stop_fixture_group(leader_file: Path, grandchild_file: Path) -> None:
    if not leader_file.exists():
        return
    process_group_id = int(leader_file.read_text(encoding="utf-8"))
    with suppress(ProcessLookupError):
        os.killpg(process_group_id, signal.SIGKILL)
    if grandchild_file.exists():
        assert _wait_for_process_stop(int(grandchild_file.read_text(encoding="utf-8")))


@pytest.mark.parametrize(
    ("cap", "burst_bytes"),
    [
        pytest.param(0, 200_000, id="zero-cap"),
        pytest.param(2_000_000, 200_000, id="capped"),
    ],
)
def test_repeated_cancellation_retains_observed_partial_output(
    tmp_path: Path, cap: int, burst_bytes: int
) -> None:
    # Given
    ready = tmp_path / "started"
    attempt = request(
        tmp_path,
        cap,
        "sleep",
        "--ready-file",
        str(ready),
        "--burst-bytes",
        str(burst_bytes),
    )

    # When
    error = asyncio.run(_cancel_twice_after_ready(attempt, ready))

    # Then
    assert error.observation.output is not None
    assert error.observation.output.stdout.startswith(b"partial\n")
    assert len(error.observation.output.stdout) > 0
    if cap:
        assert len(error.observation.output.stdout) <= cap
    assert error.observation.cleanup.signals[-1].outcome == "sent"
    assert error.observation.cleanup.direct_wait == "reaped"


async def _cancel_twice_after_ready(
    attempt: AttemptRequest, ready: Path
) -> AttemptCancelled:
    """Cancel after the fixture's backpressure handshake and await cleanup."""
    task = asyncio.create_task(run_attempt(attempt))
    try:
        deadline = monotonic() + 3.0
        while not ready.exists() and monotonic() < deadline:
            await asyncio.sleep(0.005)
        assert ready.exists(), "child did not reach its ready handshake"
        await asyncio.sleep(0)
        task.cancel()
        asyncio.get_running_loop().call_soon(task.cancel)
        with pytest.raises(AttemptCancelled) as raised:
            await task
        return raised.value
    finally:
        if not task.done():
            task.cancel()
            with suppress(BaseException):
                await task


def test_cancellation_propagates_after_bounded_cleanup(tmp_path: Path) -> None:
    # Given
    attempt = request(tmp_path, 0, "sleep")

    async def cancel_active_attempt() -> AttemptCancelled:
        task = asyncio.create_task(run_attempt(attempt))
        try:
            await asyncio.sleep(0)

            # When
            task.cancel()
            with pytest.raises(AttemptCancelled) as raised:
                await task
            return raised.value
        finally:
            if not task.done():
                task.cancel()
                with suppress(BaseException):
                    await task

    error = asyncio.run(cancel_active_attempt())

    # Then
    assert error.observation.cleanup.dispatch_permitted


def test_signal_exit_status_is_retained(tmp_path: Path) -> None:
    # Given
    attempt = request(tmp_path, 100, "sleep", timeout=0.2)

    # When
    result = asyncio.run(run_attempt(attempt))

    # Then
    assert isinstance(result, TimedOut)
    assert result.exit_status == -signal.SIGKILL
    assert result.observation.cleanup.signals[-1].outcome == "sent"
    assert result.observation.cleanup.direct_wait == "reaped"


class CleanupWaitExpiryAfterExit:
    """Observe the cleanup wait status, then force its deadline to expire."""

    def __init__(self) -> None:
        self.original_wait = asyncio.subprocess.Process.wait
        self.calls = 0
        self.cleanup_status: int | None = None

    async def wait(self, process: asyncio.subprocess.Process) -> int:
        self.calls += 1
        status = await self.original_wait(process)
        if self.calls == 2:
            self.cleanup_status = status
            await asyncio.Event().wait()
        return status


def test_expired_cleanup_wait_retains_observed_post_kill_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given
    attempt = replace(
        request(tmp_path, 100, "sleep", timeout=0.2), cleanup_timeout_seconds=0.1
    )
    seam = CleanupWaitExpiryAfterExit()

    async def wait_with_cleanup_expiry(
        process: asyncio.subprocess.Process,
    ) -> int:
        return await seam.wait(process)

    monkeypatch.setattr(asyncio.subprocess.Process, "wait", wait_with_cleanup_expiry)

    # When
    result = asyncio.run(run_attempt(attempt))

    # Then
    assert isinstance(result, TimedOut)
    assert result.exit_status == -signal.SIGKILL
    assert seam.cleanup_status == -signal.SIGKILL
    assert result.observation.cleanup.direct_wait == "expired"
    assert result.observation.cleanup.wait_diagnostic == "direct-child wait expired"
    assert not result.observation.cleanup.dispatch_permitted


@pytest.mark.parametrize("wait_fault", ["expiry", "failure"])
def test_direct_wait_fault_remains_explicit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, wait_fault: str
) -> None:
    # Given
    attempt = request(tmp_path, 100, "emit")

    async def force_wait_fault(
        awaitable: Coroutine[Any, Any, int], timeout: float
    ) -> int:
        await asyncio.sleep(0)
        awaitable.close()
        if wait_fault == "expiry":
            raise TimeoutError("test direct wait expiry")
        raise OSError("test direct wait failure")

    monkeypatch.setattr(process_supervisor.asyncio, "wait_for", force_wait_fault)

    # When
    result = asyncio.run(run_attempt(attempt))

    # Then
    assert isinstance(result, Completed)
    assert result.observation.cleanup.direct_wait == (
        "expired" if wait_fault == "expiry" else "failed"
    )
    assert result.observation.cleanup.wait_diagnostic == (
        "direct-child wait expired"
        if wait_fault == "expiry"
        else "OSError: test direct wait failure"
    )
    assert not result.observation.cleanup.dispatch_permitted


class CaptureErrorCancellationSeam:
    """Inject a real stream error and owner cancellation at asyncio edges."""

    def __init__(self) -> None:
        self.error = RuntimeError("capture diagnostic to retain")
        self.owner_task: asyncio.Task[AttemptResult] | None = None
        self.owner_cancelled = False
        self.original_wait: Callable[
            [asyncio.subprocess.Process], Coroutine[Any, Any, int]
        ] = asyncio.subprocess.Process.wait

    async def fail_read(self, _stream: asyncio.StreamReader, _size: int = -1) -> bytes:
        await asyncio.sleep(0)
        raise self.error

    async def cancel_owner_when_wait_is_drained(
        self, process: asyncio.subprocess.Process
    ) -> int:
        try:
            return await self.original_wait(process)
        finally:
            current = asyncio.current_task()
            if (
                not self.owner_cancelled
                and current is not None
                and current.cancelling()
            ):
                self.owner_cancelled = True
                assert self.owner_task is not None
                self.owner_task.cancel()

    async def run(self, attempt: AttemptRequest) -> AttemptCancelled:
        self.owner_task = asyncio.create_task(run_attempt(attempt))
        try:
            with pytest.raises(AttemptCancelled) as raised:
                await self.owner_task
            return raised.value
        finally:
            if not self.owner_task.done():
                self.owner_task.cancel()
                with suppress(BaseException):
                    await self.owner_task


def test_capture_error_survives_cancellation_during_reader_settlement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given
    attempt = request(tmp_path, 0, "sleep")
    seam = CaptureErrorCancellationSeam()

    async def cancel_owner_when_wait_is_drained(
        process: asyncio.subprocess.Process,
    ) -> int:
        return await seam.cancel_owner_when_wait_is_drained(process)

    async def fail_stream_read(stream: asyncio.StreamReader, size: int = -1) -> bytes:
        return await seam.fail_read(stream, size)

    monkeypatch.setattr(asyncio.StreamReader, "read", fail_stream_read)
    monkeypatch.setattr(
        asyncio.subprocess.Process, "wait", cancel_owner_when_wait_is_drained
    )

    # When
    error = asyncio.run(seam.run(attempt))

    # Then
    assert seam.owner_cancelled
    assert error.__cause__ is seam.error
    assert vars(error)["process_supervisor_capture_error"] is seam.error
    assert any(
        note.startswith("Capture cancellation: CancelledError")
        for note in error.__notes__
    )
    assert error.observation.cleanup.signals[-1].outcome == "sent"
    assert error.observation.cleanup.direct_wait == "reaped"


def test_signal_failure_remains_explicit_and_stops_dispatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given
    attempt = request(tmp_path, 100, "emit")

    def deny_signal(_process_group_id: int, _signal: int) -> None:
        raise PermissionError("test denied group signal")

    monkeypatch.setattr(process_supervisor.os, "killpg", deny_signal)

    # When
    result = asyncio.run(run_attempt(attempt))

    # Then
    assert isinstance(result, Completed)
    assert result.observation.cleanup.signals[-1].outcome == "failed"
    assert result.observation.cleanup.signals[-1].diagnostic == (
        "PermissionError: test denied group signal"
    )
    assert result.observation.cleanup.direct_wait == "reaped"
    assert not result.observation.cleanup.dispatch_permitted


def _deny_selected_signal(
    monkeypatch: pytest.MonkeyPatch,
    failed_signal: signal.Signals,
    diagnostic: str,
) -> list[signal.Signals]:
    sent: list[signal.Signals] = []
    real_killpg = os.killpg

    def controlled_killpg(pgid: int, sig: signal.Signals) -> None:
        sent.append(sig)
        if sig == failed_signal:
            raise PermissionError(diagnostic)
        real_killpg(pgid, sig)

    monkeypatch.setattr(process_supervisor.os, "killpg", controlled_killpg)
    return sent


@pytest.mark.parametrize(
    ("failed_signal", "diagnostic"),
    [(signal.SIGTERM, "term denied"), (signal.SIGKILL, "kill denied")],
    ids=["term-failure-still-kills", "kill-failure-is-recorded"],
)
def test_grace_signal_failures_keep_ordered_diagnostics_and_stop_dispatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failed_signal: signal.Signals,
    diagnostic: str,
) -> None:
    # Given: a real child and one injected signal failure.
    attempt = request(tmp_path, 100, "sleep", timeout=0.1, grace=0.2)
    created = capture_subprocesses(monkeypatch)
    sent = _deny_selected_signal(monkeypatch, failed_signal, diagnostic)

    # When
    result = asyncio.run(run_attempt(attempt))

    # Then
    expected_names = ("SIGTERM", "SIGKILL")
    assert tuple(sig.name for sig in sent) == expected_names
    attempts = result.observation.cleanup.signals
    assert tuple(item.signal for item in attempts) == expected_names
    failed = 0 if failed_signal == signal.SIGTERM else 1
    assert attempts[failed].outcome == "failed"
    assert attempts[failed].diagnostic == f"PermissionError: {diagnostic}"
    assert result.observation.cleanup.direct_wait == "reaped"
    assert not result.observation.cleanup.dispatch_permitted
    assert len(created) == 1 and created[0].returncode is not None
    stdout_pipe, stderr_pipe = _process_output_pipes(created[0])
    assert stdout_pipe.is_closing() and stderr_pipe.is_closing()


def _inject_grace_reader_error(
    monkeypatch: pytest.MonkeyPatch, failure: OSError | TimeoutError
) -> Callable[[], bool]:
    term_attempted = False
    injected = False
    real_killpg = os.killpg

    def signal_and_observe(pgid: int, sig: signal.Signals) -> None:
        nonlocal term_attempted
        if sig == signal.SIGTERM:
            term_attempted = True
        real_killpg(pgid, sig)

    monkeypatch.setattr(process_supervisor.os, "killpg", signal_and_observe)
    original_read = asyncio.StreamReader.read

    async def fail_after_term(reader: asyncio.StreamReader, count: int = -1) -> bytes:
        nonlocal injected
        if term_attempted and not injected:
            injected = True
            raise failure
        return await original_read(reader, count)

    monkeypatch.setattr(asyncio.StreamReader, "read", fail_after_term)
    return lambda: injected


@pytest.mark.parametrize(
    "failure_type",
    [
        pytest.param(OSError, id="os-error"),
        pytest.param(TimeoutError, id="reader-timeout-error"),
    ],
)
def test_grace_read_failure_still_kills_closes_and_settles_child(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_type: type[OSError] | type[TimeoutError],
) -> None:
    # Given: a real child and a grace reader failure injected at asyncio's read.
    ready = tmp_path / "ready"
    marker = tmp_path / "term-received"
    created = capture_subprocesses(monkeypatch)
    failure = failure_type("injected grace stream read failure")
    injected = _inject_grace_reader_error(monkeypatch, failure)
    attempt = request(
        tmp_path,
        0,
        "sleep",
        "--term-mode",
        "close-streams",
        "--ready-file",
        str(ready),
        "--term-marker",
        str(marker),
        timeout=1.0,
        grace=0.25,
    )

    # When
    with pytest.raises(
        failure_type, match="injected grace stream read failure"
    ) as raised:
        asyncio.run(run_attempt(attempt))

    # Then
    assert ready.exists() and marker.exists()
    assert injected()
    assert raised.value is failure
    assert len(created) == 1 and created[0].returncode is not None
    stdout_pipe, stderr_pipe = _process_output_pipes(created[0])
    assert stdout_pipe.is_closing() and stderr_pipe.is_closing()
    evidence = failure_evidence(raised.value)
    assert evidence is not None
    assert tuple(item.signal for item in evidence.observation.cleanup.signals) == (
        "SIGTERM",
        "SIGKILL",
    )
    assert evidence.observation.cleanup.direct_wait == "reaped"


def test_term_no_target_skips_grace_and_still_records_kill(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given: capture completes before cleanup and TERM reports no target.
    attempt = request(tmp_path, 100, "emit", grace=0.8)
    sent: list[signal.Signals] = []
    term_attempted = False
    read_during_grace = False
    original_read = asyncio.StreamReader.read

    def no_targets(_pgid: int, sig: signal.Signals) -> None:
        nonlocal term_attempted
        sent.append(sig)
        if sig == signal.SIGTERM:
            term_attempted = True
        raise ProcessLookupError

    async def observe_read(reader: asyncio.StreamReader, count: int = -1) -> bytes:
        nonlocal read_during_grace
        if term_attempted:
            read_during_grace = True
        return await original_read(reader, count)

    monkeypatch.setattr(process_supervisor.os, "killpg", no_targets)
    monkeypatch.setattr(asyncio.StreamReader, "read", observe_read)

    # When
    result = asyncio.run(run_attempt(attempt))

    # Then
    assert tuple(sig.name for sig in sent) == ("SIGTERM", "SIGKILL")
    assert tuple(item.signal for item in result.observation.cleanup.signals) == (
        "SIGTERM",
        "SIGKILL",
    )
    assert all(
        item.outcome == "no_target" for item in result.observation.cleanup.signals
    )
    assert not read_during_grace


def test_cleanup_budget_expiry_still_attempts_final_kill(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given: a synchronous TERM boundary consumes the entire cleanup budget.
    attempt = replace(
        request(tmp_path, 100, "sleep", timeout=0.05, grace=0.09),
        cleanup_timeout_seconds=0.1,
    )
    sent: list[signal.Signals] = []
    real_killpg = os.killpg
    created = capture_subprocesses(monkeypatch)

    def signal_only(pgid: int, sig: signal.Signals) -> None:
        sent.append(sig)
        if sig == signal.SIGTERM:
            time_sleep(0.15)  # Consume the whole 0.1 second cleanup budget.
        if sig == signal.SIGKILL:
            real_killpg(pgid, sig)

    monkeypatch.setattr(process_supervisor.os, "killpg", signal_only)

    # When
    result = asyncio.run(run_attempt(attempt))

    # Then
    assert tuple(sig.name for sig in sent) == ("SIGTERM", "SIGKILL")
    assert tuple(item.signal for item in result.observation.cleanup.signals) == (
        "SIGTERM",
        "SIGKILL",
    )
    assert result.observation.cleanup.direct_wait == "expired"
    assert len(created) == 1
    stdout_pipe, stderr_pipe = _process_output_pipes(created[0])
    assert stdout_pipe.is_closing() and stderr_pipe.is_closing()


def test_repeated_owner_cancellation_during_grace_finishes_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given: a real child acknowledges TERM and remains alive through grace.
    ready = tmp_path / "ready"
    term_marker = tmp_path / "term-received"
    created = capture_subprocesses(monkeypatch)

    async def scenario() -> AttemptCancelled:
        attempt = request(
            tmp_path,
            0,
            "sleep",
            "--stdout",
            "7061727469616c0a",
            "--term-mode",
            "hold",
            "--ready-file",
            str(ready),
            "--term-marker",
            str(term_marker),
            timeout=0.5,
            grace=0.25,
        )
        task = asyncio.create_task(run_attempt(attempt))
        deadline = monotonic() + 3.0
        while not term_marker.exists() and monotonic() < deadline:
            await asyncio.sleep(0.005)
        assert ready.exists() and term_marker.exists()
        task.cancel("first owner cancellation")
        await asyncio.sleep(0)
        task.cancel("second owner cancellation")

        # When: cleanup remains owned despite the second cancellation.
        with pytest.raises(AttemptCancelled) as raised:
            await task
        return raised.value

    error = asyncio.run(scenario())

    # Then: evidence and the real process resources are settled before raise.
    assert isinstance(error.__cause__, asyncio.CancelledError)
    assert error.__cause__.args == ("first owner cancellation",)
    assert error.observation.output == process_supervisor.CapturedOutput(
        b"partial\n", b""
    )
    assert tuple(item.signal for item in error.observation.cleanup.signals) == (
        "SIGTERM",
        "SIGKILL",
    )
    assert error.observation.cleanup.direct_wait == "reaped"
    assert len(created) == 1 and created[0].returncode is not None
    stdout_pipe, stderr_pipe = _process_output_pipes(created[0])
    assert stdout_pipe.is_closing() and stderr_pipe.is_closing()


class DelayedNativeAcquisition:
    """Hold a real acquired child at the existing effects seam."""

    def __init__(self) -> None:
        self.native = NativeProcessEffects()
        self.acquired = asyncio.Event()
        self.release = asyncio.Event()
        self.settled = False

    async def acquire(self, attempt: AttemptRequest, /) -> ProcessHandle | NotLaunched:
        handle = await self.native.acquire(attempt)
        if isinstance(handle, NotLaunched):
            return handle
        self.acquired.set()
        await self.release.wait()
        self.settled = True
        return handle

    async def capture(
        self,
        handle: ProcessHandle,
        attempt: AttemptRequest,
        execution_deadline: float,
        clock: Clock,
        /,
    ) -> AttemptResult:
        return await self.native.capture(handle, attempt, execution_deadline, clock)

    async def cleanup(
        self, handle: ProcessHandle, timeout_seconds: float, grace_seconds: float, /
    ) -> CleanupOutcome:
        return await self.native.cleanup(handle, timeout_seconds, grace_seconds)


def test_cancelled_acquisition_settles_real_owned_child(tmp_path: Path) -> None:
    # Given
    attempt = request(tmp_path, 100, "sleep")
    effects = DelayedNativeAcquisition()

    async def cancel_during_acquisition() -> AttemptCancelled:
        task = asyncio.create_task(run_attempt(attempt, effects))
        try:
            await asyncio.wait_for(effects.acquired.wait(), timeout=3.0)

            # When
            task.cancel()
            effects.release.set()
            with pytest.raises(AttemptCancelled) as raised:
                await task
            return raised.value
        finally:
            effects.release.set()
            if not task.done():
                task.cancel()
                with suppress(BaseException):
                    await task

    error = asyncio.run(cancel_during_acquisition())

    # Then
    assert effects.settled
    assert error.observation.output is None
    assert error.observation.cleanup.signals[-1].outcome == "sent"
    assert error.observation.cleanup.direct_wait == "reaped"


def test_missing_executable_is_safe_known_empty_no_launch(tmp_path: Path) -> None:
    # Given
    attempt = replace(
        request(tmp_path, 100, "emit"),
        argv=("/missing/process-supervisor-cli",),
    )

    # When
    result = asyncio.run(run_attempt(attempt))

    # Then
    assert isinstance(result, process_supervisor.InfrastructureFailure)
    assert result.error_type == "FileNotFoundError"
    assert result.observation.output is not None
    assert result.observation.output.stdout == b""
    assert result.observation.output.stderr == b""
    assert result.observation.cleanup.dispatch_permitted


@pytest.mark.parametrize(
    ("trigger", "signal_to_send"),
    [
        pytest.param("SIGINT", signal.SIGINT, id="sigint-delivery"),
        pytest.param("SIGTERM", signal.SIGTERM, id="sigterm-delivery"),
        pytest.param("task-cancel", None, id="async-task-cancellation"),
    ],
)
def test_representative_caller_latches_stop_and_accounts_for_unstarted_calls(
    tmp_path: Path,
    trigger: str,
    signal_to_send: signal.Signals | None,
) -> None:
    """A representative caller records a stop and preserves pending work."""
    # Given
    # The executable caller fixture plans an active and a later call.

    # When
    report = run_representative_caller(
        tmp_path, "stop", "--trigger", trigger, signal_to_send=signal_to_send
    )

    # Then
    assert report["stopped"] is True
    assert report["events"] == [
        "latched",
        "cancel-requested",
        "record_attempt",
        "recorded",
        "dispatch-refused:later-call",
    ]
    assert report["attempts"] == ["active-call"]
    assert report["active_reason"] == "AttemptCancelled"
    assert report["active_signals"] == [
        {"signal": "SIGKILL", "outcome": "sent", "diagnostic": None}
    ]
    assert report["active_wait"] == "reaped"
    assert report["not_started"] == ["later-call"]
    assert report["followup_marker"] is False


def test_stop_latch_precedes_a_failing_active_call_recorder(
    tmp_path: Path,
) -> None:
    # Given
    # The disposable caller's evidence recorder is configured to fail.

    # When
    report = run_representative_caller(
        tmp_path, "stop", "--trigger", "record-failure", "--fail-recording"
    )

    # Then
    assert report["stopped"] is True
    assert report["events"] == [
        "latched",
        "cancel-requested",
        "record_attempt",
        "dispatch-refused:later-call",
    ]
    assert report["active_reason"] == "AttemptCancelled"
    assert report["active_signals"] == [
        {"signal": "SIGKILL", "outcome": "sent", "diagnostic": None}
    ]
    assert report["active_wait"] == "reaped"
    assert report["not_started"] == ["later-call"]
    assert report["stop_diagnostic"] == "RuntimeError: representative recorder failed"
    assert report["followup_marker"] is False


@pytest.mark.parametrize(
    ("unsafe_cleanup", "expected_signals", "expected_wait"),
    [
        pytest.param("signal", "failed", "reaped", id="signal-failed"),
        pytest.param("wait", "sent", "unknown", id="wait-unknown"),
    ],
)
def test_unsafe_cleanup_stops_representative_dispatch(
    tmp_path: Path,
    unsafe_cleanup: str,
    expected_signals: str,
    expected_wait: str,
) -> None:
    # Given
    # A real active CLI is paired with one fault at the cleanup effect seam.

    # When
    report = run_representative_caller(
        tmp_path, "stop", "--unsafe-cleanup", unsafe_cleanup
    )

    # Then
    assert report["stopped"] is True
    assert report["events"] == [
        "latched",
        "record_attempt",
        "recorded",
        "dispatch-refused:later-call",
    ]
    assert report["attempts"] == ["active-call"]
    assert report["active_reason"] == "TimedOut"
    expected_outcome = expected_signals
    assert report["active_signals"] == [
        {
            "signal": "SIGKILL",
            "outcome": expected_outcome,
            "diagnostic": (
                "injected signal diagnostic" if expected_outcome == "failed" else None
            ),
        }
    ]
    assert report["active_wait"] == expected_wait
    assert report["not_started"] == ["later-call"]
    assert report["followup_marker"] is False


def test_representative_caller_retries_after_prior_cleanup_is_confirmed(
    tmp_path: Path,
) -> None:
    """The example caller starts its retry after the prior CLI is reaped."""
    # Given
    # The caller fixture has one nonzero real CLI result and one retry.

    # When
    report = run_representative_caller(tmp_path, "retry")

    # Then
    assert report["stopped"] is False
    assert report["attempts"] == ["first", "retry"]
    assert report["statuses"] == [7, 0]
    events = report["events"]
    assert isinstance(events, list)
    assert len(events) == 2
    assert isinstance(events[0], str)
    assert events[1] == "retry-dispatch"
    first_direct_pid = report["first_direct_pid"]
    assert isinstance(first_direct_pid, int)
    assert first_direct_pid > 0
    assert events[0] == f"first-reaped:{first_direct_pid}:7:reaped"
    cleanup = report["cleanup"]
    assert isinstance(cleanup, list)
    assert len(cleanup) == 2
    assert all(
        isinstance(observation, dict)
        and isinstance(observation["signals"], list)
        and len(observation["signals"]) == 1
        and observation["signals"][0]["signal"] == "SIGKILL"
        and observation["signals"][0]["outcome"] in {"sent", "no_target"}
        and observation["signals"][0]["diagnostic"] is None
        and observation["direct_wait"] == "reaped"
        for observation in cleanup
    )
