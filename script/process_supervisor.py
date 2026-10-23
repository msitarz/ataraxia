# SPDX-License-Identifier: Apache-2.0
"""Run one bounded command in an owned POSIX session."""

import argparse
from collections.abc import Callable
from dataclasses import dataclass
import math
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import threading
import time
from types import FrameType
from typing import Literal, cast

type StopReason = Literal["completed", "timeout", "output_limit", "cancelled"]
MAX_TIMEOUT_SECONDS = 300
MAX_CLEANUP_SECONDS = 10
MAX_OUTPUT_BYTES = 1024 * 1024


@dataclass(frozen=True)
class ProcessResult:
    """Bounded process output and the observed cleanup result."""

    returncode: int | None
    stdout: bytes
    stderr: bytes
    stop_reason: StopReason
    output_limit_hit: bool
    cleanup_complete: bool
    cleanup_observation: Literal["group_absent", "group_unresolved"]
    cleanup_error: str | None
    cancellation_signal: str | None


@dataclass(frozen=True)
class _SignalHandling:
    previous: dict[signal.Signals, object]
    cancelled: threading.Event
    received: list[str]


def _positive_duration(name: str, value: float, maximum: float) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, int | float)
        or value <= 0
        or value > maximum
        or not math.isfinite(value)
    ):
        raise ValueError(f"{name} must be finite, positive, and at most {maximum}")


def _positive_output_limit(value: int) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 < value <= MAX_OUTPUT_BYTES
    ):
        raise ValueError(
            f"output_limit_bytes must be an integer from 1 to {MAX_OUTPUT_BYTES}"
        )


def _install_signal_handling() -> _SignalHandling:
    previous: dict[signal.Signals, object] = {}
    cancelled = threading.Event()
    received: list[str] = []
    if threading.current_thread() is not threading.main_thread():
        return _SignalHandling(previous, cancelled, received)

    def handle(signum: int, frame: FrameType | None) -> None:
        del frame
        if not cancelled.is_set():
            received.append(signal.Signals(signum).name)
            cancelled.set()

    try:
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous[signum] = signal.signal(signum, handle)
    except BaseException:
        _restore_signal_handling(previous)
        raise
    return _SignalHandling(previous, cancelled, received)


def _restore_signal_handling(
    previous: dict[signal.Signals, object],
) -> list[BaseException]:
    errors: list[BaseException] = []
    for signum, handler in previous.items():
        try:
            signal.signal(signum, cast(signal.Handlers, handler))
        except BaseException as error:
            errors.append(error)
    return errors


def _group_exists(pgid: int) -> bool:
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    return True


def _observe_group(pgid: int) -> tuple[bool, str | None]:
    try:
        return _group_exists(pgid), None
    except PermissionError as error:
        return (
            True,
            f"cannot inspect owned process group {pgid}: "
            f"{type(error).__name__}: {error}",
        )


def _signal_owned_group(pgid: int, sig: signal.Signals) -> str | None:
    try:
        os.killpg(pgid, sig)
    except ProcessLookupError:
        return None
    except PermissionError as error:
        return (
            f"cannot signal owned process group {pgid}: {type(error).__name__}: {error}"
        )
    return None


def _cleanup_group(
    process: subprocess.Popen[bytes], pgid: int, cleanup_seconds: float
) -> tuple[bool, Literal["group_absent", "group_unresolved"], str | None]:
    """Reap the leader, terminate remaining group members, and verify absence.

    Returns:
        Completion, observed group state, and any cleanup diagnostics.
    """
    deadline = time.monotonic() + cleanup_seconds
    errors: list[str] = []

    process.poll()
    errors.extend(_terminate_group(process, pgid, deadline, cleanup_seconds))

    if process.poll() is None:
        try:
            process.wait(timeout=max(0.0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            errors.append("leader could not be reaped within cleanup deadline")

    absent, error = _wait_for_group_absence(pgid, deadline)
    if error is not None and error not in errors:
        errors.append(error)
    if not absent:
        errors.append(
            "owned process group remains; the group probe cannot distinguish "
            "live members from unreaped descendant zombies"
        )
    observation: Literal["group_absent", "group_unresolved"] = (
        "group_absent" if absent else "group_unresolved"
    )
    return (
        absent and process.returncode is not None,
        observation,
        "; ".join(errors) or None,
    )


def _terminate_group(
    process: subprocess.Popen[bytes],
    pgid: int,
    deadline: float,
    cleanup_seconds: float,
) -> list[str]:
    errors: list[str] = []
    exists, error = _observe_group(pgid)
    if error is not None:
        errors.append(error)
    if process.returncode is None or exists:
        error = _signal_owned_group(pgid, signal.SIGTERM)
        if error is not None:
            errors.append(error)
        grace = min(cleanup_seconds / 2, 1.0)
        _wait_for_term(process, pgid, min(deadline, time.monotonic() + grace), errors)
    exists, error = _observe_group(pgid)
    if error is not None and error not in errors:
        errors.append(error)
    if exists:
        error = _signal_owned_group(pgid, signal.SIGKILL)
        if error is not None:
            errors.append(error)
    return errors


def _wait_for_term(
    process: subprocess.Popen[bytes], pgid: int, deadline: float, errors: list[str]
) -> None:
    while time.monotonic() < deadline:
        process.poll()
        exists, error = _observe_group(pgid)
        if error is not None and error not in errors:
            errors.append(error)
        if process.returncode is not None and not exists:
            return
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(0.02, remaining))


def _wait_for_group_absence(pgid: int, deadline: float) -> tuple[bool, str | None]:
    exists, error = _observe_group(pgid)
    while exists and time.monotonic() < deadline:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(0.02, remaining))
        exists, current_error = _observe_group(pgid)
        if current_error is not None:
            error = current_error
    return not exists, error


def _capture_output(
    process: subprocess.Popen[bytes],
    deadline: float,
    output_limit_bytes: int,
    cancel_events: tuple[threading.Event, ...],
    read_chunk: Callable[[int, int], bytes],
) -> tuple[bytes, bytes, StopReason, bool]:
    """Capture both output pipes through the shared byte limit.

    Returns:
        Captured stdout and stderr prefixes, stop reason, and overflow status.
    """
    stdout = bytearray()
    stderr = bytearray()
    total = 0
    try:
        with selectors.DefaultSelector() as selector:
            assert process.stdout is not None and process.stderr is not None
            selector.register(process.stdout, selectors.EVENT_READ, stdout)
            selector.register(process.stderr, selectors.EVENT_READ, stderr)
            stop_reason, total, output_limit_hit = _drain_until_stop(
                process,
                selector,
                deadline,
                output_limit_bytes,
                cancel_events,
                read_chunk,
                total,
                stdout,
                stderr,
            )
    except BaseException as error:
        for name, prefix in (
            ("stdout_prefix", bytes(stdout)),
            ("stderr_prefix", bytes(stderr)),
        ):
            setattr(error, name, prefix)
        raise
    return bytes(stdout), bytes(stderr), stop_reason, output_limit_hit


def _drain_until_stop(
    process: subprocess.Popen[bytes],
    selector: selectors.BaseSelector,
    deadline: float,
    output_limit_bytes: int,
    cancel_events: tuple[threading.Event, ...],
    read_chunk: Callable[[int, int], bytes],
    total: int,
    stdout: bytearray,
    stderr: bytearray,
) -> tuple[StopReason, int, bool]:
    """Drain output until EOF, deadline, cancellation, or overflow.

    Returns:
        Stop reason, captured byte count, and overflow status.
    """
    reason: StopReason = "completed"
    overflow = False
    while selector.get_map() or process.poll() is None:
        if any(event.is_set() for event in cancel_events):
            return "cancelled", total, overflow
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return "timeout", total, overflow
        if not selector.get_map():
            time.sleep(min(0.02, remaining))
            continue
        total, overflow = _read_ready(
            selector,
            min(0.1, remaining),
            output_limit_bytes,
            total,
            read_chunk,
            stdout,
            stderr,
        )
        if overflow:
            reason = "output_limit"
            break
    return reason, total, overflow


def _read_ready(
    selector: selectors.BaseSelector,
    wait_seconds: float,
    output_limit_bytes: int,
    total: int,
    read_chunk: Callable[[int, int], bytes],
    stdout: bytearray,
    stderr: bytearray,
) -> tuple[int, bool]:
    """Read available pipe bytes while retaining a bounded combined prefix.

    Returns:
        Updated captured byte count and whether the limit was exceeded.
    """
    for key, _ in selector.select(wait_seconds):
        chunk = read_chunk(key.fd, min(65536, output_limit_bytes - total + 1))
        if not chunk:
            selector.unregister(key.fileobj)
            continue
        room = output_limit_bytes - total
        destination: bytearray = key.data
        destination.extend(chunk[:room])
        total += min(room, len(chunk))
        if len(chunk) > room:
            return total, True
    return total, False


def _verify_session_group(process: subprocess.Popen[bytes], pgid: int) -> None:
    """Reject a process that does not own its dedicated session group.

    Raises:
        ValueError: If the process group differs from the child PID.
    """
    if pgid != process.pid:
        raise ValueError("child did not own its dedicated session group")


def run_bounded(
    argv: list[str],
    *,
    timeout_seconds: float,
    cleanup_seconds: float,
    output_limit_bytes: int,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    cancel_event: threading.Event | None = None,
    read_chunk: Callable[[int, int], bytes] = os.read,
    get_process_group_id: Callable[[int], int] = os.getpgid,
) -> ProcessResult:
    """Run a command with bounded output, execution time, and group cleanup.

    Execution allows at most 300 seconds, cleanup at most 10 seconds, and
    combined output at most 1 MiB. stdin is `/dev/null` unless a future contract
    explicitly adds an input stream. SIGINT/SIGTERM are converted to a cancelled
    result on the main thread; prior signal handlers are restored afterward.

    The process must run on POSIX, where a dedicated session can be created and
    signalled. Descendants that deliberately leave that session are outside this
    ownership boundary. A remaining group is unresolved, including if it may
    contain zombies that the supervisor is not permitted to reap.

    Returns:
        Output prefixes, leader status, stop reason, and cleanup observation.

    Raises:
        NotImplementedError: If the host cannot create a POSIX session.
    """
    _positive_duration("timeout_seconds", timeout_seconds, MAX_TIMEOUT_SECONDS)
    _positive_duration("cleanup_seconds", cleanup_seconds, MAX_CLEANUP_SECONDS)
    _positive_output_limit(output_limit_bytes)
    if os.name != "posix":
        raise NotImplementedError("owned process-group control requires POSIX")

    handling = _install_signal_handling()
    result: ProcessResult | None = None
    primary_error: BaseException | None = None
    try:
        result = _run_validated(
            argv,
            timeout_seconds,
            cleanup_seconds,
            output_limit_bytes,
            cwd,
            env,
            cancel_event,
            read_chunk,
            get_process_group_id,
            handling,
        )
    except BaseException as error:
        primary_error = error
    restore_errors = _restore_signal_handling(handling.previous)
    if primary_error is not None:
        for error in restore_errors:
            primary_error.add_note(f"signal handler restoration failed: {error}")
        raise primary_error
    if restore_errors:
        raise restore_errors[0]
    assert result is not None
    return result


def _run_validated(
    argv: list[str],
    timeout_seconds: float,
    cleanup_seconds: float,
    output_limit_bytes: int,
    cwd: Path | None,
    env: dict[str, str] | None,
    cancel_event: threading.Event | None,
    read_chunk: Callable[[int, int], bytes],
    get_process_group_id: Callable[[int], int],
    handling: _SignalHandling,
) -> ProcessResult:
    """Run and clean a process after public resource bounds are validated.

    Returns:
        Leader status, bounded output, cancellation state, and cleanup status.
    """
    deadline = time.monotonic() + timeout_seconds
    run = _execute(
        argv,
        cwd,
        env,
        deadline,
        output_limit_bytes,
        tuple(
            event for event in (cancel_event, handling.cancelled) if event is not None
        ),
        read_chunk,
        get_process_group_id,
    )
    return _complete_execution(run, cleanup_seconds, handling)


def _settle_execution(
    run: _Execution, cleanup_seconds: float
) -> tuple[
    tuple[bool, Literal["group_absent", "group_unresolved"], str | None],
    BaseException | None,
    list[BaseException],
]:
    """Attempt bounded cleanup and close process pipes on every path.

    Returns:
        Cleanup result, its raised error, and errors while closing pipes.
    """
    cleanup: tuple[bool, Literal["group_absent", "group_unresolved"], str | None]
    cleanup_error: BaseException | None = None
    try:
        cleanup = _finish(run.process, run.pgid, cleanup_seconds)
    except BaseException as error:
        cleanup = (False, "group_unresolved", f"cleanup raised {error}")
        cleanup_error = error
    close_errors = [] if run.process is None else _close_process_pipes(run.process)
    return cleanup, cleanup_error, close_errors


def _complete_execution(
    run: _Execution, cleanup_seconds: float, handling: _SignalHandling
) -> ProcessResult:
    """Report the primary error only after cleanup and pipe closure attempts.

    Returns:
        Bounded output and cleanup observations for the completed operation.
    """
    cleanup, cleanup_error, close_errors = _settle_execution(run, cleanup_seconds)
    if run.error is not None:
        _attach_process_diagnostics(
            run.error, run, cleanup, cleanup_error, close_errors
        )
        raise run.error
    if cleanup_error is not None:
        cleanup_error.add_note(
            "cleanup did not complete; owned process state is unresolved"
        )
        for error in close_errors:
            cleanup_error.add_note(f"closing process pipe failed: {error}")
        raise cleanup_error
    if close_errors:
        primary = close_errors[0]
        for error in close_errors[1:]:
            primary.add_note(f"additional pipe close failed: {error}")
        raise primary
    assert run.process is not None
    return ProcessResult(
        returncode=run.process.returncode,
        stdout=run.stdout,
        stderr=run.stderr,
        stop_reason=run.stop_reason,
        output_limit_hit=run.output_limit_hit,
        cleanup_complete=cleanup[0],
        cleanup_observation=cleanup[1],
        cleanup_error=cleanup[2],
        cancellation_signal=handling.received[0] if handling.received else None,
    )


def _attach_process_diagnostics(
    primary: BaseException,
    run: _Execution,
    cleanup: tuple[bool, Literal["group_absent", "group_unresolved"], str | None],
    cleanup_error: BaseException | None,
    close_errors: list[BaseException],
) -> None:
    for name, value in (
        ("stdout_prefix", run.stdout),
        ("stderr_prefix", run.stderr),
        ("cleanup_complete", cleanup[0]),
        ("cleanup_observation", cleanup[1]),
        ("cleanup_error", cleanup[2]),
    ):
        setattr(primary, name, value)
    primary.add_note(
        f"cleanup_complete={cleanup[0]}; "
        f"cleanup_observation={cleanup[1]}; cleanup_error={cleanup[2]}"
    )
    if cleanup_error is not None:
        primary.add_note(
            f"cleanup raised {type(cleanup_error).__name__}: {cleanup_error}"
        )
    for error in close_errors:
        primary.add_note(f"closing process pipe failed: {error}")


@dataclass(frozen=True)
class _Execution:
    process: subprocess.Popen[bytes] | None
    pgid: int | None
    stdout: bytes
    stderr: bytes
    stop_reason: StopReason
    output_limit_hit: bool
    error: BaseException | None


def _execute(
    argv: list[str],
    cwd: Path | None,
    env: dict[str, str] | None,
    deadline: float,
    output_limit_bytes: int,
    cancel_events: tuple[threading.Event, ...],
    read_chunk: Callable[[int, int], bytes],
    get_process_group_id: Callable[[int], int],
) -> _Execution:
    """Start, verify, and capture one owned process session.

    Returns:
        Process identity, captured output, stop details, and any primary error.
    """
    process: subprocess.Popen[bytes] | None = None
    pgid: int | None = None
    stdout = b""
    stderr = b""
    reason: StopReason = "completed"
    overflow = False
    error: BaseException | None = None
    try:
        process = subprocess.Popen(
            argv,
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        candidate_pgid = get_process_group_id(process.pid)
        _verify_session_group(process, candidate_pgid)
        pgid = candidate_pgid
        stdout, stderr, reason, overflow = _capture_output(
            process, deadline, output_limit_bytes, cancel_events, read_chunk
        )
    except BaseException as caught:
        error = caught
        stdout = getattr(caught, "stdout_prefix", b"")
        stderr = getattr(caught, "stderr_prefix", b"")
    return _Execution(process, pgid, stdout, stderr, reason, overflow, error)


def _finish(
    process: subprocess.Popen[bytes] | None, pgid: int | None, cleanup_seconds: float
) -> tuple[bool, Literal["group_absent", "group_unresolved"], str | None]:
    if process is None:
        return True, "group_absent", None
    if pgid is None:
        error = _cleanup_unverified_leader(process, cleanup_seconds)
        return (
            False,
            "group_unresolved",
            f"could not verify the child session; {error}",
        )
    return _cleanup_group(process, pgid, cleanup_seconds)


def _cleanup_unverified_leader(
    process: subprocess.Popen[bytes], cleanup_seconds: float
) -> str:
    """Stop and reap the owned leader when its descendant group is unverified.

    Returns:
        A diagnostic that leaves descendant cleanup explicitly unresolved.
    """
    errors: list[str] = []
    if process.poll() is None:
        error = _signal_unverified_leader(process, "terminate")
        if error is not None:
            errors.append(error)
        error = _wait_unverified_leader(process, cleanup_seconds / 2)
        if error is not None:
            errors.append(error)
        if process.poll() is None:
            error = _signal_unverified_leader(process, "kill")
            if error is not None:
                errors.append(error)
            error = _wait_unverified_leader(process, cleanup_seconds / 2)
            if error is not None:
                errors.append(error)
    status = "leader reaped" if process.returncode is not None else "leader unresolved"
    errors.append(f"{status}; descendants remain unverified")
    return "; ".join(errors)


def _signal_unverified_leader(
    process: subprocess.Popen[bytes], action: Literal["terminate", "kill"]
) -> str | None:
    try:
        getattr(process, action)()
    except ProcessLookupError:
        return None
    except BaseException as error:
        return f"leader {action} failed: {type(error).__name__}: {error}"
    return None


def _wait_unverified_leader(
    process: subprocess.Popen[bytes], timeout: float
) -> str | None:
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        return "leader could not be reaped within cleanup deadline"
    except BaseException as error:
        return f"leader wait failed: {type(error).__name__}: {error}"
    return None


def _close_process_pipes(process: subprocess.Popen[bytes]) -> list[BaseException]:
    errors: list[BaseException] = []
    for stream in (process.stdout, process.stderr):
        if stream is not None:
            try:
                stream.close()
            except BaseException as error:
                errors.append(error)
    return errors


def _codex_check() -> int:
    """Exercise the installed CLI's process identity through this owner.

    Returns:
        0 when both CLI commands exit successfully and cleanup is complete;
        otherwise 1.
    """
    for args in (["codex", "--version"], ["codex", "--help"]):
        result = run_bounded(
            list(args),
            timeout_seconds=10,
            cleanup_seconds=2,
            output_limit_bytes=64 * 1024,
        )
        sys.stdout.write(
            f"argv={args!r} exit={result.returncode} "
            f"cleanup={result.cleanup_observation} "
            f"complete={result.cleanup_complete}\n"
        )
        if result.stdout:
            first_line = result.stdout.decode(errors="replace").splitlines()[0]
            sys.stdout.write(f"{first_line}\n")
        if result.returncode != 0 or not result.cleanup_complete:
            if result.cleanup_error:
                sys.stderr.write(f"{result.cleanup_error}\n")
            return 1
    return 0


def main() -> int:
    """Run the non-inference installed Codex process check.

    Returns:
        The exit status of the installed Codex check.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--codex-check", action="store_true")
    args = parser.parse_args()
    if not args.codex_check:
        parser.error("select --codex-check")
    return _codex_check()


if __name__ == "__main__":
    raise SystemExit(main())
