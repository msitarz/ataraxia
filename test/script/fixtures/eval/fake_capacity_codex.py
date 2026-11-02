#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Synthetic source-shaped capacity failures for standalone runner checks."""

import json
import os
from pathlib import Path
import sys

if sys.argv[1:] == ["--version"]:
    sys.stdout.write("codex-cli 0.164.0\n")
    raise SystemExit(0)


def emit(row: dict[str, object]) -> None:
    """Write one synthetic JSONL event."""
    sys.stdout.write(json.dumps(row) + "\n")


log = Path(os.environ["FAKE_CAPACITY_LOG"])
args = sys.argv[1:]
instruction_setting = next(
    arg for arg in args if arg.startswith("model_instructions_file=")
)
instruction_path = json.loads(instruction_setting.split("=", 1)[1])
with log.open("a") as stream:
    stream.write(
        json.dumps({
            "argv": args,
            "instructions": Path(instruction_path).read_text(),
            "pid": os.getpid(),
        })
        + "\n"
    )
count = len(log.read_text().splitlines())
emit({
    "type": "thread.started",
    "thread_id": "01a1781b-a54f-7763-9f82-74709e5e0fcf",
})
emit({"type": "turn.started"})
if count == 1 or os.environ.get("FAKE_CAPACITY_MODE") == "exhaust":
    if os.environ.get("FAKE_CAPACITY_MODE") == "ambiguous":
        emit({
            "type": "item.completed",
            "item": {"type": "agent_message", "text": "partial"},
        })
    message = "Selected model is at capacity. Please try a different model."
    emit({"type": "error", "message": message})
    emit({"type": "turn.failed", "error": {"message": message}})
    raise SystemExit(1)
emit({"type": "turn.completed"})
