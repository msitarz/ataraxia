# SPDX-License-Identifier: Apache-2.0
"""Terminal and silent implementations of the progress sink port."""

from typing import Literal, Protocol

from ..ports import ProgressSnapshot, Runtime  # ruff: ignore[relative-imports]

type TryWriteResult = Literal["written", "would_block", "unavailable"]

class TryWrite(Protocol):
    """Nonblocking one-message stderr write supplied by composition.

    Return ``written`` only when the complete short message was accepted;
    return ``would_block`` or ``unavailable`` without waiting. An expected
    ``OSError`` may be raised. Never mutate caller stream flags or queue output.
    """

    def __call__(self, text: str, /) -> TryWriteResult: ...

class SilentProgressSink:
    """Discard progress snapshots without touching the run or evidence."""

    def publish(self, snapshot: ProgressSnapshot, /) -> None: ...

class TerminalProgressSink:
    """Use a prompt try-write adapter for terminal or redirected stderr."""

    try_write: TryWrite
    is_tty: bool
    runtime: Runtime
    interval_seconds: float

    def __init__(
        self,
        try_write: TryWrite,
        is_tty: bool,
        runtime: Runtime,
        interval_seconds: float,
        /,
    ) -> None: ...
    def publish(self, snapshot: ProgressSnapshot, /) -> None:
        """Try one update and return promptly when output would block.

        Routine updates use the injected runtime's monotonic clock and finite
        interval. Meaningful transitions bypass throttling. Would-block,
        unavailable output, or OSError skips or disables presentation; no
        blocking stream write, thread, or renderer queue is used.
        """
        ...
