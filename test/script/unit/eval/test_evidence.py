# SPDX-License-Identifier: Apache-2.0
"""Typed evidence adapter ordering and identity forwarding."""

from pathlib import Path

import pytest

from script.eval.evidence import EvidenceStoreAdapter
from script.eval.model import (
    AttemptEvidence,
    AttemptRecord,
    CallId,
    DirectoryOption,
    FrozenPlan,
    HarnessConfig,
    PreparedEvidence,
    QuotaAllowanceId,
    QuotaObservation,
    QuotaProbeEvidence,
    QuotaProbeId,
    QuotaProbeRequest,
    QuotaProbeSchedule,
    QuotaProbeScheduled,
    QuotaProbeSettled,
    QuotaProviderId,
    QuotaScope,
    QuotaTelemetryEvent,
    QuotaWaitContext,
    RetryAssessment,
    RunId,
    RunRecord,
    WaitEvent,
)
from script.process_supervisor import (
    AttemptObservation,
    AttemptRequest,
    CapturedOutput,
    CleanupEvidence,
    Completed,
)


def attempt_evidence() -> AttemptEvidence:
    """Return live supervisor evidence with independently captured streams."""
    request = AttemptRequest(
        argv=("codex", "exec"),
        cwd=Path("/work"),
        timeout_seconds=5.0,
        cleanup_timeout_seconds=2.0,
        output_limit_bytes=0,
        stdin="devnull",
    )
    return AttemptEvidence(
        control_flow="returned",
        outcome=Completed(
            observation=AttemptObservation(
                output=CapturedOutput(stdout=b"out", stderr=b"err"),
                elapsed_seconds=1.0,
                cleanup=CleanupEvidence("owned", (), "reaped", None),
            ),
            exit_status=0,
        ),
        error_type=None,
        diagnostic=None,
        request=request,
        started_at_utc="2026-10-26T00:00:00Z",
        ended_at_utc="2026-10-26T00:00:01Z",
        usage_telemetry=None,
    )


def attempt_record() -> AttemptRecord:
    """Return one scalar record for projection and append ordering checks."""
    return AttemptRecord.model_validate({
        "run_id": "run-1",
        "call_id": "call-2",
        "position": 3,
        "attempt_number": 2,
        "control_flow": "returned",
        "outcome_kind": "completed",
        "started_at_utc": "2026-10-26T00:00:00Z",
        "ended_at_utc": "2026-10-26T00:00:01Z",
        "argv": ("codex", "exec"),
        "cwd": "/work",
        "timeout_seconds": 5.0,
        "cleanup_timeout_seconds": 2.0,
        "grace_seconds": 0.0,
        "output_limit_bytes": 0,
        "elapsed_seconds": 1.0,
        "elapsed_basis": "supervisor_observation",
        "exit_status": 0,
        "termination_reason": None,
        "cleanup": None,
        "stdout_artifact": None,
        "stderr_artifact": None,
        "usage_telemetry": None,
        "error_type": None,
        "diagnostic": None,
        "retry_assessment": None,
    })


def assessment() -> RetryAssessment:
    """Return the runner's already-computed retry decision."""
    return RetryAssessment(
        retry_class="unknown",
        classification_basis=None,
        no_result_basis="present_or_unknown",
        diagnostic="insufficient evidence",
    )


def frozen_plan() -> FrozenPlan:
    """Build the smallest valid frozen plan for pre-dispatch setup tests."""
    config = HarnessConfig(
        ordered_options=(DirectoryOption(position=0, path=Path("context")),),
        models=("model-a",),
        efforts=("low",),
        concurrency=1,
        output_directory=Path("results"),
        dry_run=False,
        timeout_seconds=5.0,
        cleanup_timeout_seconds=2.0,
        grace_seconds=0.0,
        output_limit_bytes=0,
        instructions_file_path=None,
    )
    return FrozenPlan(
        run_id="run-1",
        configuration=config,
        repository_root=Path("/work"),
        head_commit="commit-1",
        snapshots=(),
        boundary_bytes=(),
        instructions_file=None,
        calls=(),
    )


def test_create_forwards_plan_and_returns_prepared_paths() -> None:
    """Pre-dispatch setup uses the exact caller destination and frozen plan."""
    plan = frozen_plan()
    prepared = PreparedEvidence(Path("results"), Path("results/plan.json"), None)
    observed: list[tuple[Path, FrozenPlan]] = []

    def create(output_directory: Path, value: FrozenPlan) -> PreparedEvidence:
        observed.append((output_directory, value))
        return prepared

    store = EvidenceStoreAdapter(create_evidence=create)

    result = store.create(Path("results"), plan)

    assert result is prepared
    assert observed == [(Path("results"), plan)]


def test_record_attempt_projects_then_appends_with_supplied_identity() -> None:
    """Forward runner-owned classification and persist before returning."""
    order: list[str] = []
    observed: list[
        tuple[RunId, CallId, int, int, AttemptEvidence, RetryAssessment | None]
    ] = []
    evidence = attempt_evidence()
    classification = assessment()
    record = attempt_record()

    def project(
        run_id: RunId,
        call_id: CallId,
        position: int,
        attempt_number: int,
        value: AttemptEvidence,
        retry_assessment: RetryAssessment | None,
    ) -> AttemptRecord:
        order.append("project")
        observed.append((
            run_id,
            call_id,
            position,
            attempt_number,
            value,
            retry_assessment,
        ))
        return record

    def append(value: AttemptRecord) -> None:
        order.append("append")
        assert value is record

    store = EvidenceStoreAdapter(project_attempt=project, append_attempt=append)

    result = store.record_attempt("run-1", "call-2", 3, 2, evidence, classification)

    assert result is record
    assert order == ["project", "append"]
    assert observed == [("run-1", "call-2", 3, 2, evidence, classification)]


def test_attempt_append_failure_propagates_after_projection() -> None:
    """A failed required evidence write reaches the coordinator unchanged."""
    failure = OSError("ledger unavailable")
    order: list[str] = []

    def append(_record: AttemptRecord) -> None:
        order.append("append")
        raise failure

    store = EvidenceStoreAdapter(
        project_attempt=lambda *_args: order.append("project") or attempt_record(),
        append_attempt=append,
    )

    with pytest.raises(OSError) as captured:
        store.record_attempt("run-1", "call-2", 3, 2, attempt_evidence(), None)

    assert captured.value is failure
    assert order == ["project", "append"]


def test_settled_probe_is_projected_then_appended_and_returned() -> None:
    """Probe assessment and process projection settle before caller resumes."""
    request = QuotaProbeRequest(
        schedule=QuotaProbeSchedule(
            run_id="run-1",
            probe_id=QuotaProbeId("probe-1"),
            scope=QuotaScope(
                provider_id=QuotaProviderId("codex"),
                allowance_id=QuotaAllowanceId("a1"),
            ),
            reason="periodic",
            created_at_utc="2026-10-26T00:00:00Z",
            due_at_utc="2026-10-26T00:00:01Z",
            interval_seconds=1.0,
            reset_hint_at_utc=None,
        ),
        pause_wait_id=None,
        poll_started_at_utc="2026-10-26T00:00:01Z",
        scheduled_wait_seconds=1.0,
        scheduled_wait_elapsed_basis="monotonic",
    )
    evidence = QuotaProbeEvidence(
        request=request,
        process=attempt_evidence(),
        quota_state="unknown",
        observation=None,
        classification_basis="source unavailable",
    )
    settled = QuotaProbeSettled.model_validate({
        "kind": "settled",
        "record": {
            "control_flow": "returned",
            "outcome_kind": "completed",
            "started_at_utc": "2026-10-26T00:00:00Z",
            "ended_at_utc": "2026-10-26T00:00:01Z",
            "argv": ("codex", "exec"),
            "cwd": "/work",
            "timeout_seconds": 5.0,
            "cleanup_timeout_seconds": 2.0,
            "grace_seconds": 0.0,
            "output_limit_bytes": 0,
            "elapsed_seconds": 1.0,
            "elapsed_basis": "supervisor_observation",
            "exit_status": 0,
            "termination_reason": None,
            "cleanup": None,
            "stdout_artifact": None,
            "stderr_artifact": None,
            "usage_telemetry": None,
            "error_type": None,
            "diagnostic": None,
            "request": {
                "schedule": {
                    "run_id": "run-1",
                    "probe_id": "probe-1",
                    "scope": {"provider_id": "codex", "allowance_id": "a1"},
                    "reason": "periodic",
                    "created_at_utc": "2026-10-26T00:00:00Z",
                    "due_at_utc": "2026-10-26T00:00:01Z",
                    "interval_seconds": 1.0,
                    "reset_hint_at_utc": None,
                },
                "pause_wait_id": None,
                "poll_started_at_utc": "2026-10-26T00:00:01Z",
                "scheduled_wait_seconds": 1.0,
                "scheduled_wait_elapsed_basis": "monotonic",
            },
            "quota_state": "unknown",
            "observation": None,
            "classification_basis": "source unavailable",
        },
    })
    order: list[str] = []

    def project(value: QuotaProbeEvidence) -> QuotaProbeSettled:
        order.append("project")
        assert value is evidence
        return settled

    def append(value: QuotaProbeSettled) -> None:
        order.append("append")
        assert value is settled

    store = EvidenceStoreAdapter(
        project_settled_probe=project, append_settled_probe=append
    )

    result = store.record_quota_probe_settled(evidence)

    assert result is settled
    assert order == ["project", "append"]


def test_lifecycle_telemetry_and_final_records_use_separate_ports() -> None:
    """Forward append-only values intact through their distinct store ports."""
    schedule = QuotaProbeSchedule(
        run_id="run-1",
        probe_id=QuotaProbeId("probe-1"),
        scope=QuotaScope(
            provider_id=QuotaProviderId("codex"),
            allowance_id=QuotaAllowanceId("a1"),
        ),
        reason="periodic",
        created_at_utc="2026-10-26T00:00:00Z",
        due_at_utc="2026-10-26T00:00:01Z",
        interval_seconds=1.0,
        reset_hint_at_utc=None,
    )
    observation = QuotaObservation(
        scope=schedule.scope,
        read_at_utc="2026-10-26T00:00:00Z",
        source_coordinate="session:1",
        windows=(),
        diagnostic=None,
    )
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
    probe = QuotaProbeScheduled(kind="scheduled", schedule=schedule)
    telemetry = QuotaTelemetryEvent(
        run_id="run-1",
        call_id="call-1",
        attempt_number=1,
        observation=observation,
    )
    run = RunRecord(
        run_id="run-1",
        repository_root="/work",
        head_commit="commit-1",
        state="complete",
        runner_version="runner-1",
        codex_path=None,
        cli_version=None,
        effective_settings=(),
        calls=(),
        waits=(),
    )
    writes: list[tuple[str, object]] = []
    store = EvidenceStoreAdapter(
        append_wait_event=lambda value: writes.append(("wait", value)),
        append_probe_event=lambda value: writes.append(("probe", value)),
        append_quota_telemetry=lambda value: writes.append(("telemetry", value)),
        finalize_evidence=lambda value: writes.append(("final", value)),
    )

    store.record_wait_event(wait)
    store.record_quota_probe_event(probe)
    store.record_quota_telemetry(telemetry)
    store.finalize(run)

    assert writes == [
        ("wait", wait),
        ("probe", probe),
        ("telemetry", telemetry),
        ("final", run),
    ]


def test_unfinished_default_storage_leaf_fails_visibly() -> None:
    """Default composition never implies persistence before leaf implementation."""
    store = EvidenceStoreAdapter()

    with pytest.raises(NotImplementedError, match="exclusive evidence creation"):
        store.create(Path("results"), frozen_plan())
