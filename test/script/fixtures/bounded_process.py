# SPDX-License-Identifier: Apache-2.0
"""Disposable leader and descendant used by process-supervisor tests."""

import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time


def child(
    marker: Path,
    *,
    close_streams: bool,
    resist_term: bool,
    readiness: list[str],
) -> int:
    if resist_term:
        signal.signal(
            signal.SIGTERM, lambda signum, frame: marker.with_suffix(".term").touch()
        )
    if close_streams:
        os.close(1)
        os.close(2)
    marker.write_text(str(os.getpid()), encoding="utf-8")
    if readiness and readiness[0] == "fd":
        os.write(int(readiness[1]), str(os.getpid()).encode())
        os.close(int(readiness[1]))
    elif readiness and readiness[0] == "socket":
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.connect(readiness[1])
            connection.sendall(str(os.getpid()).encode())
    while True:
        time.sleep(1)


def leader(marker: Path, mode: str, exit_code: int) -> int:
    ready_read, ready_write = os.pipe()
    subprocess.Popen(
        [
            sys.executable,
            __file__,
            "child",
            str(marker),
            "close" if mode == "closed" else "hold",
            "resist" if mode == "resist" else "normal",
            "fd",
            str(ready_write),
        ],
        pass_fds=(ready_write,),
    )
    os.close(ready_write)
    child_pid = os.read(ready_read, 64).decode()
    os.close(ready_read)
    if not child_pid:
        return 91
    sys.stdout.write(f"child={child_pid}\n")
    sys.stdout.flush()
    sys.stderr.write("leader-ready\n")
    sys.stderr.flush()
    return exit_code


def burst() -> int:
    sys.stdout.write("O" * 80)
    sys.stdout.flush()
    sys.stderr.write("E" * 80)
    sys.stderr.flush()
    return 0


def tagged(tag: str) -> int:
    sys.stdout.write(f"out:{tag}\n")
    sys.stderr.write(f"err:{tag}\n")
    return 0


def check_stdin() -> int:
    if sys.stdin.buffer.read():
        sys.stdout.write("stdin-data\n")
        return 1
    sys.stdout.write("stdin-eof\n")
    return 0


def gated(marker: Path, readiness_path: str) -> int:
    """Announce readiness and wait for an explicit parent release."""
    marker.write_text(str(os.getpid()), encoding="utf-8")
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.connect(readiness_path)
        connection.sendall(str(os.getpid()).encode())
        if connection.recv(16) != b"exit":
            return 92
    return 0


def main() -> int:
    mode, *args = sys.argv[1:]
    if mode == "child":
        marker = Path(args[0])
        return child(
            marker,
            close_streams=args[1] == "close",
            resist_term=args[2] == "resist",
            readiness=args[3:],
        )
    if mode == "leader":
        return leader(Path(args[1]), args[0], int(args[2]))
    if mode == "burst":
        return burst()
    if mode == "tagged":
        return tagged(args[0])
    if mode == "stdin":
        return check_stdin()
    if mode == "gated":
        return gated(Path(args[0]), args[1])
    raise ValueError(f"unknown fixture mode: {mode}")


if __name__ == "__main__":
    raise SystemExit(main())
