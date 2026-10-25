# SPDX-License-Identifier: Apache-2.0
"""Disposable subprocess behaviors for native process-supervisor tests."""

import argparse
import os
import signal
import subprocess
import sys
import time


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("emit", "sleep", "hold-pipe"))
    parser.add_argument("--stdout", default="")
    parser.add_argument("--stderr", default="")
    parser.add_argument("--status", type=int, default=0)
    parser.add_argument("--ready-file")
    parser.add_argument("--grandchild-file")
    parser.add_argument("--grandchild-ready")
    parser.add_argument("--burst-bytes", type=int, default=0)
    parser.add_argument("--dispatch-marker")
    parser.add_argument(
        "--term-mode", choices=("exit", "ignore", "burst", "hold", "close-streams")
    )
    parser.add_argument("--term-marker")
    parser.add_argument(
        "--term-burst-stream", choices=("stdout", "stderr"), default="stdout"
    )
    return parser.parse_args()


def emit_output(args: argparse.Namespace) -> None:
    sys.stdout.buffer.write(bytes.fromhex(args.stdout))
    sys.stdout.buffer.flush()
    sys.stderr.buffer.write(bytes.fromhex(args.stderr))
    sys.stderr.buffer.flush()
    if args.burst_bytes:
        sys.stdout.buffer.write(b"partial\n" * args.burst_bytes)
        sys.stdout.buffer.flush()


def write_ready_file(args: argparse.Namespace) -> None:
    if args.ready_file is not None:
        with open(args.ready_file, "w", encoding="utf-8") as ready:
            ready.write(str(os.getpid()))


def write_grandchild_file(args: argparse.Namespace, pid: int) -> None:
    if args.grandchild_file is not None:
        with open(args.grandchild_file, "w", encoding="utf-8") as grandchild:
            grandchild.write(str(pid))


def write_dispatch_marker(args: argparse.Namespace) -> None:
    if args.dispatch_marker is not None:
        with open(args.dispatch_marker, "w", encoding="utf-8"):
            pass


def install_term_handler(args: argparse.Namespace) -> None:
    if args.term_mode == "ignore":
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    elif args.term_mode in {"burst", "hold", "close-streams"}:

        def finish_on_term(_signum: int, _frame: object) -> None:
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            if args.term_mode == "burst":
                stream = (
                    sys.stdout.buffer
                    if args.term_burst_stream == "stdout"
                    else sys.stderr.buffer
                )
                stream.write(b"discarded" * 524_288)
                stream.flush()
            if args.term_marker is not None:
                with open(args.term_marker, "w", encoding="utf-8"):
                    pass
            if args.term_mode == "close-streams":
                os.close(sys.stdout.fileno())
                os.close(sys.stderr.fileno())
            if args.term_mode == "burst":
                raise SystemExit(0)

        signal.signal(signal.SIGTERM, finish_on_term)


def launch_pipe_holder(args: argparse.Namespace) -> None:
    ready_path = args.grandchild_ready
    grandchild_args = [
        sys.executable,
        str(__file__),
        "sleep",
        "--term-mode",
        "ignore",
    ]
    if ready_path is not None:
        grandchild_args.extend(("--ready-file", ready_path))
    grandchild = subprocess.Popen(grandchild_args)
    write_grandchild_file(args, grandchild.pid)
    if ready_path is not None:
        deadline = time.monotonic() + 2.0
        while not os.path.exists(ready_path) and time.monotonic() < deadline:
            time.sleep(0.005)


def run_mode(args: argparse.Namespace) -> int:
    emit_output(args)
    install_term_handler(args)
    write_ready_file(args)
    write_dispatch_marker(args)
    if args.mode == "sleep":
        time.sleep(30)
    if args.mode == "hold-pipe":
        launch_pipe_holder(args)
    return args.status


if __name__ == "__main__":
    raise SystemExit(run_mode(parse_args()))
