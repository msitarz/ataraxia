# SPDX-License-Identifier: Apache-2.0
"""Bounded progress admission and worker ownership."""

import os
from pathlib import Path
import threading
from typing import override

import pytest

from script.eval.runner.adapters.progress_writer import (
    MAX_MESSAGE_BYTES,
    open_progress_writer,
)


class ControlledWrite:
    """Hold the first write while recording any subsequent claims."""

    def __init__(self) -> None:
        self.started = threading.Event()
        self.release = threading.Event()
        self.second = threading.Event()
        self.closed = threading.Event()
        self.messages: list[bytes] = []
        self.thread: threading.Thread | None = None
        self.inheritable: bool | None = None

    def write(self, fd: int, data: bytes) -> int:
        self.messages.append(data)
        self.inheritable = os.get_inheritable(fd)
        if len(self.messages) == 1:
            self.started.set()
            if not self.release.wait(5):
                raise TimeoutError("test did not release writer")
        else:
            self.second.set()
        return len(data)

    def close(self, fd: int) -> None:
        os.close(fd)
        self.closed.set()

    def thread_factory(self, target: object) -> threading.Thread:
        assert callable(target)
        self.thread = threading.Thread(target=target)
        return self.thread


def test_latest_pending_message_replaces_older_while_writer_is_blocked(
    tmp_path: Path,
) -> None:
    # Given
    fd = os.open(tmp_path / "output", os.O_CREAT | os.O_WRONLY, 0o600)
    io = ControlledWrite()
    writer = open_progress_writer(
        fd, write=io.write, close_fd=io.close, thread_factory=io.thread_factory
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
        os.close(fd)

    # Then
    assert io.messages == [b"first", b"latest"]
    assert io.thread is not None and io.thread.daemon
    assert io.inheritable is False
    assert writer("after close") == "unavailable"


def test_close_drops_pending_and_never_waits_for_blocked_write(tmp_path: Path) -> None:
    # Given
    fd = os.open(tmp_path / "output", os.O_CREAT | os.O_WRONLY, 0o600)
    io = ControlledWrite()
    writer = open_progress_writer(fd, write=io.write, close_fd=io.close)
    assert writer is not None

    # When
    try:
        assert writer("first") == "accepted"
        assert io.started.wait(5)
        assert writer("pending") == "accepted"
        writer.close()
        assert not io.closed.is_set()
        io.release.set()
        assert io.closed.wait(5)
    finally:
        io.release.set()
        writer.close()
        os.close(fd)

    # Then
    assert io.messages == [b"first"]
    assert writer("after close") == "unavailable"


@pytest.mark.parametrize("partial", [True, False], ids=["partial", "error"])
def test_failed_write_disables_admission_and_closes_owned_descriptor(
    tmp_path: Path, partial: bool
) -> None:
    # Given
    fd = os.open(tmp_path / "output", os.O_CREAT | os.O_WRONLY, 0o600)
    closed = threading.Event()

    def write(target: int, data: bytes) -> int:
        if partial:
            return 1
        raise OSError("broken")

    def close(target: int) -> None:
        os.close(target)
        closed.set()

    writer = open_progress_writer(fd, write=write, close_fd=close)
    assert writer is not None

    # When
    try:
        assert writer("message") == "accepted"
        assert closed.wait(5)
        result = writer("later")
    finally:
        writer.close()
        os.close(fd)

    # Then
    assert result == "unavailable"


def test_oversized_message_is_dropped(tmp_path: Path) -> None:
    # Given
    fd = os.open(tmp_path / "output", os.O_CREAT | os.O_WRONLY, 0o600)
    io = ControlledWrite()
    writer = open_progress_writer(fd, write=io.write, close_fd=io.close)
    assert writer is not None

    # When
    try:
        result = writer("x" * (MAX_MESSAGE_BYTES + 1))
        writer.close()
        assert io.closed.wait(5)
    finally:
        io.release.set()
        writer.close()
        os.close(fd)

    # Then
    assert result == "dropped"
    assert io.messages == []


def test_start_failure_closes_only_the_owned_duplicate(tmp_path: Path) -> None:
    # Given
    fd = os.open(tmp_path / "output", os.O_CREAT | os.O_WRONLY, 0o600)
    closed: list[int] = []

    class RefuseStart(threading.Thread):
        @override
        def start(self) -> None:
            raise RuntimeError("no worker")

    def close(target: int) -> None:
        closed.append(target)
        os.close(target)

    # When
    try:
        writer = open_progress_writer(
            fd, close_fd=close, thread_factory=lambda target: RefuseStart(target=target)
        )
        os.write(fd, b"caller")
    finally:
        os.close(fd)

    # Then
    assert writer is None
    assert len(closed) == 1 and closed[0] != fd
    assert (tmp_path / "output").read_bytes() == b"caller"


class DelayedFileWrite(ControlledWrite):
    """Delay one real descriptor write until the caller releases it."""

    @override
    def write(self, fd: int, data: bytes) -> int:
        super().write(fd, data)
        return os.write(fd, data)


def test_delayed_write_uses_owned_descriptor_after_caller_reuses_fd(
    tmp_path: Path,
) -> None:
    # Given
    first, second = tmp_path / "first", tmp_path / "second"
    fd = os.open(first, os.O_CREAT | os.O_WRONLY, 0o600)
    io = DelayedFileWrite()
    writer = open_progress_writer(fd, write=io.write, close_fd=io.close)
    assert writer is not None
    reused: int | None = None
    source_open = True

    # When
    try:
        assert writer("original") == "accepted" and io.started.wait(5)
        writer.close()
        source_open = False
        reused = reuse_descriptor(fd, second)
        io.release.set()
        assert io.closed.wait(5)
        os.write(reused, b"new")
    finally:
        io.release.set()
        writer.close()
        if reused is not None:
            os.close(reused)
        elif source_open:
            os.close(fd)

    # Then
    assert first.read_bytes() == b"original"
    assert second.read_bytes() == b"new"


def test_start_error_after_worker_started_leaves_close_to_worker(
    tmp_path: Path,
) -> None:
    # Given
    fd = os.open(tmp_path / "output", os.O_CREAT | os.O_WRONLY, 0o600)
    closed = threading.Event()
    closed_fds: list[int] = []

    class StartThenFail(threading.Thread):
        @override
        def start(self) -> None:
            super().start()
            raise RuntimeError("start interrupted")

    def close(target: int) -> None:
        closed_fds.append(target)
        os.close(target)
        closed.set()

    # When
    try:
        writer = open_progress_writer(
            fd,
            close_fd=close,
            thread_factory=lambda target: StartThenFail(target=target),
        )
        assert closed.wait(5)
        os.write(fd, b"caller")
    finally:
        os.close(fd)

    # Then
    assert writer is None
    assert len(closed_fds) == 1 and closed_fds[0] != fd
    assert (tmp_path / "output").read_bytes() == b"caller"


def reuse_descriptor(fd: int, path: Path) -> int:
    """Close a caller descriptor and allocate its number for another file."""
    os.close(fd)
    replacement = os.open(path, os.O_CREAT | os.O_WRONLY, 0o600)
    assert replacement == fd
    return replacement
