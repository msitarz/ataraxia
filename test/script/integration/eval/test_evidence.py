# SPDX-License-Identifier: Apache-2.0
"""Real-filesystem checks for immutable evidence publication."""

from dataclasses import replace
import json
import os
from pathlib import Path

import pytest

from script.eval.evidence import create_evidence_store
from script.eval.model import (
    AttemptEvidence,
    InstructionsSnapshot,
    QuotaProbeCancelled,
    QuotaProbeEvidence,
    QuotaProbeStarted,
    QuotaTelemetryEvent,
    QuotaWaitContext,
    RunRecord,
    WaitEvent,
)
from script.process_supervisor import (
    AttemptObservation,
    AttemptRequest,
    CapturedOutput,
    Completed,
)
from test.script.integration.eval.support import (
    attempt_evidence,
    empty_quota_observation,
    frozen_plan,
    git,
    make_repository,
    quota_probe_request,
    stream_bytes,
    supervisor_outcome_cases,
)


async def test_run_setup_is_exclusive_and_persists_configuration_before_dispatch(
    tmp_path: Path,
) -> None:
    """Observe directory exclusion and durable pre-dispatch plan artifacts."""
    # Given
    repository = make_repository(tmp_path / "context")
    plan = frozen_plan(repository)
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
    assert record.stdout_artifact is not None
    persisted = Path(record.stdout_artifact).parent / "attempt-1.json"
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


async def test_empty_and_unavailable_usage_remain_distinct(tmp_path: Path) -> None:
    """Retain observed empty usage bytes separately from missing telemetry."""
    # Given
    store = create_evidence_store()
    await store.create(tmp_path / "run", frozen_plan())
    base = attempt_evidence()
    absent = replace(base, usage_telemetry=None)
    empty = replace(base, usage_telemetry=b"")

    # When
    absent_record = await store.record_attempt(
        "run-1", "call-absent", 0, 1, absent, None
    )
    empty_record = await store.record_attempt("run-1", "call-empty", 1, 1, empty, None)

    # Then
    assert absent_record.usage_telemetry is None
    assert empty_record.usage_telemetry == b""


@pytest.mark.parametrize(
    "case",
    supervisor_outcome_cases(),
    ids=lambda case: case[0],
)
async def test_supervisor_outcomes_keep_their_observed_evidence(
    case: tuple[
        str,
        AttemptEvidence,
        str,
        str | None,
        int | None,
        str,
        bool,
        str | None,
        str | None,
    ],
    tmp_path: Path,
) -> None:
    """Persist supervisor outcomes, exact binary prefixes, and absent observations."""
    # Given
    (
        case_name,
        evidence,
        kind,
        termination,
        exit_status,
        elapsed_basis,
        has_cleanup,
        error_type,
        diagnostic,
    ) = case
    store = create_evidence_store()
    await store.create(tmp_path / "run", frozen_plan())

    # When
    record = await store.record_attempt("run-1", case_name, 0, 1, evidence, None)

    # Then
    assert (
        record.outcome_kind,
        record.termination_reason,
        record.exit_status,
        record.elapsed_basis,
        record.cleanup is not None,
        record.error_type,
        record.diagnostic,
    ) == (
        kind,
        termination,
        exit_status,
        elapsed_basis,
        has_cleanup,
        error_type,
        diagnostic,
    )
    assert stream_bytes(record) == (
        (b"\x00\xff", b"\xfe") if has_cleanup else (None, None)
    )
    if record.cleanup is not None:
        assert record.cleanup.direct_wait == "reaped"
    if case_name == "unobserved-exception":
        assert record.ended_at_utc is None


async def test_attempt_and_probe_records_preserve_shared_process_artifacts(
    tmp_path: Path,
) -> None:
    """Verify both persisted record types expose the supervised outcomes."""
    # Given
    store = create_evidence_store()
    await store.create(tmp_path / "run", frozen_plan())
    process = attempt_evidence()
    request = quota_probe_request("probe.alpha")
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
    dotted_request = quota_probe_request("probe.beta")
    dotted_settled = await store.record_quota_probe_settled(
        QuotaProbeEvidence(
            request=dotted_request,
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
    assert dotted_settled.record.stdout_artifact is not None
    assert settled.record.stdout_artifact != dotted_settled.record.stdout_artifact
    events = (tmp_path / "run" / "events.jsonl").read_text().splitlines()
    assert [json.loads(line)["event"]["kind"] for line in events] == [
        "started",
        "settled",
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
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check destination policy before any artifacts or model process can exist."""
    # Given
    repository = make_repository(tmp_path / "context")
    (repository / ".gitignore").write_text("ignored/\n")
    git(repository, "add", ".gitignore")
    git(repository, "commit", "-qm", "ignore")
    plan = frozen_plan(repository)

    # When
    monkeypatch.setenv("GIT_DIR", os.fspath(tmp_path / "wrong-git-dir"))
    monkeypatch.setenv("GIT_INDEX_FILE", os.fspath(tmp_path / "wrong-index"))
    with pytest.raises(ValueError, match="Git-ignored"):
        await create_evidence_store().create(repository / "unignored", plan)
    ignored = await create_evidence_store().create(repository / "ignored" / "run", plan)
    external = await create_evidence_store().create(tmp_path / "external", plan)

    # Then
    assert ignored.output_directory.is_dir()
    assert external.output_directory.is_dir()
    assert not (repository / "unignored").exists()


async def test_opaque_call_ids_cannot_escape_or_alias_artifact_paths(
    tmp_path: Path,
) -> None:
    """Hash opaque identities into distinct safe artifact path segments."""
    # Given
    store = create_evidence_store()
    prepared = await store.create(tmp_path / "run", frozen_plan())
    evidence = attempt_evidence()

    # When
    first = await store.record_attempt(
        "run-1", "../../../../outside", 0, 1, evidence, None
    )
    dotted = await store.record_attempt(
        "run-1", "../../../../outside.stdout", 1, 1, evidence, None
    )

    # Then
    assert first.stdout_artifact is not None
    assert dotted.stdout_artifact is not None
    first_path = Path(first.stdout_artifact)
    dotted_path = Path(dotted.stdout_artifact)
    assert first_path.resolve().is_relative_to(prepared.output_directory)
    assert dotted_path.resolve().is_relative_to(prepared.output_directory)
    assert first_path != dotted_path
    assert first_path.read_bytes() == dotted_path.read_bytes() == b"out"


async def test_finalization_and_attempt_collision_preserve_original_artifacts(
    tmp_path: Path,
) -> None:
    """Refuse replacement of finalized run and attempt files."""
    # Given
    store = create_evidence_store()
    prepared = await store.create(tmp_path / "run", frozen_plan())
    original = await store.record_attempt(
        "run-1", "call-1", 0, 1, attempt_evidence(), None
    )
    assert original.stdout_artifact is not None
    stdout = Path(original.stdout_artifact)
    attempt_record = stdout.parent / "attempt-1.json"
    metadata_before = attempt_record.read_bytes()
    plan_before = prepared.plan_artifact.read_bytes()
    stdout_before = stdout.read_bytes()
    run = RunRecord(
        run_id="run-1",
        repository_root="/work",
        head_commit="fixture-head",
        state="complete",
        runner_version="test-runner",
        codex_path=None,
        cli_version=None,
        effective_settings=(),
        calls=(),
    )

    # When
    with pytest.raises(FileExistsError):
        await store.record_attempt("run-1", "call-1", 0, 1, attempt_evidence(), None)
    await store.finalize(run)
    run_bytes = (prepared.output_directory / "run.json").read_bytes()
    with pytest.raises(FileExistsError):
        await store.finalize(run.model_copy(update={"state": "incomplete"}))

    # Then
    assert attempt_record.read_bytes() == metadata_before
    assert stdout.read_bytes() == stdout_before
    assert prepared.plan_artifact.read_bytes() == plan_before
    assert (prepared.output_directory / "run.json").read_bytes() == run_bytes


async def test_wait_telemetry_and_prelaunch_cancel_append_without_process_record(
    tmp_path: Path,
) -> None:
    """Keep live scalar events in order without inventing canceled probe output."""
    # Given
    store = create_evidence_store()
    prepared = await store.create(tmp_path / "run", frozen_plan())
    observation = empty_quota_observation()
    request = quota_probe_request("probe.cancelled")
    context = QuotaWaitContext(
        kind="quota",
        trigger_call_id="call-1",
        trigger_attempt_number=1,
        cumulative_waited_before_seconds=0.0,
        wait_limit_seconds=None,
        quota_observation=observation,
        selected_reset_at_utc=None,
    )
    wait = WaitEvent(
        run_id="run-1",
        wait_id="wait-1",
        context=context,
        kind="started",
        observed_at_utc="2026-10-26T00:00:00Z",
        elapsed_seconds=0.0,
        quota_observation=observation,
        end=None,
        diagnostic=None,
    )
    cancelled = QuotaProbeCancelled(
        kind="cancelled",
        schedule=request.schedule,
        cause="stop",
        ended_at_utc="2026-10-26T00:00:03Z",
        elapsed_seconds=2.0,
        elapsed_basis="monotonic",
    )

    # When
    await store.record_wait_event(wait)
    await store.record_quota_telemetry(
        QuotaTelemetryEvent(
            run_id="run-1",
            call_id="call-1",
            attempt_number=1,
            observation=observation,
        )
    )
    await store.record_quota_probe_event(cancelled)

    # Then
    events = [
        json.loads(line)
        for line in (prepared.output_directory / "events.jsonl")
        .read_text()
        .splitlines()
    ]
    assert [event["kind"] for event in events] == [
        "wait",
        "quota_telemetry",
        "probe",
    ]
    assert events[-1]["event"]["kind"] == "cancelled"
    assert not (prepared.output_directory / "probes").exists()


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
