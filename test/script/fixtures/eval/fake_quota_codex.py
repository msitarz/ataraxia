#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Synthetic Codex executable with local invocation-correlated quota rows."""

from datetime import UTC, datetime
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

if sys.argv[1:] == ["--version"]:
    sys.stdout.write(
        "codex-cli " + os.environ.get("FAKE_CLI_VERSION", "0.164.0") + "\n"
    )
    raise SystemExit(0)

state = Path(os.environ["FAKE_QUOTA_STATE"])
counts = json.loads(state.read_text()) if state.exists() else {"eval": 0, "probe": 0}
kind = "probe" if "gpt-6-luna" in sys.argv else "eval"
counts[kind] += 1
state.write_text(json.dumps(counts))
if kind == "eval":
    with state.with_suffix(".prompts").open("a") as prompts:
        prompts.write(json.dumps(sys.argv[-1]) + "\n")
thread = str(uuid4())
now = datetime.now(UTC)
sessions = Path(os.environ["CODEX_HOME"]) / "sessions" / now.strftime("%Y/%m/%d")
sessions.mkdir(parents=True, exist_ok=True)
metadata = {
    "id": thread,
    "session_id": thread,
    "model_provider": "openai",
    "cli_version": os.environ.get("FAKE_CLI_VERSION", "0.164.0"),
    "creator_account_id": "fixture-account",
    "creator_user_id": "fixture-user",
}
mode = os.environ.get("FAKE_QUOTA_MODE", "")
if mode == "wrong-version":
    metadata["cli_version"] = "0.163.0"
if mode == "mismatch" and kind == "probe":
    metadata["creator_account_id"] = "another-account"
rows: list[dict[str, object]] = [{"type": "session_meta", "payload": metadata}]
exhausted = counts[kind] == 1
if not exhausted or mode == "out-of-order":
    rows.append({
        "type": "event_msg",
        "timestamp": now.isoformat(),
        "ordinal": 1,
        "payload": {
            "type": "token_count",
            "rate_limits": {
                "limit_id": "codex",
                "primary": {"used_percent": 10.0, "window_minutes": 300},
                "secondary": {"used_percent": 20.0, "window_minutes": 10080},
                "credits": {"has_credits": False, "unlimited": False, "balance": "0"},
                "individual_limit": None,
                "spend_control_reached": None,
                "rate_limit_reached_type": None,
            },
        },
    })
if mode == "out-of-order":
    rows.append(rows[-1])
path = sessions / f"rollout-{now.strftime('%Y-%m-%dT%H-%M-%S')}-{thread}.jsonl"
if mode != "missing-session":
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
sys.stdout.write(json.dumps({"type": "thread.started", "thread_id": thread}) + "\n")
if exhausted:
    if mode == "stderr":
        sys.stderr.write("unexpected stderr\n")
    message = (
        "You\u2019ve hit your usage limit. Upgrade to Pro "
        "(https://chatgpt.com/explore/pro), visit https://chatgpt.com/settings/usage "
        "to purchase more credits or try again at 1:18 PM."
    )
    sys.stdout.write(json.dumps({"type": "turn.started"}) + "\n")
    if mode == "extra-event":
        sys.stdout.write(json.dumps({"type": "item.completed"}) + "\n")
    sys.stdout.write(json.dumps({"type": "error", "message": message}) + "\n")
    sys.stdout.write(
        json.dumps({"type": "turn.failed", "error": {"message": message}}) + "\n"
    )
    raise SystemExit(1)
sys.stdout.write(json.dumps({"type": "turn.completed"}) + "\n")
