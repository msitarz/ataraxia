# SPDX-License-Identifier: Apache-2.0
"""Saved reviewer reporting with real evidence persistence and synthetic inputs."""

from dataclasses import replace
import json
import os
from pathlib import Path
import shutil

import pytest

from script.eval.evidence import create_evidence_store
from script.eval.model import (
    CallRecord,
    RunRecord,
)
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
from script.reviewer_eval.report import inspect_run
from test.script.integration.eval.support import attempt_evidence
from test.script.integration.reviewer_eval.support import (
    create_run,
    plan,
    snapshot,
    transcript,
)


async def test_complete_saved_run_and_evidence_unchanged(tmp_path: Path):
    # Given
    root = tmp_path / "run"
    await create_run(root)
    before = snapshot(root)

    # When
    result = inspect_run(root)
    assert result.counts is not None

    # Then
    assert result.planned_count == 1
    assert result.counts.model_dump() == {
        "complete": 1,
        "incomplete": 0,
        "invalid": 0,
        "failed": 0,
        "not_started": 0,
    }
    assert result.calls[0].selected_attempt == 1
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
    assert result.counts is not None

    # Then
    assert result.calls[0].state == expected
    assert result.counts.complete == 0


async def test_missing_summary_preserves_unknown_execution(tmp_path: Path):
    # Given
    root = tmp_path / "run"
    await create_run(root, finalize=False)

    # When
    result = inspect_run(root)
    assert result.counts is not None

    # Then
    assert result.planned_count == 1
    assert result.counts.incomplete == 1
    assert result.counts.not_started == 0
    assert len(result.calls[0].attempts) == 1


async def test_extra_artifact_invalidates_known_inventory(tmp_path: Path):
    # Given
    root = tmp_path / "run"
    await create_run(root)
    (root / "attempts" / "foreign.json").write_text("{}")

    # When
    result = inspect_run(root)
    assert result.counts is not None

    # Then
    assert result.planned_count == 1
    assert result.counts.invalid == 1


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
    assert result.counts is not None

    # Then
    assert calls[0].call_id == calls[1].call_id
    assert result.counts.complete == 2
    assert [c.thread_id for c in result.calls] == ["thread-0", "thread-1"]


def watch_reads(monkeypatch: pytest.MonkeyPatch) -> tuple[list[str], list[Path]]:
    """Observe descriptor and pathlib byte reads during inspection."""
    opened: list[str] = []
    original_open = os.open

    def watch(
        path: str | bytes | os.PathLike[str] | os.PathLike[bytes],
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        opened.append(os.fsdecode(path))
        return original_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "open", watch)
    read_paths: list[Path] = []
    original_read = Path.read_bytes

    def watch_read(path: Path) -> bytes:
        read_paths.append(path)
        return original_read(path)

    monkeypatch.setattr(Path, "read_bytes", watch_read)

    return opened, read_paths


async def test_symlinked_attempts_cannot_read_external_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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

    opened, read_paths = watch_reads(monkeypatch)

    # When
    result = inspect_run(root)
    assert result.counts is not None

    # Then
    assert result.counts.invalid == 1
    assert str(external) not in opened
    assert external.name not in opened
    assert external not in read_paths
    assert (
        external.read_bytes(),
        external.stat().st_mtime_ns,
        external.stat().st_atime_ns,
    ) == before


async def test_untrusted_stream_reference_cannot_read_external_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
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

    opened, read_paths = watch_reads(monkeypatch)

    # When
    result = inspect_run(root)
    assert result.counts is not None

    # Then
    assert result.counts.invalid == 1
    assert str(external) not in opened
    assert external.name not in opened
    assert external not in read_paths
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
    assert result.counts is not None

    # Then
    assert result.calls[0].state == "invalid"
    assert result.calls[0].selected_attempt is None
    assert len(result.calls[0].attempts) == 2


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
    assert result.counts is not None

    # Then
    assert result.calls[0].state == "incomplete"
    assert [f.model_dump(mode="json") for f in result.calls[0].findings] == [
        finding | {"corrections": []}
    ]


@pytest.mark.parametrize(
    "contents",
    [b"{", b"[" * 3000 + b"0" + b"]" * 3000],
    ids=["malformed", "deeply-nested"],
)
async def test_bad_plan_has_unknown_inventory(tmp_path: Path, contents: bytes) -> None:
    # Given
    root = tmp_path / "run"
    await create_run(root)
    (root / "plan.json").write_bytes(contents)

    # When
    result = inspect_run(root)

    # Then
    assert result.evidence_state == "invalid"
    assert result.planned_count is None
    assert result.counts is None


@pytest.mark.parametrize(
    "artifact", ["run.json", "stdout"], ids=["summary", "transcript"]
)
async def test_deep_json_is_reported_invalid(tmp_path: Path, artifact: str) -> None:
    # Given
    root = tmp_path / "run"
    record = await create_run(root)
    stdout = record.calls[0].attempts[0].stdout_artifact
    assert stdout is not None
    target = root / "run.json" if artifact == "run.json" else Path(stdout)
    target.write_bytes(b"[" * 3000 + b"0" + b"]" * 3000)

    # When
    result = inspect_run(root)

    # Then
    assert result.planned_count == 1
    assert result.counts is not None
    assert result.counts.invalid == 1


@pytest.mark.parametrize("field", ["prompt", "snapshot"], ids=["prompt", "snapshot"])
async def test_corrupted_plan_bytes_never_count_coverage(
    tmp_path: Path, field: str
) -> None:
    # Given
    root = tmp_path / "run"
    await create_run(root)
    path = root / "plan.json"
    data = json.loads(path.read_bytes())
    if field == "prompt":
        data["calls"][0]["prompt_sha256"] = "bad"
    else:
        data["snapshots"][0]["content_sha256"] = "bad"
    path.write_text(json.dumps(data))

    # When
    result = inspect_run(root)

    # Then
    assert result.evidence_state == "invalid"
    assert result.planned_count is None


async def test_attempt_record_mismatch_invalidates_known_call(tmp_path: Path) -> None:
    # Given
    root = tmp_path / "run"
    record = await create_run(root)
    stdout = record.calls[0].attempts[0].stdout_artifact
    assert stdout is not None
    metadata = Path(stdout).with_suffix(".json")
    data = json.loads(metadata.read_bytes())
    data["exit_status"] = 9
    metadata.write_text(json.dumps(data))

    # When
    result = inspect_run(root)

    # Then
    assert result.counts is not None
    assert result.counts.invalid == 1
    assert "attempt metadata mismatch" in (result.diagnostic or "")


async def test_unsafe_cleanup_followed_by_success_is_invalid(tmp_path: Path) -> None:
    # Given
    root = tmp_path / "run"
    record = await create_run(root)
    call = record.calls[0]
    first = call.attempts[0]
    assert first.stdout_artifact is not None
    metadata = Path(first.stdout_artifact).with_suffix(".json")
    second = first.model_copy(
        update={
            "attempt_number": 2,
            "stdout_artifact": str(metadata.with_name("attempt-2.stdout")),
            "stderr_artifact": str(metadata.with_name("attempt-2.stderr")),
        }
    )
    first = first.model_copy(update={"exit_status": 1, "cleanup": None})
    metadata.write_text(first.model_dump_json())
    metadata.with_name("attempt-2.json").write_text(second.model_dump_json())
    metadata.with_name("attempt-2.stdout").write_bytes(
        transcript({"complete": True, "findings": []})
    )
    metadata.with_name("attempt-2.stderr").write_bytes(b"")
    changed = call.model_copy(update={"attempts": (first, second)})
    (root / "run.json").write_text(
        record.model_copy(update={"calls": (changed,)}).model_dump_json()
    )

    # When
    result = inspect_run(root)

    # Then
    assert result.counts is not None
    assert result.counts.invalid == 1
    assert "unsafe cleanup" in (result.diagnostic or "")


async def test_missing_binding_preserves_explicit_not_started(tmp_path: Path) -> None:
    # Given
    root = tmp_path / "run"
    record = await create_run(root)
    shutil.rmtree(root / "attempts")
    call = record.calls[0].model_copy(update={"state": "not_started", "attempts": ()})
    (root / "run.json").write_text(
        record.model_copy(
            update={"codex_path": None, "state": "incomplete", "calls": (call,)}
        ).model_dump_json()
    )

    # When
    result = inspect_run(root)

    # Then
    assert result.evidence_state == "incomplete"
    assert result.counts is not None
    assert result.counts.not_started == 1


async def test_global_mismatch_invalidates_every_known_position(tmp_path: Path) -> None:
    # Given
    root = tmp_path / "run"
    await create_run(root)
    (root / "plan.json").write_text(plan(repeat=True).model_dump_json())

    # When
    result = inspect_run(root)

    # Then
    assert result.planned_count == 2
    assert result.counts is not None
    assert result.counts.invalid == 2
    assert [call.position for call in result.calls] == [0, 1]


async def test_missing_binding_does_not_credit_attempted_call(tmp_path: Path) -> None:
    # Given
    root = tmp_path / "run"
    record = await create_run(root)
    (root / "run.json").write_text(
        record.model_copy(update={"codex_path": None}).model_dump_json()
    )

    # When
    result = inspect_run(root)

    # Then
    assert result.evidence_state == "incomplete"
    assert result.counts is not None
    assert result.counts.incomplete == 1
    assert result.calls[0].selected_attempt is None
    assert len(result.calls[0].attempts) == 1


@pytest.mark.parametrize("artifact", ["plan", "run", "stdout"])
async def test_decoder_limit_produces_invalid_report(
    tmp_path: Path, artifact: str
) -> None:
    # Given
    root = tmp_path / "run"
    record = await create_run(root)
    stdout = record.calls[0].attempts[0].stdout_artifact
    assert stdout is not None
    paths = {
        "plan": root / "plan.json",
        "run": root / "run.json",
        "stdout": Path(stdout),
    }
    paths[artifact].write_bytes(b"[" * 400_000 + b"]" * 400_000)

    # When
    result = inspect_run(root)

    # Then
    if artifact == "plan":
        assert result.evidence_state == "invalid"
        assert result.planned_count is None
    else:
        assert result.planned_count == 1
        assert result.counts is not None
        assert result.counts.invalid == 1
