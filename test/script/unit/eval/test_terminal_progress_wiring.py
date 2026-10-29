# SPDX-License-Identifier: Apache-2.0
"""Terminal progress composition keeps output separate from run state."""

import asyncio
from dataclasses import replace

import pytest

from script.eval.model import (
    QuotaAllowanceId,
    QuotaObservation,
    QuotaProviderId,
    QuotaScope,
    QuotaWindowId,
    QuotaWindowObservation,
)
from script.eval.runner.adapters.progress import (
    SilentProgressSink,
    TerminalProgressSink,
    TryWriteResult,
)
from script.eval.runner.ports import CallWait, ProgressCounts, ProgressSnapshot


def snapshot() -> ProgressSnapshot:
    """Provide one empty running snapshot for forwarding checks."""
    return ProgressSnapshot(
        "run",
        "running",
        None,
        ProgressCounts(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        (),
        (),
        None,
        (),
    )


class Clock:
    """Provide the runtime port and record monotonic clock use."""

    def __init__(self, events: list[object]) -> None:
        self.events = events
        self.now = 12.5

    def monotonic(self) -> float:
        self.events.append(("clock",))
        return self.now

    def utc_now(self) -> str:
        raise AssertionError("unexpected UTC clock")

    async def sleep(self, seconds: float, /) -> None:
        raise AssertionError("unexpected sleep")

    def uniform(self, lower: float, upper: float, /) -> float:
        raise AssertionError("unexpected randomness")


class Presentation:
    """Record the injected pending presentation operations."""

    def __init__(self, events: list[object], message: str | None) -> None:
        self.events = events
        self.message = message

    def prepare(
        self,
        value: ProgressSnapshot,
        now: float,
        is_tty: bool,
        interval: float,
        tty_columns: int,
        /,
    ) -> str | None:
        self.events.append(("prepare", value, now, is_tty, interval, tty_columns))
        return self.message

    def settle(
        self, value: ProgressSnapshot, now: float, result: TryWriteResult, /
    ) -> None:
        self.events.append(("settle", value, now, result))


class Writer:
    """Record one prompt write or raise its configured exception."""

    def __init__(
        self,
        events: list[object],
        result: TryWriteResult = "written",
        error: BaseException | None = None,
    ) -> None:
        self.events = events
        self.result = result
        self.error = error

    def __call__(self, text: str, /) -> TryWriteResult:
        self.events.append(("write", text))
        if self.error is not None:
            raise self.error
        return self.result


def test_silent_sink_discards_snapshot() -> None:
    # Given
    value = snapshot()

    # When
    result = SilentProgressSink().publish(value)

    # Then
    assert result is None


def test_terminal_forwards_snapshot_clock_and_output_in_order() -> None:
    # Given
    events: list[object] = []
    value = snapshot()
    sink = TerminalProgressSink(
        Writer(events),
        True,
        Clock(events),
        2.0,
        presentation=Presentation(events, "line"),
    )

    # When
    sink.publish(value)

    # Then
    assert events == [
        ("clock",),
        ("prepare", value, 12.5, True, 2.0, 80),
        ("write", "line"),
        ("settle", value, 12.5, "written"),
    ]


def test_skipped_update_does_not_write_or_settle() -> None:
    # Given
    events: list[object] = []
    value = snapshot()
    sink = TerminalProgressSink(
        Writer(events),
        False,
        Clock(events),
        1.0,
        presentation=Presentation(events, None),
    )

    # When
    sink.publish(value)

    # Then
    assert events == [("clock",), ("prepare", value, 12.5, False, 1.0, 80)]


@pytest.mark.parametrize(
    ("result", "error", "expected"),
    [
        ("would_block", None, "would_block"),
        ("unavailable", None, "unavailable"),
        ("written", OSError("closed"), "unavailable"),
    ],
    ids=["would-block", "unavailable", "os-error"],
)
def test_output_failures_reach_settlement(
    result: TryWriteResult,
    error: OSError | None,
    expected: TryWriteResult,
) -> None:
    # Given
    events: list[object] = []
    value = snapshot()
    sink = TerminalProgressSink(
        Writer(events, result, error),
        False,
        Clock(events),
        1.0,
        presentation=Presentation(events, "line"),
    )

    # When
    sink.publish(value)

    # Then
    assert events == [
        ("clock",),
        ("prepare", value, 12.5, False, 1.0, 80),
        ("write", "line"),
        ("settle", value, 12.5, expected),
    ]


@pytest.mark.parametrize(
    "error",
    [asyncio.CancelledError(), KeyboardInterrupt(), SystemExit()],
    ids=["cancellation", "keyboard-interrupt", "system-exit"],
)
def test_interrupts_propagate(error: BaseException) -> None:
    # Given
    events: list[object] = []
    value = snapshot()
    sink = TerminalProgressSink(
        Writer(events, error=error),
        False,
        Clock(events),
        1.0,
        presentation=Presentation(events, "line"),
    )

    # When
    with pytest.raises(type(error)) as caught:
        sink.publish(value)

    # Then
    assert caught.value is error
    assert events == [
        ("clock",),
        ("prepare", value, 12.5, False, 1.0, 80),
        ("write", "line"),
    ]


def test_default_presentation_throttles_routine_updates_and_reports_transitions() -> (
    None
):
    # Given
    events: list[object] = []
    clock = Clock(events)
    sink = TerminalProgressSink(Writer(events), False, clock, 2.0)
    initial = snapshot()
    paused = replace(initial, phase="quota_paused")

    # When
    sink.publish(initial)
    clock.now = 14.4
    sink.publish(initial)
    clock.now = 14.5
    sink.publish(initial)
    sink.publish(paused)

    # Then
    writes = [
        event for event in events if isinstance(event, tuple) and event[0] == "write"
    ]
    assert len(writes) == 3
    assert "phase=running" in writes[0][1]
    assert "phase=quota_paused" in writes[2][1]
    assert all(event[1].endswith("\n") and "\x1b" not in event[1] for event in writes)


def test_final_tty_report_keeps_disjoint_counts_and_status() -> None:
    # Given
    events: list[object] = []
    value = snapshot()
    counts = replace(
        value.counts,
        calls_succeeded=2,
        calls_failed=1,
        calls_cancelled=1,
        calls_stopped_not_started=1,
        calls_evidence_pending=1,
        attempts_started=4,
        attempts_succeeded=2,
        attempts_failed=1,
        attempts_cancelled=1,
        retries_started=1,
        probes_started=1,
        probes_completed=1,
    )
    final = replace(
        value, phase="final", final_status="incomplete_evidence", counts=counts
    )
    sink = TerminalProgressSink(Writer(events), True, Clock(events), 1.0)

    # When
    sink.publish(final)

    # Then
    event = events[1]
    assert isinstance(event, tuple)
    line = event[1]
    assert line.startswith("\r\x1b[2Krun=run phase=final final=incomplete_evidence")
    assert "calls completed=4 success=2 failed=1 cancelled=1 remaining=2" in line
    assert "not-started=1 evidence-pending=1" in line
    assert "attempts started=4 active=0 success=2 failed=1 cancelled=1" in line
    assert "retries=1" in line
    assert "probes started=1 active=0 completed=1 failed=0 cancelled=0" in line
    assert line.endswith("quota=unknown\n")


@pytest.mark.parametrize(
    ("result", "error", "expected_writes"),
    [
        ("would_block", None, 2),
        ("unavailable", None, 1),
        ("written", OSError("closed"), 1),
    ],
    ids=[
        "would-block-retries-at-interval",
        "unavailable-disables",
        "os-error-disables",
    ],
)
def test_default_presentation_degrades_output_without_blocking(
    result: TryWriteResult,
    error: OSError | None,
    expected_writes: int,
) -> None:
    # Given
    events: list[object] = []
    clock = Clock(events)
    sink = TerminalProgressSink(Writer(events, result, error), False, clock, 2.0)
    value = snapshot()

    # When
    sink.publish(value)
    clock.now = 14.4
    sink.publish(value)
    clock.now = 14.5
    sink.publish(value)

    # Then
    assert (
        len([
            event
            for event in events
            if isinstance(event, tuple) and event[0] == "write"
        ])
        == expected_writes
    )


def test_quota_uses_supplied_age_and_preserves_stale_and_unknown() -> None:
    # Given
    events: list[object] = []
    window = QuotaWindowObservation(
        window_id=QuotaWindowId("weekly"),
        state="exhausted",
        usage_percent=98.0,
        reset_at_utc="2026-01-03T00:00:00Z",
        source_observed_at_utc="2026-01-01T00:00:00Z",
        source_sequence=None,
        source=None,
        diagnostic=None,
    )
    unknown = QuotaWindowObservation(
        window_id=QuotaWindowId("five-hour"),
        state="unknown",
        usage_percent=None,
        reset_at_utc=None,
        source_observed_at_utc=None,
        source_sequence=None,
        source=None,
        diagnostic=None,
    )
    observation = QuotaObservation(
        scope=QuotaScope(
            provider_id=QuotaProviderId("provider"),
            allowance_id=QuotaAllowanceId("scope"),
        ),
        read_at_utc="2026-01-01T00:00:20Z",
        source_coordinate=None,
        windows=(window, unknown),
        diagnostic=None,
        valid_until_utc="2026-01-01T00:00:10Z",
    )
    value = replace(
        snapshot(),
        quota_observation=observation,
        quota_window_ages_seconds=((QuotaWindowId("weekly"), 20.0),),
    )
    sink = TerminalProgressSink(Writer(events), False, Clock(events), 1.0)

    # When
    sink.publish(value)

    # Then
    event = events[1]
    assert isinstance(event, tuple)
    line = event[1]
    assert "quota scope=provider/scope" in line
    assert (
        "weekly:state=exhausted:usage=98.0%:reset-hint=2026-01-03T00:00:00Z:age=20.0s:freshness=stale"
        in line
    )
    assert (
        "five-hour:state=unknown:usage=unknown:reset-hint=unknown:age=unknown:freshness=unknown"
        in line
    )


@pytest.mark.parametrize(
    "error",
    [asyncio.CancelledError(), KeyboardInterrupt(), SystemExit()],
    ids=["cancellation", "keyboard-interrupt", "system-exit"],
)
def test_default_presentation_propagates_interrupt_identity(
    error: BaseException,
) -> None:
    # Given
    events: list[object] = []
    sink = TerminalProgressSink(Writer(events, error=error), False, Clock(events), 1.0)

    # When
    with pytest.raises(type(error)) as caught:
        sink.publish(snapshot())

    # Then
    assert caught.value is error


def test_wait_elapsed_changes_do_not_bypass_throttle() -> None:
    # Given
    events: list[object] = []
    clock = Clock(events)
    wait = CallWait("call", "capacity", 1, 1.0, 4.0)
    value = replace(snapshot(), call_waits=(wait,))
    updated = replace(
        value, call_waits=(replace(wait, elapsed_seconds=2.0, remaining_seconds=3.0),)
    )
    sink = TerminalProgressSink(Writer(events), False, clock, 2.0)

    # When
    sink.publish(value)
    clock.now = 13.5
    sink.publish(updated)
    clock.now = 14.5
    sink.publish(updated)

    # Then
    writes = [
        event for event in events if isinstance(event, tuple) and event[0] == "write"
    ]
    assert len(writes) == 2
    assert "call:capacity:attempt=1:elapsed=1.0s:remaining=4.0s" in writes[0][1]
    assert "call:capacity:attempt=1:elapsed=2.0s:remaining=3.0s" in writes[1][1]


@pytest.mark.parametrize("columns", [12, 80], ids=["narrow", "typical"])
def test_repeated_tty_refreshes_fit_a_single_unwrapped_row(columns: int) -> None:
    # Given
    events: list[object] = []
    clock = Clock(events)
    value = snapshot()
    sink = TerminalProgressSink(Writer(events), True, clock, 1.0, tty_columns=columns)

    # When
    sink.publish(value)
    sink.publish(replace(value, phase="quota_paused"))

    # Then
    writes = [
        event[1] for event in events if isinstance(event, tuple) and event[0] == "write"
    ]
    assert len(writes) == 2
    assert all(line.startswith("\r\x1b[2K") for line in writes)
    assert all("\n\r\x1b[2K" in line for line in writes)
    assert all(len(line.rsplit("\r\x1b[2K", 1)[1]) < columns for line in writes)


def test_final_status_bypasses_routine_interval() -> None:
    # Given
    events: list[object] = []
    value = snapshot()
    sink = TerminalProgressSink(Writer(events), True, Clock(events), 10.0)

    # When
    sink.publish(value)
    sink.publish(replace(value, phase="final", final_status="success"))

    # Then
    writes = [
        event[1] for event in events if isinstance(event, tuple) and event[0] == "write"
    ]
    assert len(writes) == 2
    assert writes[1].startswith("\r\x1b[2Krun=run phase=final final=success")
    assert writes[1].endswith("\n")


def test_quota_age_is_routine_but_unknown_and_expiry_changes_are_transitions() -> None:
    # Given
    events: list[object] = []
    clock = Clock(events)
    window = QuotaWindowObservation(
        window_id=QuotaWindowId("weekly"),
        state="available",
        usage_percent=20.0,
        reset_at_utc=None,
        source_observed_at_utc="2026-01-01T00:00:00Z",
        source_sequence=None,
        source=None,
        diagnostic=None,
    )
    observation = QuotaObservation(
        scope=None,
        read_at_utc="2026-01-01T00:00:00Z",
        source_coordinate=None,
        windows=(window,),
        diagnostic=None,
        valid_until_utc="2026-01-01T00:00:10Z",
    )
    value = replace(
        snapshot(),
        quota_observation=observation,
        quota_window_ages_seconds=((QuotaWindowId("weekly"), 1.0),),
    )
    aged = replace(value, quota_window_ages_seconds=((QuotaWindowId("weekly"), 2.0),))
    expiry = replace(
        aged, quota_observation=observation.model_copy(update={"valid_until_utc": None})
    )
    unknown = replace(expiry, quota_observation=None)
    sink = TerminalProgressSink(Writer(events), False, clock, 10.0)

    # When
    sink.publish(value)
    sink.publish(aged)
    sink.publish(expiry)
    sink.publish(unknown)

    # Then
    writes = [
        event[1] for event in events if isinstance(event, tuple) and event[0] == "write"
    ]
    assert len(writes) == 3
    assert "age=1.0s:freshness=fresh" in writes[0]
    assert "age=2.0s:freshness=unknown" in writes[1]
    assert writes[2].endswith("quota=unknown\n")


def test_large_redirected_report_bounds_details_and_escapes_control_characters() -> (
    None
):
    # Given
    events: list[object] = []
    value = snapshot()
    waits = tuple(
        CallWait(f"call\x1b[{index}\n", "capacity", 1, 1.0, 2.0) for index in range(100)
    )
    counts = replace(
        value.counts,
        calls_succeeded=2,
        calls_failed=1,
        calls_cancelled=1,
        calls_stopped_not_started=1,
    )
    final = replace(
        value,
        run_id="run\n\x1b[31m",
        counts=counts,
        call_waits=waits,
        phase="final",
        final_status="failure",
    )
    sink = TerminalProgressSink(Writer(events), False, Clock(events), 1.0)

    # When
    sink.publish(final)

    # Then
    event = events[1]
    assert isinstance(event, tuple)
    line = event[1]
    assert len(line) <= 4001
    assert line.count("\n") == 1 and "\x1b" not in line
    assert "run=run\\n\\x1b[31m phase=final final=failure" in line
    assert "calls completed=4 success=2 failed=1 cancelled=1 remaining=1" in line
    assert "not-started=1" in line and "[truncated]" in line


def test_tty_quota_and_wait_transitions_show_details_without_count_floods() -> None:
    # Given
    events: list[object] = []
    window = QuotaWindowObservation(
        window_id=QuotaWindowId("weekly"),
        state="exhausted",
        usage_percent=98.0,
        reset_at_utc="2026-01-03T00:00:00Z",
        source_observed_at_utc="2026-01-01T00:00:00Z",
        source_sequence=None,
        source=None,
        diagnostic=None,
    )
    observation = QuotaObservation(
        scope=None,
        read_at_utc="2026-01-01T00:00:20Z",
        source_coordinate=None,
        windows=(window,),
        diagnostic=None,
        valid_until_utc="2026-01-01T00:00:10Z",
    )
    value = snapshot()
    paused = replace(
        value,
        phase="quota_paused",
        quota_observation=observation,
        quota_window_ages_seconds=((QuotaWindowId("weekly"), 20.0),),
    )
    waiting = replace(paused, call_waits=(CallWait("call", "capacity", 1, 2.0, 3.0),))
    counts = replace(
        waiting.counts, attempts_active=1, retries_started=1, probes_active=1
    )
    counted = replace(waiting, counts=counts)
    clock = Clock(events)
    sink = TerminalProgressSink(Writer(events), True, clock, 10.0)

    # When
    sink.publish(value)
    sink.publish(paused)
    sink.publish(waiting)
    sink.publish(counted)
    clock.now = 22.5
    sink.publish(counted)

    # Then
    writes = [
        event[1] for event in events if isinstance(event, tuple) and event[0] == "write"
    ]
    assert len(writes) == 4
    assert (
        "weekly:state=exhausted:usage=98.0%:reset-hint=2026-01-03T00:00:00Z:age=20.0s:freshness=stale"
        in writes[1]
    )
    assert "call:capacity:attempt=1:elapsed=2.0s:remaining=3.0s" in writes[2]
    assert "\n" not in writes[3] and "a=1 r=1 p=1" in writes[3]
    assert all(line.startswith("\r\x1b[2K") for line in writes)
    assert all(len(line.rsplit("\r\x1b[2K", 1)[1]) < 80 for line in writes)
