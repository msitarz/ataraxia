# SPDX-License-Identifier: Apache-2.0
"""Intent placeholder for nonblocking terminal progress presentation."""

import pytest


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason=(
        "not implemented: AC-9 terminal progress is monotonic-throttled and nonblocking"
    ),
)
def test_terminal_progress_throttles_routine_updates_and_returns_promptly() -> None:
    """Keep unavailable stderr from delaying evaluation or dropping transitions."""
    # Given
    # An injected monotonic clock, a finite interval, and a try-write callback
    # that can report success, would-block, unavailable, or OSError.

    # When
    # Routine snapshots, retry/pause/resume/error/final transitions, and
    # cancellation or process interrupts reach the terminal sink.

    # Then
    # Routine updates coalesce by the injected clock; meaningful transitions
    # bypass throttling; unavailable output returns promptly and degrades
    # presentation; expected OSError is isolated; cancellation, KeyboardInterrupt,
    # and SystemExit propagate. No thread, queue, or stream-flag mutation occurs.
    pass
