# SPDX-License-Identifier: Apache-2.0
"""Disposable real-process regressions for native supervisor behavior."""

import asyncio
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
from typing import Any

import pytest

import script.process_supervisor as process_supervisor
from script.process_supervisor import (
    AttemptCancelled,
    AttemptRequest,
    AttemptResult,
    CleanupOutcome,
    Completed,
    NativeProcessEffects,
    NotLaunched,
    OutputLimitExceeded,
    ProcessHandle,
    TimedOut,
    run_attempt,
)

FIXTURE = Path(__file__).parents[1] / "fixtures" / "process_supervisor_child.py"
CALLER_FIXTURE = Path(__file__).parents[1] / "fixtures" / "process_supervisor_caller.py"


def request(
    tmp_path: Path, cap: int, *args: str, timeout: float = 3.0
) -> AttemptRequest:
    """Build a bounded request for the disposable CLI fixture."""
    return AttemptRequest(
        (sys.executable, str(FIXTURE), *args),
        tmp_path,
        timeout,
        2.0,
        cap,
        "devnull",
    )


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
    assert result.observation.cleanup.signal in {"sent", "no_target"}
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
def test_timeout_when_exited_leader_child_holds_output_pipe(
    tmp_path: Path, cap: int
) -> None:
    # Given
    attempt = request(
        tmp_path, cap, "hold-pipe", "--stdout", "7365656e0a", timeout=0.25
    )

    # When
    result = asyncio.run(run_attempt(attempt))

    # Then
    assert isinstance(result, TimedOut)
    assert result.exit_status == 0
    assert result.observation.output is not None
    assert result.observation.output.stdout == b"seen\n"
    assert result.observation.cleanup.signal == "sent"
    assert result.observation.cleanup.direct_wait == "reaped"


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
    assert error.observation.cleanup.signal == "sent"
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
    assert result.observation.cleanup.signal == "sent"
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
    assert error.observation.cleanup.signal == "sent"
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
    assert result.observation.cleanup.signal == "failed"
    assert result.observation.cleanup.signal_diagnostic == (
        "PermissionError: test denied group signal"
    )
    assert result.observation.cleanup.direct_wait == "reaped"
    assert not result.observation.cleanup.dispatch_permitted


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
        /,
    ) -> AttemptResult:
        return await self.native.capture(handle, attempt, execution_deadline)

    async def cleanup(
        self, handle: ProcessHandle, timeout_seconds: float, /
    ) -> CleanupOutcome:
        return await self.native.cleanup(handle, timeout_seconds)


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
    assert error.observation.cleanup.signal == "sent"
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
    assert report["active_signal"] == "sent"
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
    assert report["active_signal"] == "sent"
    assert report["active_wait"] == "reaped"
    assert report["not_started"] == ["later-call"]
    assert report["stop_diagnostic"] == "RuntimeError: representative recorder failed"
    assert report["followup_marker"] is False


@pytest.mark.parametrize(
    ("unsafe_cleanup", "expected_signal", "expected_wait"),
    [
        pytest.param("signal", "failed", "reaped", id="signal-failed"),
        pytest.param("wait", "sent", "unknown", id="wait-unknown"),
    ],
)
def test_unsafe_cleanup_stops_representative_dispatch(
    tmp_path: Path,
    unsafe_cleanup: str,
    expected_signal: str,
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
    assert report["active_signal"] == expected_signal
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
        and observation["signal"] in {"sent", "no_target"}
        and observation["direct_wait"] == "reaped"
        for observation in cleanup
    )
