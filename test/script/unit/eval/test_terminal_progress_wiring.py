# SPDX-License-Identifier: Apache-2.0
"""Terminal progress composition keeps output separate from run state."""

import asyncio

import pytest

from script.eval.runner.adapters.progress import (
    SilentProgressSink,
    TerminalProgressSink,
    TryWriteResult,
)
from script.eval.runner.ports import ProgressCounts, ProgressSnapshot


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

    def monotonic(self) -> float:
        self.events.append(("clock",))
        return 12.5

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
        self, value: ProgressSnapshot, now: float, is_tty: bool, interval: float, /
    ) -> str | None:
        self.events.append(("prepare", value, now, is_tty, interval))
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
        ("prepare", value, 12.5, True, 2.0),
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
    assert events == [("clock",), ("prepare", value, 12.5, False, 1.0)]


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
        ("prepare", value, 12.5, False, 1.0),
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
        ("prepare", value, 12.5, False, 1.0),
        ("write", "line"),
    ]
