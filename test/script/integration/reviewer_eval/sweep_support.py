# SPDX-License-Identifier: Apache-2.0
"""Create synthetic sweep evidence through the real evidence store."""

from dataclasses import replace
import json
from pathlib import Path

from script.eval.evidence import create_evidence_store
from script.eval.model import CallRecord, FrozenPlan, RunRecord
from script.eval.runner.adapters import CodexAttemptRequestBuilder
from script.eval.runner.adapters.codex import requested_settings
from script.eval.runner.coordinator.records import settings_digest
from script.eval.runner.ports import CliBinding
from script.process_supervisor import (
    AttemptObservation,
    CapturedOutput,
    CleanupEvidence,
    Completed,
    SignalAttempt,
)
from script.reviewer_eval.context import c_target
from test.script.integration.eval.support import attempt_evidence


def stream(plan: FrozenPlan, position: int, malformed: bool, tool: bool) -> bytes:
    """Build a unique completed synthetic stream with optional boundary violations."""
    target = c_target(plan, plan.calls[position])
    answer = json.dumps([
        {
            "rule_id": target.rule_id,
            "file_id": target.file_id,
            "function_name": target.function_name,
            "judgement": "PASS",
        }
    ])
    if malformed:
        answer = "{"
    events = [
        {"type": "thread.started", "thread_id": f"thread-{position}"},
        {"type": "turn.started"},
        {"type": "error", "message": "Reconnecting... 1/5 (offline)"},
        {
            "type": "item.completed",
            "item": {
                "id": "fallback",
                "type": "error",
                "message": "Falling back from WebSockets to HTTPS transport. offline",
            },
        },
        {
            "type": "item.completed",
            "item": {"id": "answer", "type": "agent_message", "text": answer},
        },
        {"type": "turn.completed"},
    ]
    if tool:
        events.insert(
            4,
            {
                "type": "item.completed",
                "item": {"id": "tool", "type": "command_execution"},
            },
        )
    return b"".join(json.dumps(event).encode() + b"\n" for event in events)


async def saved_sweep(
    root: Path,
    plan: FrozenPlan,
    *,
    invalid: int = 1,
    stderr: bytes = b"Reading additional input from stdin...\n",
    tool: bool = False,
) -> None:
    """Persist 50 safely completed attempts with controlled public outcomes."""
    store = create_evidence_store()
    prepared = await store.create(root, plan)
    cwd = Path("/tmp/ataraxia-eval-synthetic/empty")
    settings = requested_settings(plan.configuration, Path.cwd(), None)
    binding = CliBinding(
        Path("/synthetic/codex"), "codex-cli 0.166.0", "synthetic", settings, None
    )
    builder = CodexAttemptRequestBuilder(invocation_cwd=cwd)
    cleanup = CleanupEvidence(
        "owned", (SignalAttempt("SIGKILL", "no_target", None),), "reaped", None
    )
    calls: list[CallRecord] = []
    for planned in plan.calls:
        effective = builder.build(plan, planned, binding, prepared, plan.configuration)
        output = stream(
            plan,
            planned.position,
            planned.position < invalid,
            tool and planned.position == 0,
        )
        evidence = replace(
            attempt_evidence(),
            request=effective.request,
            outcome=Completed(
                AttemptObservation(CapturedOutput(output, stderr), 1.0, cleanup), 0
            ),
        )
        attempt = await store.record_attempt(
            plan.run_id, effective.call_id, planned.position, 1, evidence, None
        )
        sources = tuple(plan.snapshots[i] for i in planned.context_indices)
        calls.append(
            CallRecord(
                run_id=plan.run_id,
                call_id=effective.call_id,
                position=planned.position,
                state="complete",
                source_paths=tuple(s.repository_path for s in sources),
                source_sha256=tuple(s.content_sha256 for s in sources),
                boundary_bytes_hex=tuple(b.hex() for b in plan.boundary_bytes),
                prompt_sha256=planned.prompt_sha256,
                model=planned.model,
                effort=planned.effort,
                effective_settings_sha256=settings_digest(settings),
                attempts=(attempt,),
            )
        )
    await store.finalize(
        RunRecord(
            run_id=plan.run_id,
            repository_root=str(plan.repository_root),
            head_commit=plan.head_commit,
            state="complete",
            runner_version="synthetic",
            codex_path=str(binding.executable_path),
            cli_version=binding.cli_version,
            effective_settings=settings,
            calls=tuple(calls),
        )
    )
