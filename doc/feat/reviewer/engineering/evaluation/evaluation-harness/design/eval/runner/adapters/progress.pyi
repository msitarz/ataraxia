# SPDX-License-Identifier: Apache-2.0
"""Terminal and silent implementations of the progress sink port."""

from typing import TextIO

from ..ports import ProgressSnapshot  # ruff: ignore[relative-imports]

class SilentProgressSink:
    """Discard progress snapshots without touching the run or evidence."""

    def publish(self, snapshot: ProgressSnapshot, /) -> None: ...

class TerminalProgressSink:
    """Render compact progress to stderr, using plain lines when redirected."""

    stream: TextIO
    is_tty: bool

    def __init__(self, stream: TextIO, is_tty: bool, /) -> None: ...
    def publish(self, snapshot: ProgressSnapshot, /) -> None:
        """Write one throttled update; disable on ordinary stream write failure.

        The synchronous write is small and transition-driven, with no queued
        renderer task. A blocked stderr write can delay coordinator progress;
        cancellation is delivered when control returns to the event loop.
        """
        ...
