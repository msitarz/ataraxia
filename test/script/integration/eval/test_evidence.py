# SPDX-License-Identifier: Apache-2.0
"""Real-filesystem checks for immutable evidence publication."""

from dataclasses import replace
import json
from pathlib import Path
import subprocess

import pytest

from script.eval.evidence import create_evidence_store
from script.eval.model import (
    FrozenPlan,
    InstructionsSnapshot,
    QuotaProbeEvidence,
    QuotaProbeStarted,
)
from script.process_supervisor import (
    AttemptObservation,
    AttemptRequest,
    CapturedOutput,
    Completed,
)
from test.script.unit.eval.test_evidence import (
    attempt_evidence,
    empty_quota_observation,
    frozen_plan,
    quota_probe_request,
)


async def test_run_setup_is_exclusive_and_persists_configuration_before_dispatch(
    tmp_path: Path,
) -> None:
    """Observe directory exclusion and durable pre-dispatch plan artifacts."""
    # Given
    repository = tmp_path / "context"
    repository.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"],
        cwd=repository,
        check=True,
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repository, check=True)
    (repository / "input.txt").write_text("context")
    subprocess.run(["git", "add", "input.txt"], cwd=repository, check=True)
    subprocess.run(["git", "commit", "-qm", "input"], cwd=repository, check=True)
    plan = FrozenPlan.model_validate(
        frozen_plan().model_dump() | {"repository_root": repository}
    )
    existing = tmp_path / "existing"
    existing.mkdir()
    destination = tmp_path / "run"

    # When
    with pytest.raises(FileExistsError):
        await create_evidence_store().create(existing, plan)
    prepared = await create_evidence_store().create(destination, plan)

    # Then
    assert prepared.plan_artifact.is_file()
    assert (
        json.loads(prepared.plan_artifact.read_text())["head_commit"]
        == plan.head_commit
    )
    with pytest.raises(FileExistsError):
        await create_evidence_store().create(destination, plan)


async def test_run_setup_stages_exact_instruction_bytes(tmp_path: Path) -> None:
    """Retain optional instructions as an exact binary artifact."""
    # Given
    original = tmp_path / "instructions.md"
    content = b"rules\x00\xff\n"
    original.write_bytes(content)
    plan = frozen_plan()
    config = plan.configuration.model_copy(update={"instructions_file_path": original})
    plan = plan.model_copy(
        update={
            "configuration": config,
            "instructions_file": InstructionsSnapshot(
                repository_path="instructions.md",
                commit_blob_sha="blob-id",
                content_sha256="content-hash",
                content=content,
            ),
        }
    )

    # When
    prepared = await create_evidence_store().create(tmp_path / "run", plan)
    original.write_bytes(b"changed")

    # Then
    assert prepared.model_instructions_file is not None
    assert prepared.model_instructions_file.read_bytes() == content


async def test_attempt_records_preserve_raw_streams_and_missing_observations(
    tmp_path: Path,
) -> None:
    """Keep empty, absent, partial, and failed evidence distinct and immutable."""
    # Given
    store = create_evidence_store()
    await store.create(tmp_path / "run", frozen_plan())
    source = attempt_evidence()

    # When
    record = await store.record_attempt("run-1", "call-1", 0, 1, source, None)

    # Then
    assert record.elapsed_basis == "supervisor_observation"
    assert record.argv == source.request.argv
    assert record.stdout_artifact is not None
    assert Path(record.stdout_artifact).read_bytes() == b"out"
    assert record.stderr_artifact is not None
    assert Path(record.stderr_artifact).read_bytes() == b"err"
    persisted = tmp_path / "run" / "attempts" / "call-1" / "attempt-1.json"
    assert json.loads(persisted.read_text())["retry_assessment"] is None


async def test_empty_and_unavailable_streams_remain_distinct(tmp_path: Path) -> None:
    """Observed empty streams get artifacts while absent output stays absent."""
    # Given
    store = create_evidence_store()
    await store.create(tmp_path / "run", frozen_plan())
    original = attempt_evidence()
    assert isinstance(original.outcome, Completed)
    cleanup = original.outcome.observation.cleanup
    empty = replace(
        original,
        outcome=Completed(
            AttemptObservation(CapturedOutput(b"", b""), 1.0, cleanup), 0
        ),
    )
    unavailable = replace(
        original,
        outcome=Completed(AttemptObservation(None, 1.0, cleanup), 0),
    )

    # When
    empty_record = await store.record_attempt("run-1", "call-empty", 0, 1, empty, None)
    absent_record = await store.record_attempt(
        "run-1", "call-absent", 1, 1, unavailable, None
    )

    # Then
    assert empty_record.stdout_artifact is not None
    assert Path(empty_record.stdout_artifact).read_bytes() == b""
    assert empty_record.stderr_artifact is not None
    assert Path(empty_record.stderr_artifact).read_bytes() == b""
    assert absent_record.stdout_artifact is None
    assert absent_record.stderr_artifact is None


async def test_attempt_and_probe_records_preserve_shared_process_artifacts(
    tmp_path: Path,
) -> None:
    """Verify both persisted record types expose the supervised outcomes."""
    # Given
    store = create_evidence_store()
    await store.create(tmp_path / "run", frozen_plan())
    process = attempt_evidence()
    request = quota_probe_request()
    await store.record_quota_probe_event(
        QuotaProbeStarted(kind="started", request=request)
    )

    # When
    settled = await store.record_quota_probe_settled(
        QuotaProbeEvidence(
            request=request,
            process=process,
            quota_state="unknown",
            observation=empty_quota_observation(),
            classification_basis="source unavailable",
        )
    )

    # Then
    assert settled.record.request == request
    assert settled.record.quota_state == "unknown"
    assert settled.record.argv == process.request.argv
    assert settled.record.stdout_artifact is not None
    assert Path(settled.record.stdout_artifact).read_bytes() == b"out"
    assert settled.record.stderr_artifact is not None
    assert Path(settled.record.stderr_artifact).read_bytes() == b"err"
    events = (tmp_path / "run" / "events.jsonl").read_text().splitlines()
    assert [json.loads(line)["event"]["kind"] for line in events] == [
        "started",
        "settled",
    ]


async def test_attempt_record_retains_effective_deadline_grace_and_output_limit(
    tmp_path: Path,
) -> None:
    """Trace request policy even for limits that are not CLI arguments."""
    # Given
    store = create_evidence_store()
    await store.create(tmp_path / "run", frozen_plan())
    original = attempt_evidence()
    request = AttemptRequest(
        argv=("/usr/bin/codex", "exec"),
        cwd=tmp_path,
        timeout_seconds=9.0,
        cleanup_timeout_seconds=3.0,
        grace_seconds=1.0,
        output_limit_bytes=128,
        stdin="devnull",
    )
    evidence = replace(original, request=request)

    # When
    record = await store.record_attempt("run-1", "call-1", 0, 1, evidence, None)

    # Then
    assert record.argv == request.argv
    assert record.cwd == str(tmp_path)
    assert (
        record.timeout_seconds,
        record.cleanup_timeout_seconds,
        record.grace_seconds,
    ) == (
        request.timeout_seconds,
        request.cleanup_timeout_seconds,
        request.grace_seconds,
    )
    assert record.output_limit_bytes == 128


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason="not implemented: AC-2 staged instruction snapshot survives source edits",
)
def test_request_uses_staged_instructions_after_original_file_changes() -> None:
    """Prove the native setting targets frozen evidence, never a reopened source."""
    # Given
    # A clean tracked -i file frozen into the new evidence area.

    # When
    # The original source changes after freeze and the request is then constructed.

    # Then
    # argv maps -c model_instructions_file=PATH to the staged snapshot path and
    # execution remains based on the captured bytes.
    pass


async def test_new_output_requires_external_or_ignored_location_before_any_launch(
    tmp_path: Path,
) -> None:
    """Check destination policy before any artifacts or model process can exist."""
    # Given
    repository = tmp_path / "context"
    repository.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"],
        cwd=repository,
        check=True,
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repository, check=True)
    (repository / ".gitignore").write_text("ignored/\n")
    (repository / "input.txt").write_text("context")
    subprocess.run(
        ["git", "add", ".gitignore", "input.txt"], cwd=repository, check=True
    )
    subprocess.run(["git", "commit", "-qm", "input"], cwd=repository, check=True)
    plan = FrozenPlan.model_validate(
        frozen_plan().model_dump() | {"repository_root": repository}
    )

    # When
    with pytest.raises(ValueError, match="Git-ignored"):
        await create_evidence_store().create(repository / "unignored", plan)
    ignored = await create_evidence_store().create(repository / "ignored" / "run", plan)
    external = await create_evidence_store().create(tmp_path / "external", plan)

    # Then
    assert ignored.output_directory.is_dir()
    assert external.output_directory.is_dir()
    assert not (repository / "unignored").exists()


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason="not implemented: AC-2 omitted instruction file preserves Codex defaults",
)
def test_omitted_instructions_file_adds_no_override_or_staged_artifact() -> None:
    """Retain default/unavailable metadata when the optional -i input is absent."""
    # Given
    # A clean planned invocation with no -i / --instructions-file setting.

    # When
    # The effective request is built and the frozen plan is persisted.

    # Then
    # argv has no model_instructions_file override, no instruction artifact is
    # staged, and metadata says defaults are preserved with automatic bytes
    # unavailable.
    pass
