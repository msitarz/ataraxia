# SPDX-License-Identifier: Apache-2.0
"""Pure coordinator transitions preserve durable evidence and dispatch gates."""

from asyncio import CancelledError
from pathlib import Path

import pytest

from script.eval.model import (
    AttemptEvidence,
    AttemptRecord,
    CapacityWaitContext,
    CleanupRecord,
    DirectoryOption,
    HarnessConfig,
    PlannedCall,
    QuotaAllowanceId,
    QuotaObservation,
    QuotaProbeEvidence,
    QuotaProbeId,
    QuotaProbeRecord,
    QuotaProbeRequest,
    QuotaProbeSchedule,
    QuotaProviderId,
    QuotaScope,
    QuotaWaitContext,
    QuotaWindowId,
    QuotaWindowObservation,
    RetryAssessment,
    RetryClass,
    SignalRecord,
    WaitRecord,
)
from script.eval.runner.coordinator.calls import (
    attempt_persisted,
    attempt_write_failed,
    call_wait_completed,
    call_wait_started,
    capture_attempt,
)
from script.eval.runner.coordinator.quota import (
    capture_probe,
    probe_dispatch_gate,
    probe_persisted,
    quota_wait_completed,
)
from script.eval.runner.coordinator.state import (
    Attempting,
    CallHistory,
    CallWait,
    Finished,
    ObservingQuota,
    Open,
    PreparingProbe,
    ProbeEvidencePending,
    ProbePrepared,
    Probing,
    Queued,
    QuotaHistory,
    QuotaStopped,
    Recording,
    RecordingProbe,
    RetryWait,
    Stopped,
    Waiting,
)
from script.eval.runner.ports import EffectiveCall
from script.process_supervisor import AttemptRequest


def config(**overrides: object) -> HarnessConfig:
    """Build a valid configuration with selected policies."""
    values: dict[str, object] = {
        "ordered_options": (DirectoryOption(position=0, path=Path("context")),),
        "models": ("m",),
        "efforts": ("low",),
        "concurrency": 1,
        "output_directory": None,
        "dry_run": True,
        "timeout_seconds": 1.0,
        "cleanup_timeout_seconds": 1.0,
        "grace_seconds": 0.0,
        "output_limit_bytes": 0,
        "instructions_file_path": None,
    }
    values.update(overrides)
    return HarnessConfig.model_validate(values)


def call() -> EffectiveCall:
    """Build one frozen request identity."""
    request = AttemptRequest(
        argv=("cmd",),
        cwd=Path("/tmp"),
        timeout_seconds=1.0,
        cleanup_timeout_seconds=1.0,
        output_limit_bytes=0,
        stdin="devnull",
        grace_seconds=0.0,
    )
    return EffectiveCall(
        "run", "call", PlannedCall.model_construct(position=0), request
    )


def assessment(kind: RetryClass, basis: str = "confident_absence") -> RetryAssessment:
    """Build a controlled classification."""
    return RetryAssessment.model_validate({
        "retry_class": kind,
        "classification_basis": "test",
        "no_result_basis": basis,
        "diagnostic": None,
    })


def process_fields() -> dict[str, object]:
    """Build a safely settled process record."""
    return {
        "control_flow": "returned",
        "outcome_kind": "completed",
        "started_at_utc": "2026-01-01T00:00:00Z",
        "ended_at_utc": "2026-01-01T00:00:01Z",
        "argv": ("cmd",),
        "cwd": "/tmp",
        "timeout_seconds": 1.0,
        "cleanup_timeout_seconds": 1.0,
        "grace_seconds": 0.0,
        "output_limit_bytes": 0,
        "elapsed_seconds": 1.0,
        "elapsed_basis": "supervisor_observation",
        "exit_status": 1,
        "termination_reason": None,
        "cleanup": CleanupRecord(
            process="owned",
            signals=(SignalRecord(signal="SIGKILL", outcome="sent", diagnostic=None),),
            direct_wait="reaped",
            wait_diagnostic=None,
        ),
        "stdout_artifact": None,
        "stderr_artifact": None,
        "usage_telemetry": None,
        "error_type": None,
        "diagnostic": None,
    }


def attempt_record(
    number: int, category: RetryClass, **overrides: object
) -> AttemptRecord:
    """Build a durable attempt with independent explicit facts."""
    fields = process_fields()
    fields.update(
        run_id="run",
        call_id="call",
        position=0,
        attempt_number=number,
        retry_assessment=assessment(category),
    )
    fields.update(overrides)
    return AttemptRecord.model_validate(fields)


def recording(history: CallHistory, number: int, category: RetryClass) -> Recording:
    """Capture one supervisor result without marking it durable."""
    evidence = AttemptEvidence(
        "returned",
        None,
        None,
        None,
        history.call.request,
        "2026-01-01T00:00:00Z",
        None,
        None,
    )
    return capture_attempt(Attempting(history, number), evidence, assessment(category))


def capacity_wait(number: int, index: int) -> CallWait:
    """Build a prepared call-local delay."""
    context = CapacityWaitContext(
        kind="capacity",
        call_id="call",
        failed_attempt_number=number,
        retry_index=index,
        base_seconds=1.0,
        cap_seconds=2.0,
        jitter_bound_seconds=1.0,
        sampled_seconds=0.0,
    )
    return CallWait("wait", context, "2026-01-01T00:00:01Z", 1.0, "prepared", None)


@pytest.mark.parametrize(
    ("category", "settings", "exit_status", "expected"),
    [
        ("infrastructure", {}, 1, Finished),
        ("infrastructure", {"retry_limit": 1, "retry_nonzero_exit": True}, 1, Queued),
        (
            "capacity",
            {
                "capacity_retry_limit": 1,
                "capacity_backoff_base_seconds": 1.0,
                "capacity_backoff_cap_seconds": 2.0,
            },
            1,
            RetryWait,
        ),
        (
            "capacity",
            {
                "capacity_retry_limit": 1,
                "capacity_backoff_base_seconds": 1.0,
                "capacity_backoff_cap_seconds": 2.0,
            },
            0,
            Finished,
        ),
        ("quota", {"quota_wait_enabled": True}, 1, Queued),
    ],
    ids=[
        "infra-default-zero",
        "infra-one",
        "capacity-independent-opt-in",
        "zero-exit-no-retry",
        "quota-independent-opt-in",
    ],
)
def test_durable_attempt_selects_independent_retry_policy(
    category: RetryClass, settings: dict[str, object], exit_status: int, expected: type
) -> None:
    # Given
    history = CallHistory(call(), (), ())
    state = recording(history, 1, category)
    record = attempt_record(1, category, exit_status=exit_status)
    settings_config = config(**settings)

    # When
    result = attempt_persisted(
        state, record, settings_config, None, capacity_wait(1, 0)
    )

    # Then
    if settings_config.quota_wait_enabled:
        assert isinstance(result, ObservingQuota)
        from script.eval.model import QuotaTelemetryEvent
        from script.eval.runner.coordinator.calls import (
            capture_telemetry,
            telemetry_persisted,
        )

        result = telemetry_persisted(
            capture_telemetry(
                result,
                QuotaTelemetryEvent(
                    run_id="run",
                    call_id="call",
                    attempt_number=1,
                    observation=observation(),
                ),
            ),
            settings_config,
            None,
            None,
        )
    assert isinstance(result, expected)
    assert result.history.attempts == (record,)
    assert history.attempts == ()


@pytest.mark.parametrize(
    ("prior", "category", "settings", "expected"),
    [
        (
            ("infrastructure",),
            "infrastructure",
            {"retry_limit": 1, "retry_nonzero_exit": True},
            Finished,
        ),
        (
            ("infrastructure",),
            "capacity",
            {
                "capacity_retry_limit": 1,
                "capacity_backoff_base_seconds": 1.0,
                "capacity_backoff_cap_seconds": 2.0,
            },
            RetryWait,
        ),
        (
            ("capacity",),
            "capacity",
            {
                "capacity_retry_limit": 1,
                "capacity_backoff_base_seconds": 1.0,
                "capacity_backoff_cap_seconds": 2.0,
            },
            Finished,
        ),
    ],
    ids=["infra-exhausted", "mixed-separate-count", "capacity-exhausted"],
)
def test_retry_allowances_count_dispatched_retries(
    prior: tuple[RetryClass, ...],
    category: RetryClass,
    settings: dict[str, object],
    expected: type,
) -> None:
    # Given
    history = CallHistory(
        call(), tuple(attempt_record(i + 1, item) for i, item in enumerate(prior)), ()
    )
    state = recording(history, 2, category)

    # When
    result = attempt_persisted(
        state,
        attempt_record(2, category),
        config(**settings),
        None,
        capacity_wait(2, 0),
    )

    # Then
    assert isinstance(result, expected)
    assert len(result.history.attempts) == 2


def observation() -> QuotaObservation:
    """Build a fresh scoped available observation."""
    scope = QuotaScope(
        provider_id=QuotaProviderId("p"), allowance_id=QuotaAllowanceId("a")
    )
    window = QuotaWindowObservation(
        window_id=QuotaWindowId("w"),
        state="available",
        usage_percent=20.0,
        reset_at_utc=None,
        source_observed_at_utc="2026-01-01T00:00:01Z",
        source_sequence=1,
        source="source",
        diagnostic=None,
    )
    return QuotaObservation(
        scope=scope,
        read_at_utc="2026-01-01T00:00:01Z",
        source_coordinate="source",
        windows=(window,),
        diagnostic=None,
        valid_until_utc="2026-01-01T00:00:03Z",
    )


def waiting() -> Waiting:
    """Build a durably started quota wait."""
    obs = observation()
    context = QuotaWaitContext(
        kind="quota",
        trigger_call_id="call",
        trigger_attempt_number=1,
        cumulative_waited_before_seconds=0.0,
        wait_limit_seconds=None,
        quota_observation=obs,
        selected_reset_at_utc=None,
    )
    return Waiting(context, "wait", "2026-01-01T00:00:00Z", 0.0, "durable", None, obs)


def request() -> QuotaProbeRequest:
    """Build an exact request for the active pause."""
    obs = observation()
    assert obs.scope is not None
    schedule = QuotaProbeSchedule(
        run_id="run",
        probe_id=QuotaProbeId("probe"),
        scope=obs.scope,
        reason="periodic",
        created_at_utc="2026-01-01T00:00:00Z",
        due_at_utc="2026-01-01T00:00:01Z",
        interval_seconds=1.0,
        reset_hint_at_utc=None,
    )
    return QuotaProbeRequest(
        schedule=schedule,
        pause_wait_id="wait",
        poll_started_at_utc="2026-01-01T00:00:01Z",
        scheduled_wait_seconds=1.0,
        scheduled_wait_elapsed_basis="monotonic",
    )


@pytest.mark.parametrize(
    ("remaining", "expected"),
    [(None, True), (1.0, True), (0.0, False), (-1.0, False)],
    ids=["unbounded", "remaining", "exact-bound", "expired"],
)
def test_probe_gate_rechecks_wait_bound(
    remaining: float | None, expected: bool
) -> None:
    # Given
    req = request()
    state = PreparingProbe(waiting(), ProbePrepared(req.schedule, "wait"))

    # When
    result = probe_dispatch_gate(
        state,
        config(quota_wait_enabled=True),
        0,
        remaining,
        None,
        None,
        "2026-01-01T00:00:02Z",
        2.0,
    )

    # Then
    assert isinstance(result, PreparingProbe) is expected


@pytest.mark.parametrize(
    ("now", "expected"),
    [("2026-01-01T00:00:03Z", Open), ("2026-01-01T00:00:04Z", QuotaStopped)],
    ids=["expiry-inclusive", "expired-after-write"],
)
def test_available_probe_opens_only_after_fresh_durable_closure(
    now: str, expected: type
) -> None:
    # Given
    req = request()
    evidence = QuotaProbeEvidence(
        req,
        AttemptEvidence(
            "returned",
            None,
            None,
            None,
            call().request,
            "2026-01-01T00:00:00Z",
            None,
            None,
        ),
        "available",
        observation(),
        "controlled",
    )
    state = RecordingProbe(waiting(), evidence)
    fields = process_fields()
    fields.update(
        request=req,
        quota_state="available",
        observation=observation(),
        classification_basis="controlled",
        exit_status=0,
    )
    record = QuotaProbeRecord.model_validate(fields)

    # When
    history, pending = probe_persisted(
        state, QuotaHistory((), ()), record, None, None, "2026-01-01T00:00:02Z", 2.0
    )
    assert pending.end_record is not None
    history, result = quota_wait_completed(
        pending, history, pending.end_record, None, None, now
    )

    # Then
    assert isinstance(result, expected)
    assert history.probes == (record,)
    assert len(history.waits) == 1


def test_missing_probe_evidence_retains_exact_request_and_error() -> None:
    # Given
    req = request()
    error = TimeoutError("timeout")

    # When
    result = capture_probe(Probing(waiting(), req), None, error)

    # Then
    assert isinstance(result, ProbeEvidencePending)
    assert result.request is req
    assert result.error is error


@pytest.mark.parametrize(
    ("record_changes", "outcome"),
    [
        (
            {"retry_assessment": assessment("infrastructure", "present_or_unknown")},
            "failure",
        ),
        ({"outcome_kind": "output_limit_exceeded"}, "failure"),
        ({"cleanup": None, "exit_status": 0}, "failure"),
        ({"control_flow": "cancelled", "outcome_kind": "cancelled"}, "cancelled"),
    ],
    ids=["semantic-unknown", "overflow", "unsafe-zero-exit", "cancelled"],
)
def test_unsafe_or_inconclusive_attempts_never_retry(
    record_changes: dict[str, object], outcome: str
) -> None:
    # Given
    history = CallHistory(call(), (), ())
    record = attempt_record(1, "infrastructure", **record_changes)
    evidence = AttemptEvidence(
        "returned",
        None,
        None,
        None,
        history.call.request,
        "2026-01-01T00:00:00Z",
        None,
        None,
    )
    state = capture_attempt(Attempting(history, 1), evidence, record.retry_assessment)

    # When
    result = attempt_persisted(
        state, record, config(retry_limit=1, retry_nonzero_exit=True), None, None
    )

    # Then
    assert isinstance(result, Finished | Stopped)
    assert result.outcome == outcome
    assert result.history.attempts == (record,)


def test_failed_attempt_write_retains_error_without_durable_history() -> None:
    # Given
    history = CallHistory(call(), (), ())
    state = recording(history, 1, "infrastructure")
    error = OSError("write failed")

    # When
    result = attempt_write_failed(state, error)

    # Then
    assert result.failure.error is error
    assert result.failure.obligation is state.attempt
    assert result.history is history
    assert result.history.attempts == ()


def test_cancelled_submitted_wait_retains_closure_until_durable() -> None:
    # Given
    from dataclasses import replace

    history = CallHistory(call(), (attempt_record(1, "capacity"),), ())
    wait = replace(capacity_wait(1, 0), start_phase="submitted")
    state = RetryWait(history, wait)
    closure = WaitRecord(
        wait_id="wait",
        context=wait.context,
        started_at_utc=wait.started_at_utc,
        ended_at_utc="2026-01-01T00:00:02Z",
        elapsed_seconds=1.0,
        end="cancelled",
        diagnostic=None,
    )

    # When
    started = call_wait_started(state, CancelledError(), None, closure)
    result = call_wait_completed(started, closure, None)

    # Then
    assert started.wait.start_phase == "durable"
    assert started.wait.end_record is closure
    assert started.history.waits == ()
    assert isinstance(result, Stopped)
    assert result.outcome == "cancelled"
    assert result.history.waits == (closure,)


def test_mismatched_probe_evidence_never_becomes_a_record() -> None:
    # Given
    req = request()
    other = req.model_copy()
    evidence = QuotaProbeEvidence(
        other,
        AttemptEvidence(
            "returned",
            None,
            None,
            None,
            call().request,
            "2026-01-01T00:00:00Z",
            None,
            None,
        ),
        "available",
        observation(),
        None,
    )

    # When
    result = capture_probe(Probing(waiting(), req), evidence, None)

    # Then
    assert isinstance(result, ProbeEvidencePending)
    assert result.request is req
    assert isinstance(result.error, ValueError)
    assert result.evidence is None


def test_latched_stop_does_not_consume_leaf_cancellation() -> None:
    # Given
    from script.eval.runner.coordinator.state import StopReason

    history = CallHistory(call(), (), ())
    state = recording(history, 1, "infrastructure")
    record = attempt_record(
        1, "infrastructure", control_flow="cancelled", outcome_kind="cancelled"
    )
    stop = StopReason(RuntimeError("latched"), None, None, None)

    # When
    result = attempt_persisted(
        state, record, config(quota_wait_enabled=True), stop, None
    )

    # Then
    assert isinstance(result, Stopped)
    assert result.outcome == "cancelled"
    assert result.history.attempts == (record,)


def test_probe_journal_failure_retains_dispatched_request() -> None:
    # Given
    from script.eval.runner.coordinator.quota import quota_write_failed
    from script.eval.runner.coordinator.state import ProbeDispatched

    req = request()
    probing = Probing(waiting(), req)
    event = ProbeDispatched(req)
    error = OSError("journal failed")

    # When
    result = quota_write_failed(probing, event, error)

    # Then
    assert result.obligation is event
    assert result.error is error
    assert result.probe is probing
    assert result.probe.request is req


@pytest.mark.parametrize(
    ("changes", "end"),
    [
        ({"cleanup": None}, "unknown"),
        (
            {"observation": observation().model_copy(update={"valid_until_utc": None})},
            "unknown",
        ),
        ({"outcome_kind": "timed_out"}, "unknown"),
    ],
    ids=["unsafe-zero-exit", "missing-expiry", "timeout-zero-exit"],
)
def test_inconclusive_probe_never_closes_as_available(
    changes: dict[str, object], end: str
) -> None:
    # Given
    req = request()
    fields = process_fields()
    fields.update(
        request=req,
        quota_state="available",
        observation=observation(),
        classification_basis="controlled",
        exit_status=0,
    )
    fields.update(changes)
    record = QuotaProbeRecord.model_validate(fields)
    evidence = QuotaProbeEvidence(
        req,
        AttemptEvidence(
            "returned",
            None,
            None,
            None,
            call().request,
            "2026-01-01T00:00:00Z",
            None,
            None,
        ),
        record.quota_state,
        record.observation,
        "controlled",
    )

    # When
    history, pending = probe_persisted(
        RecordingProbe(waiting(), evidence),
        QuotaHistory((), ()),
        record,
        None,
        None,
        "2026-01-01T00:00:02Z",
        2.0,
    )

    # Then
    assert history.probes == (record,)
    assert pending.end_record is not None
    assert pending.end_record.end == end
