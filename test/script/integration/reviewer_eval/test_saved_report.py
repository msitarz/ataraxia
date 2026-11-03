# SPDX-License-Identifier: Apache-2.0
"""Saved reviewer reporting with real evidence persistence and synthetic inputs."""

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

import pytest

from script.eval.evidence import create_evidence_store
from script.eval.model import (
    CallRecord,
    DirectoryOption,
    FrozenInputs,
    HarnessConfig,
    RunRecord,
    SourceSnapshot,
)
from script.eval.plan import PurePlanBuilder
from script.eval.runner.adapters import CodexAttemptRequestBuilder
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
from script.reviewer_eval.report import inspect_run
from test.script.integration.eval.support import attempt_evidence


def plan(*, repeat: bool = False):
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
):
    """Persist a controlled plan, process and final summary through the real store."""
    frozen = plan()
    store = create_evidence_store()
    prepared = await store.create(root, frozen)
    binding = CliBinding(Path("/synthetic/codex"), None, "synthetic", (), None)
    effective = CodexAttemptRequestBuilder().build(
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
        effective_settings_sha256=settings_digest(()),
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
        effective_settings=(),
        calls=(call,),
    )
    if finalize:
        await store.finalize(record)
    return record


def snapshot(root: Path):
    """Capture bytes and mtimes of all evidence files."""
    return {
        str(p.relative_to(root)): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in root.rglob("*")
        if p.is_file()
    }


async def test_complete_saved_run_and_evidence_unchanged(tmp_path: Path):
    # Given
    root = tmp_path / "run"
    await create_run(root)
    before = snapshot(root)

    # When
    result = inspect_run(root)

    # Then
    assert result["planned_count"] == 1
    assert result["counts"] == {
        "complete": 1,
        "incomplete": 0,
        "invalid": 0,
        "failed": 0,
        "not_started": 0,
    }
    assert result["calls"][0]["selected_attempt"] == 1
    assert snapshot(root) == before


@pytest.mark.parametrize(
    ("response", "status", "expected"),
    [
        ({"complete": False, "findings": []}, 0, "incomplete"),
        ({"complete": True, "findings": []}, 1, "failed"),
        ({"bad": True}, 0, "invalid"),
    ],
)
async def test_noncomplete_results_never_count_as_complete(
    tmp_path: Path, response: dict[str, object], status: int, expected: str
):
    # Given
    root = tmp_path / "run"
    await create_run(root, response=response, status=status)

    # When
    result = inspect_run(root)

    # Then
    assert result["calls"][0]["state"] == expected
    assert result["counts"]["complete"] == 0


async def test_missing_summary_preserves_unknown_execution(tmp_path: Path):
    # Given
    root = tmp_path / "run"
    await create_run(root, finalize=False)

    # When
    result = inspect_run(root)

    # Then
    assert result["planned_count"] == 1
    assert result["counts"]["incomplete"] == 1
    assert result["counts"]["not_started"] == 0
    assert len(result["calls"][0]["attempts"]) == 1


async def test_extra_artifact_invalidates_known_inventory(tmp_path: Path):
    # Given
    root = tmp_path / "run"
    await create_run(root)
    (root / "attempts" / "foreign.json").write_text("{}")

    # When
    result = inspect_run(root)

    # Then
    assert result["planned_count"] == 1
    assert result["counts"]["invalid"] == 1


async def test_cli_creates_exclusive_report(tmp_path: Path):
    # Given
    root = tmp_path / "run"
    await create_run(root)
    output = tmp_path / "report.json"
    command = [
        sys.executable,
        "-m",
        "script.reviewer_eval",
        str(root),
        "--output",
        str(output),
    ]

    # When
    first = subprocess.run(command, capture_output=True, timeout=10, check=False)
    before = output.read_bytes()
    second = subprocess.run(command, capture_output=True, timeout=10, check=False)

    # Then
    assert first.returncode == 0
    assert second.returncode == 1
    assert output.read_bytes() == before


async def test_repeated_effective_identity_keeps_separate_fresh_calls(
    tmp_path: Path,
) -> None:
    # Given
    root = tmp_path / "run"
    frozen = plan(repeat=True)
    store = create_evidence_store()
    prepared = await store.create(root, frozen)
    binding = CliBinding(Path("/synthetic/codex"), None, "synthetic", (), None)
    calls = []
    for planned in frozen.calls:
        effective = CodexAttemptRequestBuilder().build(
            frozen, planned, binding, prepared, frozen.configuration
        )
        cleanup = CleanupEvidence(
            "owned", (SignalAttempt("SIGKILL", "no_target", None),), "reaped", None
        )
        output = transcript(
            {"complete": True, "findings": []}, f"thread-{planned.position}"
        )
        evidence = replace(
            attempt_evidence(),
            request=effective.request,
            outcome=Completed(
                AttemptObservation(CapturedOutput(output, b""), 1.0, cleanup), 0
            ),
        )
        attempt = await store.record_attempt(
            "run", effective.call_id, planned.position, 1, evidence, None
        )
        calls.append(
            CallRecord(
                run_id="run",
                call_id=effective.call_id,
                position=planned.position,
                state="complete",
                source_paths=tuple(s.repository_path for s in frozen.snapshots),
                source_sha256=tuple(s.content_sha256 for s in frozen.snapshots),
                boundary_bytes_hex=tuple(b.hex() for b in frozen.boundary_bytes),
                prompt_sha256=planned.prompt_sha256,
                model=planned.model,
                effort=planned.effort,
                effective_settings_sha256=settings_digest(()),
                attempts=(attempt,),
            )
        )
    await store.finalize(
        RunRecord(
            run_id="run",
            repository_root="/unused",
            head_commit="head",
            state="complete",
            runner_version="synthetic",
            codex_path="/synthetic/codex",
            cli_version=None,
            effective_settings=(),
            calls=tuple(calls),
        )
    )

    # When
    result = inspect_run(root)

    # Then
    assert calls[0].call_id == calls[1].call_id
    assert result["counts"]["complete"] == 2
    assert [c["thread_id"] for c in result["calls"]] == ["thread-0", "thread-1"]


async def test_symlinked_attempts_cannot_read_external_file(tmp_path: Path) -> None:
    # Given
    root = tmp_path / "run"
    await create_run(root)
    external = tmp_path / "external"
    external.write_text("private")
    before = (
        external.read_bytes(),
        external.stat().st_mtime_ns,
        external.stat().st_atime_ns,
    )
    (root / "attempts" / "foreign.json").symlink_to(external)

    # When
    result = inspect_run(root)

    # Then
    assert result["counts"]["invalid"] == 1
    assert (
        external.read_bytes(),
        external.stat().st_mtime_ns,
        external.stat().st_atime_ns,
    ) == before


async def test_untrusted_stream_reference_cannot_read_external_file(
    tmp_path: Path,
) -> None:
    # Given
    root = tmp_path / "run"
    record = await create_run(root)
    external = tmp_path / "external"
    external.write_text("private")
    before = (
        external.read_bytes(),
        external.stat().st_mtime_ns,
        external.stat().st_atime_ns,
    )
    run_path = root / "run.json"
    data = json.loads(run_path.read_bytes())
    data["calls"][0]["attempts"][0]["stdout_artifact"] = str(external)
    artifact = record.calls[0].attempts[0].stdout_artifact
    assert artifact is not None
    metadata = Path(artifact).with_suffix(".json")
    metadata.write_text(json.dumps(data["calls"][0]["attempts"][0]))
    run_path.write_text(json.dumps(data))

    # When
    result = inspect_run(root)

    # Then
    assert result["counts"]["invalid"] == 1
    assert (
        external.read_bytes(),
        external.stat().st_mtime_ns,
        external.stat().st_atime_ns,
    ) == before


async def test_later_failed_retry_never_uses_earlier_success(tmp_path: Path) -> None:
    # Given
    root = tmp_path / "run"
    record = await create_run(root)
    call = record.calls[0]
    attempt = call.attempts[0]
    assert attempt.stdout_artifact is not None
    metadata = Path(attempt.stdout_artifact).with_suffix(".json")
    second = attempt.model_copy(
        update={
            "attempt_number": 2,
            "exit_status": 1,
            "stdout_artifact": str(metadata.with_name("attempt-2.stdout")),
            "stderr_artifact": str(metadata.with_name("attempt-2.stderr")),
        }
    )
    metadata.with_name("attempt-2.json").write_text(second.model_dump_json())
    metadata.with_name("attempt-2.stdout").write_bytes(
        transcript({"complete": True, "findings": []})
    )
    metadata.with_name("attempt-2.stderr").write_bytes(b"")
    changed = call.model_copy(update={"state": "failed", "attempts": (attempt, second)})
    (root / "run.json").write_text(
        record.model_copy(update={"calls": (changed,)}).model_dump_json()
    )

    # When
    result = inspect_run(root)

    # Then
    assert result["calls"][0]["state"] == "failed"
    assert result["calls"][0]["selected_attempt"] is None
    assert len(result["calls"][0]["attempts"]) == 2


async def test_valid_finding_is_retained_against_frozen_source(tmp_path: Path) -> None:
    # Given
    root = tmp_path / "run"
    finding = {
        "rule_id": "R1",
        "file_id": "r1/dispatch.py.txt",
        "start_line": 1,
        "end_line": 1,
        "quote": "first",
        "explanation": "explanation",
        "consequence": "consequence",
        "severity": "major",
    }
    await create_run(root, response={"complete": False, "findings": [finding]})

    # When
    result = inspect_run(root)

    # Then
    assert result["calls"][0]["state"] == "incomplete"
    assert result["calls"][0]["findings"] == [finding | {"corrections": []}]
