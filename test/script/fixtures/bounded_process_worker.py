# SPDX-License-Identifier: Apache-2.0
"""Run the supervisor in a separate process for signal-boundary checks."""

import json
import os
from pathlib import Path
import signal
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from script.process_supervisor import run_bounded


def main() -> int:
    fixture, marker, ready_socket = map(Path, sys.argv[1:])
    previous_term = signal.getsignal(signal.SIGTERM)
    previous_int = signal.getsignal(signal.SIGINT)
    try:
        result = run_bounded(
            [
                sys.executable,
                str(fixture),
                "child",
                str(marker),
                "hold",
                "normal",
                "socket",
                str(ready_socket),
            ],
            timeout_seconds=30,
            cleanup_seconds=2,
            output_limit_bytes=1024,
            env={
                **os.environ,
                "PYTHONPATH": str(Path(__file__).resolve().parents[3]),
            },
        )
    except KeyboardInterrupt as error:
        sys.stdout.write(
            json.dumps({
                "exception": type(error).__name__,
                "notes": getattr(error, "__notes__", []),
                "term_restored": signal.getsignal(signal.SIGTERM) == previous_term,
                "int_restored": signal.getsignal(signal.SIGINT) == previous_int,
            })
            + "\n"
        )
        return 23
    sys.stdout.write(
        json.dumps({
            "stop_reason": result.stop_reason,
            "cancellation_signal": result.cancellation_signal,
            "cleanup_complete": result.cleanup_complete,
            "term_restored": signal.getsignal(signal.SIGTERM) == previous_term,
            "int_restored": signal.getsignal(signal.SIGINT) == previous_int,
        })
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
