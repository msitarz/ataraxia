# SPDX-License-Identifier: Apache-2.0
"""Run the supervisor in a separate process for signal-boundary checks."""

import asyncio
import json
import os
from pathlib import Path
import signal
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from script.process_supervisor import _CancellationEvent, _cli_with_signals, run_bounded


def main() -> int:
    fixture, marker, ready_socket = map(Path, sys.argv[1:])
    previous_term = signal.getsignal(signal.SIGTERM)
    previous_int = signal.getsignal(signal.SIGINT)
    cancelled = _CancellationEvent()

    async def run() -> dict[str, object]:
        result = await run_bounded(
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
            cancel_event=cancelled,
            env={
                **os.environ,
                "PYTHONPATH": str(Path(__file__).resolve().parents[3]),
            },
        )
        return {
            "stop_reason": result.stop_reason,
            "cancellation_signal": result.cancellation_signal,
            "cleanup_complete": result.cleanup_complete,
        }

    try:
        observation = asyncio.run(_cli_with_signals(run(), cancelled))
    except BaseException as error:
        sys.stdout.write(json.dumps({"exception": type(error).__name__}) + "\n")
        return 23
    observation["term_restored"] = signal.getsignal(signal.SIGTERM) == previous_term
    observation["int_restored"] = signal.getsignal(signal.SIGINT) == previous_int
    sys.stdout.write(json.dumps(observation) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
