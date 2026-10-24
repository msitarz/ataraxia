# SPDX-License-Identifier: Apache-2.0
"""Disposable subprocess behaviors for native process-supervisor tests."""

import argparse
import os
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
    parser.add_argument("--burst-bytes", type=int, default=0)
    parser.add_argument("--dispatch-marker")
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


def write_dispatch_marker(args: argparse.Namespace) -> None:
    if args.dispatch_marker is not None:
        with open(args.dispatch_marker, "w", encoding="utf-8"):
            pass


def run_mode(args: argparse.Namespace) -> int:
    emit_output(args)
    write_ready_file(args)
    write_dispatch_marker(args)
    if args.mode == "sleep":
        time.sleep(30)
    if args.mode == "hold-pipe":
        subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    return args.status


if __name__ == "__main__":
    raise SystemExit(run_mode(parse_args()))
