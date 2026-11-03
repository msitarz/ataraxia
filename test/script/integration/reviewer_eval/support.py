# SPDX-License-Identifier: Apache-2.0
"""Synthetic initial A/B evidence retained through the real store."""

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

from script.eval.evidence import create_evidence_store
from script.eval.model import (
    CallRecord,
    DirectoryOption,
    FrozenInputs,
    FrozenPlan,
    HarnessConfig,
    RunRecord,
    SourceSnapshot,
)
from script.eval.plan import PurePlanBuilder
from script.eval.runner.adapters import CodexAttemptRequestBuilder
from script.eval.runner.adapters.codex import (
    INVOCATION_PROFILE,
    PROFILE_DIGEST,
    PROFILE_SETTING,
)
from script.eval.runner.coordinator.records import settings_digest
from script.eval.runner.ports import CliBinding
from script.process_supervisor import (
    AttemptObservation,
    CapturedOutput,
    CleanupEvidence,
    Completed,
    SignalAttempt,
)
from script.reviewer_eval.context import CASES, CORPUS, SHARED
from test.script.integration.eval.support import attempt_evidence


def plan(*, repeat: bool = False) -> FrozenPlan:
    """Construct a tiny frozen A/B-shaped plan with no external source reads."""
    case = next(iter(CASES))
    bundle = (
        b"Context:\n\n--- r1/dispatch.py.txt (original lines 1-1) ---\nfirst\n"
        b"\n--- r3/planning.py.txt (original lines 1-1) ---\nsecond\n"
        b"\n--- r4/ledger.py.txt (original lines 1-1) ---\nthird\n"
    )
    entries = (
        (SHARED, b"shared"),
        (case, b"Rules:\n\n--- R1 ---\na\n\n--- R3 ---\nb\n\n--- R4 ---\nc\n"),
        (CORPUS, bundle),
    )
    snapshots = tuple(
        SourceSnapshot(
            directory_position=i * 2,
            repository_path=path,
            commit_blob_sha="blob",
            content_sha256=sha256(content).hexdigest(),
            content=content,
        )
        for i, (path, content) in enumerate(entries)
    )
    config = HarnessConfig(
        ordered_options=tuple(
            DirectoryOption(position=i * 2, path=Path(path).parent)
            for i, (path, _) in enumerate(entries)
        ),
        models=("model", "model") if repeat else ("model",),
        efforts=("low",),
        concurrency=1,
        output_directory=Path("run"),
        dry_run=False,
        timeout_seconds=5.0,
        cleanup_timeout_seconds=2.0,
        grace_seconds=0.0,
        output_limit_bytes=10000,
        instructions_file_path=None,
    )
    return PurePlanBuilder("run").plan(
        FrozenInputs(Path("/unused"), "head", snapshots, None), config
    )


def transcript(response: dict[str, object], thread: str = "thread") -> bytes:
    """Build a single synthetic successful transcript."""
    events = [
        {"type": "thread.started", "thread_id": thread},
        {"type": "turn.started"},
        {
            "type": "item.completed",
            "item": {
                "id": "item",
                "type": "agent_message",
                "text": json.dumps(response),
            },
        },
        {"type": "turn.completed", "usage": {"future": True}},
    ]
    return b"".join(json.dumps(event).encode() + b"\n" for event in events)


async def create_run(
    root: Path,
    *,
    response: dict[str, object] | None = None,
    status: int = 0,
    finalize: bool = True,
    invocation_cwd: Path | None = None,
) -> RunRecord:
    """Persist a controlled plan, process and final summary through the real store."""
    frozen = plan()
    store = create_evidence_store()
    prepared = await store.create(root, frozen)
    settings = (
        ()
        if invocation_cwd is None
        else (
            (PROFILE_SETTING, INVOCATION_PROFILE),
            ("invocation_profile_sha256", PROFILE_DIGEST),
        )
    )
    binding = CliBinding(Path("/synthetic/codex"), None, "synthetic", settings, None)
    effective = CodexAttemptRequestBuilder(invocation_cwd=invocation_cwd).build(
        frozen, frozen.calls[0], binding, prepared, frozen.configuration
    )
    output = transcript(
        response if response is not None else {"complete": True, "findings": []}
    )
    cleanup = CleanupEvidence(
        "owned", (SignalAttempt("SIGKILL", "no_target", None),), "reaped", None
    )
    evidence = replace(
        attempt_evidence(),
        request=effective.request,
        outcome=Completed(
            AttemptObservation(CapturedOutput(output, b""), 1.0, cleanup), status
        ),
    )
    attempt = await store.record_attempt("run", effective.call_id, 0, 1, evidence, None)
    planned = frozen.calls[0]
    call = CallRecord(
        run_id="run",
        call_id=effective.call_id,
        position=0,
        state="complete" if status == 0 else "failed",
        source_paths=tuple(s.repository_path for s in frozen.snapshots),
        source_sha256=tuple(s.content_sha256 for s in frozen.snapshots),
        boundary_bytes_hex=tuple(b.hex() for b in frozen.boundary_bytes),
        prompt_sha256=planned.prompt_sha256,
        model=planned.model,
        effort=planned.effort,
        effective_settings_sha256=settings_digest(settings),
        attempts=(attempt,),
    )
    record = RunRecord(
        run_id="run",
        repository_root="/unused",
        head_commit="head",
        state="complete",
        runner_version="synthetic",
        codex_path="/synthetic/codex",
        cli_version=None,
        effective_settings=settings,
        calls=(call,),
    )
    if finalize:
        await store.finalize(record)
    return record


def snapshot(root: Path) -> dict[str, tuple[bytes, int]]:
    """Capture bytes and mtimes of all evidence files."""
    return {
        str(p.relative_to(root)): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in root.rglob("*")
        if p.is_file()
    }
