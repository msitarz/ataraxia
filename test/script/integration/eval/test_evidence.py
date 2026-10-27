# SPDX-License-Identifier: Apache-2.0
"""Real-filesystem checks for immutable evidence publication."""

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tomllib

import pytest

from script.eval.evidence import create_evidence_store
from script.eval.inputs import GitRepositoryReader
from script.eval.model import (
    AttemptEvidence,
    DirectoryOption,
    FrozenPlan,
    HarnessConfig,
    InstructionsSnapshot,
    QuotaProbeCancelled,
    QuotaProbeEvidence,
    QuotaProbeStarted,
    QuotaTelemetryEvent,
    QuotaWaitContext,
    RunRecord,
    WaitEvent,
)
from script.eval.plan import PurePlanBuilder
from script.eval.runner import CliBinding
from script.eval.runner.adapters import CodexAttemptRequestBuilder
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


async def test_probe_records_preserve_process_artifacts(
    tmp_path: Path,
) -> None:
    """Verify persisted probe records expose the supervised outcomes."""
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


def frozen_instruction_plan(
    tmp_path: Path,
) -> tuple[Path, bytes, HarnessConfig, FrozenPlan]:
    """Freeze a tracked instruction file with its real repository reader."""
    repository = make_repository(tmp_path / "context")
    original = repository / "instructions.md"
    instruction_bytes = b"frozen system instructions"
    original.write_bytes(instruction_bytes)
    git(repository, "add", "instructions.md")
    git(repository, "commit", "-qm", "add instructions")
    configuration = HarnessConfig(
        ordered_options=(DirectoryOption(position=0, path=repository / "context"),),
        models=("model-a",),
        efforts=("low",),
        concurrency=1,
        output_directory=tmp_path / "run",
        dry_run=False,
        timeout_seconds=5.0,
        cleanup_timeout_seconds=2.0,
        grace_seconds=0.0,
        output_limit_bytes=0,
        instructions_file_path=original,
    )
    inputs = GitRepositoryReader().freeze(configuration)
    plan = PurePlanBuilder("run-1").plan(inputs, configuration)
    return original, instruction_bytes, configuration, plan


def static_cli_binding() -> CliBinding:
    """Describe an absolute CLI path without launching Codex in integration tests."""
    return CliBinding(
        executable_path=Path("/absolute/codex"),
        cli_version="codex-cli test",
        runner_version="test",
        effective_settings=(("automatic_system_instructions", None),),
        quota_scope=None,
    )


async def test_request_uses_staged_instructions_after_original_file_changes(
    tmp_path: Path,
) -> None:
    """Prove the native setting targets frozen evidence, never a reopened source."""
    # Given
    original, instruction_bytes, configuration, plan = frozen_instruction_plan(tmp_path)
    prepared = await create_evidence_store().create(tmp_path / "run", plan)
    binding = static_cli_binding()
    builder = CodexAttemptRequestBuilder()

    # When
    original.write_bytes(b"changed source")
    effective_call = builder.build(
        plan, plan.calls[0], binding, prepared, configuration
    )

    # Then
    # argv maps the override to staged immutable bytes; no source bytes changed
    # in the frozen plan or persisted evidence.
    staged = prepared.model_instructions_file
    assert staged is not None
    assert staged.read_bytes() == instruction_bytes
    assert plan.instructions_file is not None
    assert plan.instructions_file.content == instruction_bytes
    request = effective_call.request
    assert request.argv[-1] == plan.calls[0].prompt.decode("utf-8")
    override = next(
        request.argv[index + 1]
        for index, argument in enumerate(request.argv[:-1])
        if argument == "-c"
        and request.argv[index + 1].startswith("model_instructions_file=")
    )
    assert tomllib.loads(override)["model_instructions_file"] == str(staged)
    assert original.read_bytes() == b"changed source"


async def test_unignored_in_repository_output_is_written_and_makes_next_freeze_dirty(
    tmp_path: Path,
) -> None:
    """Write evidence into an unignored checkout without changing Git metadata."""
    # Given
    repository = make_repository(tmp_path / "context")
    output = repository / "evidence" / "run"
    configuration = HarnessConfig(
        ordered_options=(DirectoryOption(position=0, path=repository / "context"),),
        models=("model-a",),
        efforts=("low",),
        concurrency=1,
        output_directory=output,
        dry_run=False,
        timeout_seconds=5.0,
        cleanup_timeout_seconds=2.0,
        grace_seconds=0.0,
        output_limit_bytes=0,
        instructions_file_path=None,
    )
    reader = GitRepositoryReader()
    inputs = reader.freeze(configuration)
    plan = PurePlanBuilder("run-1").plan(inputs, configuration)
    index_before = (repository / ".git" / "index").read_bytes()
    tracked_before = git(repository, "ls-files", "--stage", "-z")

    # When
    prepared = await create_evidence_store().create(output, plan)
    artifact_names = {path.name for path in output.iterdir()}
    status_after_write = git(repository, "status", "--porcelain=v1", "-z")
    with pytest.raises(ValueError, match="worktree must be clean"):
        reader.freeze(configuration)

    # Then
    assert prepared.output_directory == output.resolve()
    assert artifact_names == {"plan.json"}
    assert json.loads(prepared.plan_artifact.read_text()) == plan.model_dump(
        mode="json"
    )
    assert b"?? evidence/" in status_after_write
    assert (repository / ".git" / "index").read_bytes() == index_before
    assert git(repository, "ls-files", "--stage", "-z") == tracked_before
    assert not (repository / ".gitignore").exists()


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


async def test_repeated_call_id_at_distinct_positions_has_separate_attempts(
    tmp_path: Path,
) -> None:
    """Persist repeated effective call IDs in their scheduled positions."""
    # Given
    store = create_evidence_store()
    prepared = await store.create(tmp_path / "run", frozen_plan())
    evidence = attempt_evidence()

    # When
    first = await store.record_attempt("run-1", "same-call", 0, 1, evidence, None)
    second = await store.record_attempt("run-1", "same-call", 1, 1, evidence, None)

    # Then
    assert first.position == 0
    assert second.position == 1
    assert first.stdout_artifact != second.stdout_artifact
    for record in (first, second):
        assert record.stdout_artifact is not None
        metadata = Path(record.stdout_artifact).parent / "attempt-1.json"
        assert json.loads(metadata.read_text())["position"] == record.position
        assert Path(record.stdout_artifact).is_relative_to(prepared.output_directory)


async def test_partial_attempt_publication_preserves_conflict_and_reports_orphan(
    tmp_path: Path,
) -> None:
    """Keep a conflicting stream intact and expose partial publication honestly."""
    # Given
    store = create_evidence_store()
    prepared = await store.create(tmp_path / "run", frozen_plan())
    call_id = "partial-write"
    position = 4
    stem = (
        prepared.output_directory
        / "attempts"
        / f"position-{position}"
        / hashlib.sha256(call_id.encode()).hexdigest()
        / "attempt-1"
    )
    stderr = Path(f"{stem}.stderr")
    stderr.parent.mkdir(parents=True)
    stderr.write_bytes(b"existing stderr")

    # When
    with pytest.raises(FileExistsError):
        await store.record_attempt(
            "run-1", call_id, position, 1, attempt_evidence(), None
        )

    # Then
    assert stderr.read_bytes() == b"existing stderr"
    assert Path(f"{stem}.stdout").read_bytes() == b"out"
    assert not Path(f"{stem}.json").exists()


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


async def test_omitted_instructions_file_adds_no_override_or_staged_artifact(
    tmp_path: Path,
) -> None:
    """Retain default/unavailable metadata when the optional -i input is absent."""
    # Given
    repository = make_repository(tmp_path / "context")
    configuration = HarnessConfig(
        ordered_options=(DirectoryOption(position=0, path=repository / "context"),),
        models=("model-a",),
        efforts=("low",),
        concurrency=1,
        output_directory=tmp_path / "run",
        dry_run=False,
        timeout_seconds=5.0,
        cleanup_timeout_seconds=2.0,
        grace_seconds=0.0,
        output_limit_bytes=0,
        instructions_file_path=None,
    )
    inputs = GitRepositoryReader().freeze(configuration)
    plan = PurePlanBuilder("run-1").plan(inputs, configuration)
    prepared = await create_evidence_store().create(tmp_path / "run", plan)
    binding = static_cli_binding()
    effective_call = CodexAttemptRequestBuilder().build(
        plan, plan.calls[0], binding, prepared, configuration
    )

    # When
    assert plan.instructions_file is None
    assert prepared.model_instructions_file is None
    assert binding.effective_settings == (("automatic_system_instructions", None),)

    # Then
    assert not any(
        argument.startswith("model_instructions_file=")
        for index, argument in enumerate(effective_call.request.argv)
        if index > 0 and effective_call.request.argv[index - 1] == "-c"
    )
    assert prepared.model_instructions_file is None
    assert {path.name for path in prepared.output_directory.iterdir()} == {"plan.json"}
    assert json.loads(prepared.plan_artifact.read_text())["instructions_file"] is None
