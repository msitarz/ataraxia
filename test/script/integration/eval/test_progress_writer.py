# SPDX-License-Identifier: Apache-2.0
"""Real file, pipe, and terminal progress output through an owned descriptor."""

import fcntl
import os
from pathlib import Path
import pty
import select
import threading

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
