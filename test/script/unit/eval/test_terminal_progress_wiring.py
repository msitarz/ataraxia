# SPDX-License-Identifier: Apache-2.0
"""Terminal progress composition keeps output separate from run state."""

import asyncio
from unittest.mock import Mock, call

import pytest

from script.eval.runner.adapters.progress import (
    SilentProgressSink,
    TerminalProgressSink,
)
from script.eval.runner.coordinator.progress import project
from test.script.unit.eval.test_coordinator_progress import view


def test_silent_sink_discards_snapshot() -> None:
    """Quiet presentation needs no clock or output dependency."""
    assert SilentProgressSink().publish(project(view())) is None


def test_terminal_forwards_snapshot_clock_and_output_in_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One eligible snapshot flows through preparation, write, then settlement."""
    snapshot = project(view())
    events = Mock()
    runtime = Mock()
    runtime.monotonic.return_value = 12.5
    writer = Mock(return_value="written")
    sink = TerminalProgressSink(writer, True, runtime, 2.0)
    prepare = Mock(return_value="line")
    settle = Mock()
    monkeypatch.setattr(sink, "_prepare", prepare)
    monkeypatch.setattr(sink, "_settle", settle)
    events.attach_mock(runtime.monotonic, "clock")
    events.attach_mock(prepare, "prepare")
    events.attach_mock(writer, "write")
    events.attach_mock(settle, "settle")

    sink.publish(snapshot)

    assert events.mock_calls == [
        call.clock(),
        call.prepare(snapshot, 12.5),
        call.write("line"),
        call.settle(snapshot, 12.5, "written"),
    ]
    assert sink.is_tty is True
    assert sink.interval_seconds == pytest.approx(2.0)


def test_skipped_update_does_not_write_or_settle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A throttle decision can skip output without a queued write."""
    runtime, writer = Mock(), Mock()
    sink = TerminalProgressSink(writer, False, runtime, 1.0)
    settle = Mock()
    monkeypatch.setattr(sink, "_prepare", Mock(return_value=None))
    monkeypatch.setattr(sink, "_settle", settle)

    sink.publish(project(view()))

    writer.assert_not_called()
    settle.assert_not_called()


@pytest.mark.parametrize("result", ["would_block", "unavailable", OSError("closed")])
def test_output_failures_reach_settlement(
    result: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Expected transport failures are presented to the state owner."""
    runtime, writer = Mock(), Mock()
    runtime.monotonic.return_value = 8.0
    if isinstance(result, OSError):
        writer.side_effect = result
    else:
        writer.return_value = result
    sink = TerminalProgressSink(writer, False, runtime, 1.0)
    settle = Mock()
    monkeypatch.setattr(sink, "_prepare", Mock(return_value="line"))
    monkeypatch.setattr(sink, "_settle", settle)
    snapshot = project(view())

    sink.publish(snapshot)

    expected = "unavailable" if isinstance(result, OSError) else result
    settle.assert_called_once_with(snapshot, 8.0, expected)


@pytest.mark.parametrize(
    "error", [asyncio.CancelledError(), KeyboardInterrupt(), SystemExit()]
)
def test_interrupts_propagate(
    error: BaseException, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Output must not consume cancellation or process interrupts."""
    writer = Mock(side_effect=error)
    sink = TerminalProgressSink(writer, False, Mock(), 1.0)
    settle = Mock()
    monkeypatch.setattr(sink, "_prepare", Mock(return_value="line"))
    monkeypatch.setattr(sink, "_settle", settle)

    with pytest.raises(type(error)):
        sink.publish(project(view()))
    settle.assert_not_called()
