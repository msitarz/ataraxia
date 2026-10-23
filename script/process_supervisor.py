# SPDX-License-Identifier: Apache-2.0
"""Run bounded asynchronous commands in owned POSIX sessions."""

import argparse
import asyncio
from collections.abc import Awaitable, Callable
from contextlib import suppress
from dataclasses import dataclass, field
import math
import os
from pathlib import Path
import signal
import sys
from types import FrameType
from typing import Any, Literal, cast, override

type StopReason = Literal["completed", "timeout", "output_limit", "cancelled"]
type GroupObservation = Literal["group_absent", "group_unresolved"]
type SignalHandler = signal.Handlers | Callable[[int, FrameType | None], Any]
MAX_TIMEOUT_SECONDS = 300
MAX_CLEANUP_SECONDS = 10
MAX_OUTPUT_BYTES = 1024 * 1024


@dataclass(frozen=True)
class ProcessResult:
    """Bounded output and the observed cleanup result."""

    returncode: int | None
    stdout: bytes
    stderr: bytes
    stop_reason: StopReason
    output_limit_hit: bool
    cleanup_complete: bool
    cleanup_observation: GroupObservation
    cleanup_error: str | None
    cancellation_signal: str | None


@dataclass
class _Execution:
    """Mutable state for one subprocess protocol."""

    loop: asyncio.AbstractEventLoop
    changed: asyncio.Event = field(default_factory=asyncio.Event)
    leader_exited: bool = False
    stdout_eof: bool = False
    stderr_eof: bool = False
    returncode: int | None = None
    stdout: bytearray = field(default_factory=bytearray)
    stderr: bytearray = field(default_factory=bytearray)
    total: int = 0
    output_limit_hit: bool = False
    error: BaseException | None = None
    transport: asyncio.SubprocessTransport | None = None
    transport_closed: asyncio.Event = field(default_factory=asyncio.Event)
    cleanup_deadline: float | None = None
    on_data: Callable[[int, bytes], None] | None = None
    capturing: bool = True

    @property
    def streams_complete(self) -> bool:
        """Whether both captured streams reached EOF."""
        return self.stdout_eof and self.stderr_eof

    def data_received(self, fd: int, data: bytes) -> None:
        """Retain the exact combined prefix and observe overflow."""
        if not self.capturing:
            return
        if self.on_data is not None:
            self.on_data(fd, data)
        room = self.output_limit_bytes - self.total
        destination = self.stdout if fd == 1 else self.stderr
        accepted = min(room, len(data))
        destination.extend(data[:accepted])
        self.total += accepted
        if len(data) > room:
            self.output_limit_hit = True
        self.changed.set()

    output_limit_bytes: int = MAX_OUTPUT_BYTES


class _ProcessProtocol(asyncio.SubprocessProtocol):
    """Collect public subprocess callbacks without private transports."""

    def __init__(self, execution: _Execution) -> None:
        self.execution = execution

    @override
    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.execution.transport = cast(asyncio.SubprocessTransport, transport)

    @override
    def pipe_data_received(self, fd: int, data: bytes) -> None:
        try:
            self.execution.data_received(fd, data)
        except BaseException as error:
            if self.execution.error is None:
                self.execution.error = error
            self.execution.changed.set()

    @override
    def pipe_connection_lost(self, fd: int, exc: Exception | None) -> None:
        if fd == 1:
            self.execution.stdout_eof = True
        elif fd == 2:
            self.execution.stderr_eof = True
        if exc is not None and self.execution.error is None:
            self.execution.error = exc
        self.execution.changed.set()

    @override
    def connection_lost(self, exc: Exception | None) -> None:
        if exc is not None and self.execution.error is None:
            self.execution.error = exc
        self.execution.transport_closed.set()
        self.execution.changed.set()

    @override
    def process_exited(self) -> None:
        transport = self.execution.transport
        if transport is not None:
            self.execution.returncode = transport.get_returncode()
        self.execution.leader_exited = True
        self.execution.changed.set()


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


def _observe_group(pgid: int) -> tuple[bool, str | None]:
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False, None
    except PermissionError as error:
        return True, (
            f"cannot inspect owned process group {pgid}: "
            f"{type(error).__name__}: {error}"
        )
    return True, None


def _signal_group(pgid: int, signum: signal.Signals) -> str | None:
    try:
        os.killpg(pgid, signum)
    except ProcessLookupError:
        return None
    except PermissionError as error:
        return (
            f"cannot signal owned process group {pgid}: {type(error).__name__}: {error}"
        )
    return None


async def _wait_for_change(execution: _Execution, seconds: float) -> None:
    execution.changed.clear()
    if seconds <= 0:
        return
    with suppress(TimeoutError):
        await asyncio.wait_for(execution.changed.wait(), timeout=seconds)


async def _capture(
    execution: _Execution,
    deadline: float,
    cancel_event: asyncio.Event | None,
) -> StopReason:
    loop = execution.loop
    if execution.error is not None:
        execution.capturing = False
        raise execution.error
    if execution.output_limit_hit:
        execution.capturing = False
        return "output_limit"
    while not (execution.leader_exited and execution.streams_complete):
        if execution.error is not None:
            execution.capturing = False
            raise execution.error
        if execution.output_limit_hit:
            execution.capturing = False
            return "output_limit"
        if cancel_event is not None and cancel_event.is_set():
            execution.capturing = False
            return "cancelled"
        remaining = deadline - loop.time()
        if remaining <= 0:
            execution.capturing = False
            return "timeout"
        await _wait_for_change(execution, min(remaining, 0.1))
    execution.capturing = False
    if execution.error is not None:
        raise execution.error
    if execution.output_limit_hit:
        return "output_limit"
    return "completed"


async def _cleanup(
    execution: _Execution,
    pgid: int | None,
    cleanup_seconds: float,
) -> _CleanupResult:
    if execution.transport is None:
        return _CleanupResult(True, "group_absent", None)
    if pgid is None:
        return await _cleanup_unverified(execution, cleanup_seconds)
    return await _cleanup_verified(execution, pgid, cleanup_seconds)


async def _cleanup_unverified(
    execution: _Execution, cleanup_seconds: float
) -> _CleanupResult:
    errors: list[str] = []
    transport = execution.transport
    if transport is not None and not execution.leader_exited:
        errors.extend(
            await _stop_unverified_leader(execution, transport, cleanup_seconds)
        )
    errors.append("child session identity is unverified; descendants remain unverified")
    return _CleanupResult(False, "group_unresolved", "; ".join(errors))


async def _stop_unverified_leader(
    execution: _Execution,
    transport: asyncio.SubprocessTransport,
    cleanup_seconds: float,
) -> list[str]:
    errors: list[str] = []
    term_error = _signal_leader(transport, signal.SIGTERM)
    if term_error is not None:
        errors.append(term_error)
    reaped, wait_error = await _wait_leader_within(execution, cleanup_seconds / 2)
    if wait_error is not None:
        errors.append(wait_error)
    if reaped:
        return errors
    kill_error = _signal_leader(transport, signal.SIGKILL)
    if kill_error is not None:
        errors.append(kill_error)
    reaped, wait_error = await _wait_leader_within(execution, cleanup_seconds / 2)
    if wait_error is not None:
        errors.append(wait_error)
    if not reaped:
        errors.append("unverified leader could not be reaped")
    return errors


async def _wait_leader_within(
    execution: _Execution, timeout: float
) -> tuple[bool, str | None]:
    try:
        await asyncio.wait_for(_wait_leader(execution), timeout)
    except TimeoutError:
        return False, None
    except Exception as error:
        return False, f"unverified leader wait failed: {error}"
    return True, None


def _signal_leader(
    transport: asyncio.SubprocessTransport, signum: signal.Signals
) -> str | None:
    try:
        transport.send_signal(signum)
    except ProcessLookupError:
        return None
    except BaseException as error:
        return f"cannot signal unverified leader: {type(error).__name__}: {error}"
    return None


async def _cleanup_verified(
    execution: _Execution,
    pgid: int,
    cleanup_seconds: float,
) -> _CleanupResult:
    deadline = execution.loop.time() + cleanup_seconds
    errors: list[str] = []
    await _terminate_owned_group(execution, pgid, deadline, cleanup_seconds, errors)
    complete, observation = await _confirm_cleanup(execution, pgid, deadline, errors)
    return _CleanupResult(complete, observation, "; ".join(errors) or None)


async def _terminate_owned_group(
    execution: _Execution,
    pgid: int,
    deadline: float,
    cleanup_seconds: float,
    errors: list[str],
) -> None:
    exists, error = _observe_group(pgid)
    if error is not None:
        errors.append(error)
    if not execution.leader_exited or exists:
        error = _signal_group(pgid, signal.SIGTERM)
        if error is not None:
            errors.append(error)
        await _wait_for_term(execution, pgid, deadline, cleanup_seconds, errors)
        exists, observed_error = _observe_group(pgid)
        if observed_error is not None and observed_error not in errors:
            errors.append(observed_error)
        if exists:
            error = _signal_group(pgid, signal.SIGKILL)
            if error is not None:
                errors.append(error)


async def _confirm_cleanup(
    execution: _Execution, pgid: int, deadline: float, errors: list[str]
) -> tuple[bool, GroupObservation]:
    if not execution.leader_exited:
        try:
            await asyncio.wait_for(
                _wait_leader(execution), max(0, deadline - execution.loop.time())
            )
        except TimeoutError:
            errors.append("leader could not be reaped within cleanup deadline")

    exists, observed_error = _observe_group(pgid)
    if observed_error is not None and observed_error not in errors:
        errors.append(observed_error)
    exists = await _wait_for_group_absence(execution, pgid, deadline, exists, errors)
    if exists:
        errors.append(
            "owned process group remains; the probe cannot distinguish live "
            "members from unreaped descendant zombies"
        )
    observation: GroupObservation = "group_unresolved" if exists else "group_absent"
    complete = not exists and execution.leader_exited
    return complete, observation


async def _wait_for_term(
    execution: _Execution,
    pgid: int,
    cleanup_deadline: float,
    cleanup_seconds: float,
    errors: list[str],
) -> None:
    term_deadline = min(
        cleanup_deadline, execution.loop.time() + min(cleanup_seconds / 2, 1.0)
    )
    while execution.loop.time() < term_deadline:
        exists, error = _observe_group(pgid)
        if error is not None and error not in errors:
            errors.append(error)
        if execution.leader_exited and not exists:
            return
        remaining = term_deadline - execution.loop.time()
        await _wait_for_change(execution, min(0.02, remaining))


async def _wait_for_group_absence(
    execution: _Execution,
    pgid: int,
    deadline: float,
    exists: bool,
    errors: list[str],
) -> bool:
    while exists and execution.loop.time() < deadline:
        await asyncio.sleep(min(0.02, deadline - execution.loop.time()))
        exists, error = _observe_group(pgid)
        if error is not None and error not in errors:
            errors.append(error)
    return exists


async def _wait_leader(execution: _Execution) -> None:
    while not execution.leader_exited:
        await _wait_for_change(execution, 0.05)


async def _close(execution: _Execution) -> None:
    transport = execution.transport
    if transport is None:
        return
    transport.close()
    deadline = execution.cleanup_deadline
    if deadline is None:
        await asyncio.sleep(0)
        return
    remaining = deadline - execution.loop.time()
    if remaining > 0:
        try:
            await asyncio.wait_for(execution.transport_closed.wait(), remaining)
        except TimeoutError:
            raise TimeoutError(
                "subprocess transport did not close within cleanup deadline"
            ) from None


async def _settle(
    execution: _Execution,
    pgid: int | None,
    cleanup_seconds: float,
) -> _CleanupResult:
    execution.cleanup_deadline = execution.loop.time() + cleanup_seconds
    close_reserve = min(0.05, cleanup_seconds / 10)
    try:
        cleanup = await _cleanup(
            execution, pgid, max(0.001, cleanup_seconds - close_reserve)
        )
        cleanup_error = None
    except BaseException as error:
        cleanup = _CleanupResult(
            False, "group_unresolved", f"cleanup raised {error}", error
        )
        cleanup_error = error
    try:
        await _close(execution)
    except BaseException as error:
        if cleanup_error is None:
            cleanup_error = error
        else:
            cleanup_error.add_note(f"closing subprocess transport failed: {error}")
    return _CleanupResult(
        cleanup.complete and cleanup_error is None,
        cleanup.observation if cleanup_error is None else "group_unresolved",
        _combine_diagnostics(
            cleanup.diagnostic,
            None
            if cleanup_error is None
            else f"transport close failed: {cleanup_error}",
        ),
        cleanup_error or cleanup.error,
    )


def _combine_diagnostics(first: str | None, second: str | None) -> str | None:
    if first is None:
        return second
    if second is None:
        return first
    return f"{first}; {second}"


async def _settle_shielded(
    execution: _Execution,
    pgid: int | None,
    cleanup_seconds: float,
    primary: BaseException | None,
) -> _CleanupResult:
    task = asyncio.create_task(_settle(execution, pgid, cleanup_seconds))
    cancellations: list[asyncio.CancelledError] = []
    result = await _await_settlement(task, cancellations)
    if primary is not None:
        _attach_cleanup_diagnostics(primary, execution, result)
        for cancellation in cancellations:
            primary.add_note(f"additional cancellation during cleanup: {cancellation}")
        if isinstance(primary, asyncio.CancelledError):
            raise primary
        return result
    if cancellations:
        cancellation = cancellations[0]
        _attach_cleanup_diagnostics(cancellation, execution, result)
        for additional in cancellations[1:]:
            cancellation.add_note(
                f"additional cancellation during cleanup: {additional}"
            )
        raise cancellation
    return result


async def _await_settlement(
    task: asyncio.Task[_CleanupResult],
    cancellations: list[asyncio.CancelledError],
) -> _CleanupResult:
    while not task.done():
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError as error:
            cancellations.append(error)
    return task.result()


def _attach_cleanup_diagnostics(
    error: BaseException, execution: _Execution, cleanup: _CleanupResult
) -> None:
    for name, value in (
        ("stdout_prefix", bytes(execution.stdout)),
        ("stderr_prefix", bytes(execution.stderr)),
        ("cleanup_complete", cleanup.complete),
        ("cleanup_observation", cleanup.observation),
        ("cleanup_error", cleanup.diagnostic),
    ):
        setattr(error, name, value)
    if cleanup.error is not None:
        error.add_note(f"cleanup failed: {cleanup.error}")


@dataclass(frozen=True)
class _RunState:
    pgid: int | None
    reason: StopReason
    error: BaseException | None


@dataclass(frozen=True)
class _CleanupResult:
    complete: bool
    observation: GroupObservation
    diagnostic: str | None
    error: BaseException | None = None


async def _acquire_and_capture(
    execution: _Execution,
    spawn_task: asyncio.Task[tuple[asyncio.SubprocessTransport, _ProcessProtocol]],
    deadline: float,
    cancel_event: asyncio.Event | None,
    get_process_group_id: Callable[[int], int],
) -> _RunState:
    error = await _await_spawn(spawn_task)
    pgid: int | None = None
    reason: StopReason = "completed"
    try:
        execution.transport, _ = spawn_task.result()
    except BaseException as caught:
        if error is None:
            error = caught
        elif error is not caught:
            error.add_note(f"subprocess creation failed: {caught}")
    if execution.transport is not None:
        pgid, error, reason = await _verify_and_capture(
            execution, deadline, cancel_event, get_process_group_id, error
        )
    return _RunState(pgid, reason, error)


async def _await_spawn(
    spawn_task: asyncio.Task[tuple[asyncio.SubprocessTransport, _ProcessProtocol]],
) -> BaseException | None:
    primary: BaseException | None = None
    while not spawn_task.done():
        try:
            await asyncio.shield(spawn_task)
        except BaseException as error:
            if primary is None:
                primary = error
            elif primary is not error:
                primary.add_note(f"subprocess creation failed: {error}")
    return primary


async def _verify_and_capture(
    execution: _Execution,
    deadline: float,
    cancel_event: asyncio.Event | None,
    get_process_group_id: Callable[[int], int],
    primary: BaseException | None,
) -> tuple[int | None, BaseException | None, StopReason]:
    transport = execution.transport
    assert transport is not None
    pgid: int | None = None
    reason: StopReason = "completed"
    try:
        pgid = _get_verified_group_id(
            transport.get_pid(), get_process_group_id, execution.leader_exited
        )
        if primary is None:
            reason = await _capture(execution, deadline, cancel_event)
    except asyncio.CancelledError as caught:
        if primary is None:
            primary = caught
    except BaseException as caught:
        if primary is None:
            primary = caught
        else:
            primary.add_note(f"subprocess observation failed: {caught}")
    return pgid, primary, reason


def _get_verified_group_id(
    pid: int,
    get_process_group_id: Callable[[int], int],
    leader_exited: bool,
) -> int:
    try:
        candidate = get_process_group_id(pid)
    except ProcessLookupError:
        if not leader_exited:
            raise
        # start_new_session guarantees that the child's initial process group
        # ID is its PID, even if asyncio reaped the leader before this check.
        return pid
    if candidate != pid:
        raise ValueError("child did not own its dedicated session group")
    return candidate


async def run_bounded(
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
) -> ProcessResult:
    """Run and clean one process within the declared protocol caps.

    Task cancellation is re-raised after bounded cleanup. A shared event stops
    the invocation cooperatively and returns a ``cancelled`` result. SIGINT and
    SIGTERM belong to the command-line entry boundary, not this composable API.

    Returns:
        The leader status, bounded output prefixes, and cleanup observation.

    Raises:
        NotImplementedError: If POSIX process-group control is unavailable.
    """
    _positive_duration("timeout_seconds", timeout_seconds, MAX_TIMEOUT_SECONDS)
    _positive_duration("cleanup_seconds", cleanup_seconds, MAX_CLEANUP_SECONDS)
    _positive_output_limit(output_limit_bytes)
    if os.name != "posix":
        raise NotImplementedError("owned process-group control requires POSIX")
    if cancel_event is not None and cancel_event.is_set():
        return ProcessResult(
            returncode=None,
            stdout=b"",
            stderr=b"",
            stop_reason="cancelled",
            output_limit_hit=False,
            cleanup_complete=True,
            cleanup_observation="group_absent",
            cleanup_error=None,
            cancellation_signal=(
                cancel_event.signal_name
                if isinstance(cancel_event, _CancellationEvent)
                else None
            ),
        )

    loop = asyncio.get_running_loop()
    execution = _Execution(
        loop=loop, output_limit_bytes=output_limit_bytes, on_data=on_data
    )
    deadline = loop.time() + timeout_seconds
    spawn = loop.subprocess_exec(
        lambda: _ProcessProtocol(execution),
        *argv,
        cwd=cwd,
        env=env,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        start_new_session=True,
    )
    spawn_task = asyncio.create_task(spawn)
    state = await _acquire_and_capture(
        execution, spawn_task, deadline, cancel_event, get_process_group_id
    )
    cleanup = await _settle_shielded(
        execution,
        state.pgid,
        cleanup_seconds,
        state.error,
    )

    if state.error is not None:
        raise state.error
    if cleanup.error is not None:
        raise cleanup.error
    return ProcessResult(
        returncode=execution.returncode,
        stdout=bytes(execution.stdout),
        stderr=bytes(execution.stderr),
        stop_reason=state.reason,
        output_limit_hit=execution.output_limit_hit,
        cleanup_complete=cleanup.complete,
        cleanup_observation=cleanup.observation,
        cleanup_error=cleanup.diagnostic,
        cancellation_signal=(
            cancel_event.signal_name
            if isinstance(cancel_event, _CancellationEvent)
            else None
        ),
    )


def _codex_check() -> int:
    """Run non-inference installed CLI startup checks.

    Returns:
        0 when both commands exit successfully and cleanup is complete;
        otherwise 1.
    """
    cancelled = _CancellationEvent()

    async def check() -> int:
        for args in (["codex", "--version"], ["codex", "--help"]):
            result = await run_bounded(
                list(args),
                timeout_seconds=10,
                cleanup_seconds=2,
                output_limit_bytes=64 * 1024,
                cancel_event=cancelled,
            )
            sys.stdout.write(
                f"argv={args!r} exit={result.returncode} "
                f"cleanup={result.cleanup_observation} "
                f"complete={result.cleanup_complete}\n"
            )
            if result.stdout:
                first_line = result.stdout.decode(errors="replace").splitlines()[0]
                sys.stdout.write(first_line + "\n")
            if result.returncode != 0 or not result.cleanup_complete:
                if result.cleanup_error:
                    sys.stderr.write(f"{result.cleanup_error}\n")
                return 1
        return 0

    return asyncio.run(_cli_with_signals(check(), cancelled))


async def _cli_with_signals[T](
    operation: Awaitable[T], cancelled: _CancellationEvent
) -> T:
    """Own process signals once around the CLI's active async operation.

    Returns:
        The wrapped operation's exit status.
    """
    loop = asyncio.get_running_loop()
    previous: dict[signal.Signals, SignalHandler] = {}
    primary: BaseException | None = None

    def handle(signum: signal.Signals) -> None:
        if not cancelled.is_set():
            cancelled.signal_name = signum.name
            cancelled.set()

    try:
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous[signum] = _restorable_signal_handler(signum)
            loop.add_signal_handler(signum, handle, signum)
        return await operation
    except BaseException as error:
        primary = error
        raise
    finally:
        errors = _restore_signal_handlers(loop, previous)
        if primary is not None:
            for error in errors:
                primary.add_note(f"signal handler restoration failed: {error}")
        elif errors:
            for error in errors[1:]:
                errors[0].add_note(f"additional signal restoration failure: {error}")
            raise errors[0]


def _restorable_signal_handler(signum: signal.Signals) -> SignalHandler:
    """Read a handler that the owner can restore.

    Returns:
        The prior callable or enum handler.

    Raises:
        RuntimeError: If the platform returns no previous handler.
    """
    handler = signal.getsignal(signum)
    if handler is None:
        raise RuntimeError(f"signal {signum.name} has no restorable handler")
    if isinstance(handler, signal.Handlers):
        return handler
    if isinstance(handler, int):
        raise RuntimeError(f"signal {signum.name} has an unsupported integer handler")
    return handler


def _restore_signal_handlers(
    loop: asyncio.AbstractEventLoop,
    previous: dict[signal.Signals, SignalHandler],
) -> list[BaseException]:
    errors: list[BaseException] = []
    for signum, handler in previous.items():
        try:
            loop.remove_signal_handler(signum)
        except BaseException as error:
            errors.append(error)
        try:
            signal.signal(signum, handler)
        except BaseException as error:
            errors.append(error)
    return errors


class _CancellationEvent(asyncio.Event):
    """CLI cancellation event that retains the first received signal."""

    signal_name: str | None = None


def main() -> int:
    """Run the optional installed Codex check.

    Returns:
        The installed CLI check's exit status.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--codex-check", action="store_true")
    args = parser.parse_args()
    if not args.codex_check:
        parser.error("select --codex-check")
    return _codex_check()


if __name__ == "__main__":
    raise SystemExit(main())
