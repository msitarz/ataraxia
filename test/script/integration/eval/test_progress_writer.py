# SPDX-License-Identifier: Apache-2.0
"""Real file, pipe, and terminal progress output through an owned descriptor."""

from collections.abc import Callable
import fcntl
import os
from pathlib import Path
import pty
import select
import threading
from typing import override

import pytest

from script.eval.runner.adapters.progress_writer import open_progress_writer


@pytest.mark.parametrize(
    "destination", ["file", "pipe", "tty"], ids=["file", "pipe", "tty"]
)
def test_writer_delivers_to_real_descriptor(tmp_path: Path, destination: str) -> None:
    # Given
    read_fd, target = open_destination(tmp_path, destination)
    original_flags = caller_modes(target)
    written, closed = threading.Event(), threading.Event()

    def write(fd: int, data: bytes) -> int:
        count = os.write(fd, data)
        written.set()
        return count

    def close(fd: int) -> None:
        os.close(fd)
        closed.set()

    writer = open_progress_writer(target, write=write, close_fd=close)
    assert writer is not None

    # When
    try:
        assert writer("progress\n") == "accepted"
        assert written.wait(5)
        writer.close()
        assert closed.wait(5)
        assert caller_modes(target) == original_flags
        data = read_destination(read_fd, destination)
    finally:
        writer.close()
        if target != read_fd:
            os.close(target)
        os.close(read_fd)

    # Then
    assert data in (b"progress\n", b"progress\r\n")


def open_destination(tmp_path: Path, destination: str) -> tuple[int, int]:
    """Open a paired read end and output descriptor for one test destination."""
    if destination == "file":
        fd = os.open(tmp_path / "output", os.O_CREAT | os.O_RDWR, 0o600)
        return fd, fd
    if destination == "pipe":
        return os.pipe()
    return pty.openpty()


def read_destination(fd: int, destination: str) -> bytes:
    """Read one completed message from the real destination."""
    if destination == "file":
        os.lseek(fd, 0, os.SEEK_SET)
    else:
        empty: list[int] = []
        assert select.select([fd], empty, empty, 5)[0]
    return os.read(fd, 100)


def caller_modes(fd: int) -> int:
    """Read mutable caller modes, excluding Darwin's internal written flag."""
    return fcntl.fcntl(fd, fcntl.F_GETFL) & (os.O_NONBLOCK | os.O_APPEND)


def test_delayed_write_stays_on_owned_descriptor_after_caller_reuses_fd(
    tmp_path: Path,
) -> None:
    # Given
    first, second = tmp_path / "first", tmp_path / "second"
    fd = os.open(first, os.O_CREAT | os.O_WRONLY, 0o600)
    io = DelayedWrite()
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


def reuse_descriptor(fd: int, path: Path) -> int:
    """Allocate the caller's descriptor number for another file."""
    os.close(fd)
    replacement = os.open(path, os.O_CREAT | os.O_WRONLY, 0o600)
    assert replacement == fd
    return replacement


class DelayedWrite:
    """Delay a real descriptor write until released by the test."""

    def __init__(self) -> None:
        self.started = threading.Event()
        self.release = threading.Event()
        self.closed = threading.Event()

    def write(self, target: int, data: bytes) -> int:
        self.started.set()
        if not self.release.wait(5):
            raise TimeoutError("test did not release writer")
        return os.write(target, data)

    def close(self, target: int) -> None:
        os.close(target)
        self.closed.set()


def test_late_worker_after_failed_start_cannot_touch_reused_duplicate(
    tmp_path: Path,
) -> None:
    # Given
    original = tmp_path / "original"
    replacement = tmp_path / "replacement"
    fd = os.open(original, os.O_CREAT | os.O_WRONLY, 0o600)
    io = DelayedFailedStart()

    # When
    reused: int | None = None
    try:
        writer = open_progress_writer(
            fd, duplicate=io.duplicate, thread_factory=io.factory
        )
        reused = os.open(replacement, os.O_CREAT | os.O_WRONLY, 0o600)
        assert reused == io.duplicated[0]
        io.release.set()
        assert io.finished.wait(5)
        os.write(reused, b"replacement")
    finally:
        io.release.set()
        if reused is not None:
            os.close(reused)
        os.close(fd)

    # Then
    assert writer is None
    assert original.read_bytes() == b""
    assert replacement.read_bytes() == b"replacement"


class DelayedFailedStart:
    """Delay worker entry after a thread start raises."""

    def __init__(self) -> None:
        self.release = threading.Event()
        self.finished = threading.Event()
        self.duplicated: list[int] = []

    def duplicate(self, source: int) -> int:
        owned = os.dup(source)
        self.duplicated.append(owned)
        return owned

    def factory(self, target: Callable[[], None]) -> threading.Thread:
        class FailAfterStart(threading.Thread):
            @override
            def start(self) -> None:
                super().start()
                raise RuntimeError("start failed")

        def delayed() -> None:
            if self.release.wait(5):
                target()
            self.finished.set()

        return FailAfterStart(target=delayed)
