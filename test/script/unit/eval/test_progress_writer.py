# SPDX-License-Identifier: Apache-2.0
"""Bounded progress admission and worker ownership with controlled I/O."""

import asyncio
from collections.abc import Callable
from contextlib import suppress
import threading
from typing import override

import pytest

from script.eval.runner.adapters.progress_writer import (
    MAX_MESSAGE_BYTES,
    open_progress_writer,
)


class ControlledWrite:
    """Hold the first write while recording claims and descriptor closure."""

    def __init__(self) -> None:
        self.started = threading.Event()
        self.release = threading.Event()
        self.second = threading.Event()
        self.closed = threading.Event()
        self.messages: list[bytes] = []
        self.closed_fds: list[int] = []
        self.thread: threading.Thread | None = None

    def duplicate(self, fd: int) -> int:
        return 73

    def write(self, fd: int, data: bytes) -> int:
        self.messages.append(data)
        if len(self.messages) == 1:
            self.started.set()
            if not self.release.wait(5):
                raise TimeoutError("test did not release writer")
        else:
            self.second.set()
        return len(data)

    def close(self, fd: int) -> None:
        self.closed_fds.append(fd)
        self.closed.set()

    def thread_factory(self, target: Callable[[], None]) -> threading.Thread:
        self.thread = threading.Thread(target=target)
        return self.thread


def test_latest_pending_message_replaces_older_while_writer_is_blocked() -> None:
    # Given
    io = ControlledWrite()
    writer = open_progress_writer(
        1,
        duplicate=io.duplicate,
        write=io.write,
        close_fd=io.close,
        thread_factory=io.thread_factory,
    )
    assert writer is not None

    # When
    try:
        assert writer("first") == "accepted"
        assert io.started.wait(5)
        assert writer("old") == "accepted"
        assert writer("latest") == "accepted"
        io.release.set()
        assert io.second.wait(5)
        writer.close()
        assert io.closed.wait(5)
    finally:
        io.release.set()
        writer.close()

    # Then
    assert io.messages == [b"first", b"latest"]
    assert io.closed_fds == [73]
    assert io.thread is not None and io.thread.daemon
    assert writer("after close") == "unavailable"


def test_important_pending_message_survives_routine_refresh() -> None:
    # Given
    io = ControlledWrite()
    writer = open_progress_writer(
        1, duplicate=io.duplicate, write=io.write, close_fd=io.close
    )
    assert writer is not None

    # When
    try:
        assert writer("first") == "accepted" and io.started.wait(5)
        assert writer("detail", important=True) == "accepted"
        routine = writer("refresh")
        io.release.set()
        assert io.second.wait(5)
        writer.close()
        assert io.closed.wait(5)
    finally:
        io.release.set()
        writer.close()

    # Then
    assert routine == "dropped"
    assert io.messages == [b"first", b"detail"]


def test_close_discards_pending_without_waiting_for_blocked_write() -> None:
    # Given
    io = ControlledWrite()
    writer = open_progress_writer(
        1, duplicate=io.duplicate, write=io.write, close_fd=io.close
    )
    assert writer is not None

    # When
    try:
        assert writer("first") == "accepted" and io.started.wait(5)
        assert writer("pending") == "accepted"
        writer.close()
        assert not io.closed.is_set()
        io.release.set()
        assert io.closed.wait(5)
    finally:
        io.release.set()
        writer.close()

    # Then
    assert io.messages == [b"first"]
    assert writer("after close") == "unavailable"


@pytest.mark.parametrize("partial", [True, False], ids=["partial", "error"])
def test_failed_write_disables_admission_and_closes_owned_descriptor(
    partial: bool,
) -> None:
    # Given
    io = ControlledWrite()

    def write(target: int, data: bytes) -> int:
        if partial:
            return 1
        raise OSError("broken")

    writer = open_progress_writer(
        1, duplicate=io.duplicate, write=write, close_fd=io.close
    )
    assert writer is not None

    # When
    try:
        assert writer("message") == "accepted"
        assert io.closed.wait(5)
        result = writer("later")
    finally:
        writer.close()

    # Then
    assert result == "unavailable"
    assert io.closed_fds == [73]


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("é" * (MAX_MESSAGE_BYTES // 2), "accepted"),
        ("é" * (MAX_MESSAGE_BYTES // 2) + "x", "dropped"),
    ],
    ids=["exact-byte-limit", "one-byte-over"],
)
def test_utf8_byte_limit(message: str, expected: str) -> None:
    # Given
    io = ControlledWrite()
    writer = open_progress_writer(
        1, duplicate=io.duplicate, write=io.write, close_fd=io.close
    )
    assert writer is not None

    # When
    try:
        result = writer(message)
    finally:
        io.release.set()
        writer.close()
        assert io.closed.wait(5)

    # Then
    assert result == expected


@pytest.mark.parametrize(
    "error",
    [KeyboardInterrupt(), asyncio.CancelledError(), SystemExit()],
    ids=["interrupt", "cancel", "exit"],
)
def test_interrupted_start_closes_duplicate_and_preserves_error(
    error: BaseException,
) -> None:
    # Given
    io = ControlledWrite()

    class RefuseStart(threading.Thread):
        @override
        def start(self) -> None:
            raise error

    # When
    with pytest.raises(type(error)) as caught:
        open_progress_writer(
            1,
            duplicate=io.duplicate,
            close_fd=io.close,
            thread_factory=lambda target: RefuseStart(target=target),
        )

    # Then
    assert caught.value is error
    assert io.closed_fds == [73]


def test_late_worker_after_failed_start_cannot_close_or_write_duplicate() -> None:
    # Given
    io = ControlledWrite()
    enter, entered = threading.Event(), threading.Event()

    class DelayedStart(threading.Thread):
        @override
        def start(self) -> None:
            super().start()
            raise RuntimeError("start failed")

    def factory(target: Callable[[], None]) -> threading.Thread:
        def delayed() -> None:
            if enter.wait(5):
                target()
            entered.set()

        return DelayedStart(target=delayed)

    # When
    try:
        result = open_progress_writer(
            1,
            duplicate=io.duplicate,
            write=io.write,
            close_fd=io.close,
            thread_factory=factory,
        )
        enter.set()
        assert entered.wait(5)
    finally:
        enter.set()
        io.release.set()

    # Then
    assert result is None
    assert io.closed_fds == [73]
    assert io.messages == []


def test_unexpected_worker_exit_disables_admission() -> None:
    # Given
    io = ControlledWrite()

    def write(fd: int, data: bytes) -> int:
        raise SystemExit()

    def factory(target: Callable[[], None]) -> threading.Thread:
        def capture() -> None:
            with suppress(SystemExit):
                target()

        return threading.Thread(target=capture)

    writer = open_progress_writer(
        1,
        duplicate=io.duplicate,
        write=write,
        close_fd=io.close,
        thread_factory=factory,
    )
    assert writer is not None

    # When
    try:
        assert writer("message") == "accepted"
        assert io.closed.wait(5)
        result = writer("later")
    finally:
        writer.close()

    # Then
    assert result == "unavailable"
    assert io.closed_fds == [73]
