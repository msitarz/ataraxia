# SPDX-License-Identifier: Apache-2.0
"""Leave a session-independent child blocked after its wrapper is killed."""

from pathlib import Path
import subprocess
import sys
import time


def child(gate: Path, done: Path, started: Path) -> None:
    started.write_text("ready\n")
    with gate.open("rb") as stream:
        stream.read(1)
    with done.open("wb") as stream:
        stream.write(b"stopped")


def main() -> None:
    mode = sys.argv[1]
    gate, pid_path, done, started = map(Path, sys.argv[2:6])
    if mode == "child":
        child(gate, done, started)
        return
    descendant = subprocess.Popen(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "child",
            str(gate),
            str(pid_path),
            str(done),
            str(started),
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    pid_path.write_text(str(descendant.pid))
    deadline = time.monotonic() + 10
    while not started.exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    if not started.exists():
        raise TimeoutError("descendant did not start")
    sys.stdout.write("descendant-started\n")
    sys.stdout.flush()
    sys.stdin.buffer.read(1)


if __name__ == "__main__":
    main()
