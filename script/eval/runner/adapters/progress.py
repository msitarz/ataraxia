# SPDX-License-Identifier: Apache-2.0
"""Wired terminal and silent progress sinks; presentation leaves are pending."""

from typing import Literal, Protocol

from script.eval.runner.ports import ProgressSnapshot, Runtime

type TryWriteResult = Literal["written", "would_block", "unavailable"]


class TryWrite(Protocol):
    """Promptly accept one complete short message or report it cannot be written.

    An expected ``OSError`` may be raised. The callback must not wait, queue
    output, or mutate stream flags. Composition owns the transport.
    """

    def __call__(self, text: str, /) -> TryWriteResult:
        """Try one complete message without waiting."""
        ...


class Presentation(Protocol):
    """Own pending rendering and throttle state for a terminal sink."""

    def prepare(
        self,
        snapshot: ProgressSnapshot,
        now: float,
        is_tty: bool,
        interval_seconds: float,
        /,
    ) -> str | None:
        """Select and render an update, or skip it."""
        ...

    def settle(
        self, snapshot: ProgressSnapshot, now: float, result: TryWriteResult, /
    ) -> None:
        """Record the outcome of an attempted write."""
        ...


class SilentProgressSink:
    """Discard snapshots without touching evaluation or evidence."""

    def publish(self, snapshot: ProgressSnapshot, /) -> None:
        """Discard a snapshot."""


class TerminalProgressSink:
    """Compose a monotonic presentation decision with a prompt try-write port.

    Rendering and throttle state are unfinished. No concrete stderr transport
    is supplied by this adapter.
    """

    def __init__(
        self,
        try_write: TryWrite,
        is_tty: bool,
        runtime: Runtime,
        interval_seconds: float,
        /,
        *,
        presentation: Presentation | None = None,
    ) -> None:
        """Retain the composition dependencies for synchronous publication."""
        self.try_write = try_write
        self.is_tty = is_tty
        self.runtime = runtime
        self.interval_seconds = interval_seconds
        self._presentation = (
            presentation if presentation is not None else _PendingPresentation()
        )

    def publish(self, snapshot: ProgressSnapshot, /) -> None:
        """Prepare and attempt an update, isolating expected output failures.

        Cancellation and process interrupts propagate. The pending preparation
        leaf will use monotonic time for throttling and bypass it for meaningful
        transitions; a skipped update makes no write attempt.
        """
        now = self.runtime.monotonic()
        message = self._presentation.prepare(
            snapshot, now, self.is_tty, self.interval_seconds
        )
        if message is None:
            return
        try:
            result = self.try_write(message)
        except OSError:
            result = "unavailable"
        self._presentation.settle(snapshot, now, result)


class _PendingPresentation:
    """Placeholder for terminal rendering and state."""

    def prepare(
        self,
        snapshot: ProgressSnapshot,
        now: float,
        is_tty: bool,
        interval_seconds: float,
        /,
    ) -> str | None:
        """Select and render an update using throttle and terminal mode."""
        raise NotImplementedError

    def settle(
        self, snapshot: ProgressSnapshot, now: float, result: TryWriteResult, /
    ) -> None:
        """Record presentation state after the prompt write attempt."""
        raise NotImplementedError
