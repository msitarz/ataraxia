# SPDX-License-Identifier: Apache-2.0
"""Projection counts state and durable evidence without a second ledger."""

from dataclasses import replace

import pytest

from script.eval.model import QuotaProbeRecord, QuotaTelemetryEvent
from script.eval.runner.coordinator.call_states import (
    Attempting,
    CallHistory,
    CallState,
    Finished,
    ObservingQuota,
    Queued,
    RecordingTelemetry,
    RetryWait,
    Stopped,
)
from script.eval.runner.coordinator.progress import (
    ProgressView,
    _safe_completion,
    project,
)
from script.eval.runner.coordinator.quota_states import (
    Open,
    PreparingProbe,
    ProbeEvidencePending,
    ProbePrepared,
    Probing,
    QuotaEvidencePending,
    QuotaHistory,
)
from test.script.unit.eval.test_coordinator_states import (
    attempt_record,
    call,
    capacity_wait,
    observation,
    process_fields,
    recording,
    request,
    waiting,
)


def view(*calls: CallState) -> ProgressView:
    """Build an otherwise empty snapshot for typed state examples."""
    return ProgressView(
        "run",
        "running",
        None,
        calls,
        Open(),
        QuotaHistory((), ()),
        None,
        3.0,
        "2026-01-01T00:00:03Z",
    )


@pytest.mark.parametrize(
    ("kind", "bucket"),
    [
        ("queued", "calls_queued"),
        ("attempting", "calls_active"),
        ("recording", "calls_active"),
        ("observing", "calls_active"),
        ("telemetry", "calls_active"),
        ("retry", "calls_retry_wait"),
        ("pending", "calls_evidence_pending"),
        ("success", "calls_succeeded"),
        ("failure", "calls_failed"),
        ("cancelled", "calls_cancelled"),
        ("not_started", "calls_stopped_not_started"),
    ],
)
def test_call_partition(kind: str, bucket: str) -> None:
    """Each planned position occupies exactly one call bucket."""
    empty = CallHistory(call(), (), ())
    history = replace(empty, attempts=(attempt_record(1, "capacity"),))
    captured = recording(empty, 1, "capacity")
    event = QuotaTelemetryEvent(
        run_id="run", call_id="call", attempt_number=1, observation=observation()
    )
    states = {
        "queued": Queued(empty),
        "attempting": Attempting(empty, 1),
        "recording": captured,
        "observing": ObservingQuota(history, 1, captured.attempt.evidence),
        "telemetry": RecordingTelemetry(history, event),
        "retry": RetryWait(history, capacity_wait(1, 0)),
        "pending": captured.write_failed(OSError()),
        "success": Finished(history, "success"),
        "failure": Finished(history, "failure"),
        "cancelled": Stopped(history, "cancelled"),
        "not_started": Stopped(empty, "cancelled"),
    }
    counts = project(view(states[kind])).counts
    values = [
        getattr(counts, name)
        for name in counts.__dataclass_fields__
        if name.startswith("calls_")
    ]
    assert getattr(counts, bucket) == 1
    assert sum(values) == 1


def test_durable_attempts_and_pending_obligations_are_disjoint() -> None:
    """Telemetry failure leaves its attempt terminal; attempt failure does not."""
    empty = CallHistory(call(), (), ())
    good = attempt_record(1, "capacity", exit_status=0)
    history = replace(empty, attempts=(good,))
    event = QuotaTelemetryEvent(
        run_id="run", call_id="call", attempt_number=1, observation=observation()
    )
    telemetry = RecordingTelemetry(history, event).write_failed(OSError())
    pending = recording(history, 2, "capacity").write_failed(OSError())
    counts = project(view(telemetry, pending)).counts
    assert (
        counts.calls_evidence_pending,
        counts.attempts_started,
        counts.attempts_succeeded,
        counts.attempts_evidence_pending,
        counts.retries_started,
    ) == (2, 3, 2, 1, 1)
    assert project(view(pending)).retry_reasons == (("capacity", 1),)


@pytest.mark.parametrize(
    ("changes", "bucket"),
    [
        ({"exit_status": 0}, "attempts_succeeded"),
        ({"exit_status": 0, "outcome_kind": "timed_out"}, "attempts_failed"),
        ({"exit_status": 0, "cleanup": None}, "attempts_failed"),
        (
            {"control_flow": "cancelled", "outcome_kind": "cancelled"},
            "attempts_cancelled",
        ),
    ],
)
def test_attempt_terminal_outcomes(changes: dict[str, object], bucket: str) -> None:
    """Zero exit cannot override timeout, unsafe cleanup, or cancellation."""
    history = CallHistory(call(), (attempt_record(1, "capacity", **changes),), ())
    counts = project(view(Finished(history, "failure"))).counts
    assert getattr(counts, bucket) == 1
    assert counts.attempts_started == 1


def test_probe_preparation_and_nested_pending_are_distinct() -> None:
    """Preparation has no invocation; a journal failure retains the live probe."""
    req = request()
    prepared = PreparingProbe(waiting(), ProbePrepared(req.schedule, "wait"))
    probing = Probing(waiting(), req)
    failed = ProbeEvidencePending(waiting(), req, None, OSError())
    journal = QuotaEvidencePending(waiting(), prepared.preparation, OSError(), failed)
    base = view()
    assert project(replace(base, quota=prepared)).counts.probes_started == 0
    assert project(replace(base, quota=probing)).counts.probes_active == 1
    counts = project(replace(base, quota=journal)).counts
    assert (
        counts.probes_started,
        counts.probes_evidence_pending,
        counts.probes_active,
    ) == (1, 1, 0)


@pytest.mark.parametrize(
    ("state", "exit_status", "bucket"),
    [
        ("available", 0, "probes_completed"),
        ("exhausted", 1, "probes_completed"),
        ("available", 1, "probes_failed"),
        ("unknown", 0, "probes_failed"),
    ],
)
def test_durable_probe_outcomes(state: str, exit_status: int, bucket: str) -> None:
    """Conclusive exhausted checks may return nonzero; unknown checks fail."""
    fields = process_fields()
    fields.update(
        request=request(),
        quota_state=state,
        observation=observation(),
        classification_basis="test",
        exit_status=exit_status,
    )
    record = QuotaProbeRecord.model_validate(fields)
    counts = project(replace(view(), probes=QuotaHistory((), (record,)))).counts
    assert counts.probes_started == 1
    assert getattr(counts, bucket) == 1


@pytest.mark.parametrize(
    ("timestamp", "expected"),
    [
        ("2026-01-01T00:00:01Z", 2.0),
        (None, None),
        ("bad", None),
        ("2026-01-01T00:00:01", None),
        ("2026-01-01T00:00:04Z", None),
    ],
)
def test_age_uses_producer_time(timestamp: str | None, expected: float | None) -> None:
    """Missing, malformed, naive, and future producer times stay unknown."""
    obs = observation()
    window = obs.windows[0].model_copy(update={"source_observed_at_utc": timestamp})
    obs = obs.model_copy(update={"windows": (window,)})
    result = project(replace(view(), observation=obs))
    assert result.quota_observation is obs
    assert result.quota_window_ages_seconds == ((window.window_id, expected),)


def test_capacity_wait_uses_explicit_monotonic_clock() -> None:
    """Elapsed and remaining time never become negative."""
    history = CallHistory(call(), (attempt_record(1, "capacity"),), ())
    wait = replace(
        capacity_wait(1, 0),
        context=capacity_wait(1, 0).context.model_copy(update={"sampled_seconds": 5.0}),
    )
    result = project(view(RetryWait(history, wait)))
    assert (
        result.call_waits[0].elapsed_seconds,
        result.call_waits[0].remaining_seconds,
    ) == (2.0, 3.0)
    assert result.counts.retries_started == 0


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        ({}, True),
        ({"control_flow": "cancelled"}, False),
        ({"outcome_kind": "timed_out"}, False),
        ({"cleanup": None}, False),
    ],
)
def test_safe_completion_requires_return_and_owned_cleanup(
    changes: dict[str, object], expected: bool
) -> None:
    """A settled process must be returned and safely owned to complete."""
    assert _safe_completion(attempt_record(1, "capacity", **changes)) is expected
