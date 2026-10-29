# SPDX-License-Identifier: Apache-2.0
"""Nonblocking terminal and silent progress sinks."""

from datetime import datetime, timedelta
from typing import Literal, Protocol

from script.eval.model import QuotaObservation, QuotaWindowObservation
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
    """Own rendering and throttle state for a terminal sink."""

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

    The caller supplies a prompt writer; no concrete stderr transport is
    supplied by this adapter.
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
            presentation if presentation is not None else _TerminalPresentation()
        )

    def publish(self, snapshot: ProgressSnapshot, /) -> None:
        """Prepare and attempt an update, isolating expected output failures.

        Cancellation and process interrupts propagate. Meaningful transitions
        bypass routine throttling; a skipped update makes no write attempt.
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


class _TerminalPresentation:
    """Track attempts and render bounded updates without retaining a queue."""

    def __init__(self) -> None:
        self.disabled = False
        self.last_attempt: float | None = None
        self.last_transition: object = None

    def prepare(
        self,
        snapshot: ProgressSnapshot,
        now: float,
        is_tty: bool,
        interval_seconds: float,
        /,
    ) -> str | None:
        """Render transitions immediately and routine updates at the interval.

        Returns:
            The next message, or None when no write is due.
        """
        if self.disabled:
            return None
        transition = _transition(snapshot)
        if (
            self.last_attempt is not None
            and transition == self.last_transition
            and now - self.last_attempt < interval_seconds
        ):
            return None
        return _render(snapshot, is_tty)

    def settle(
        self, snapshot: ProgressSnapshot, now: float, result: TryWriteResult, /
    ) -> None:
        """Bound retry cadence after a failed write and disable unavailable output."""
        self.last_attempt = now
        self.last_transition = _transition(snapshot)
        if result == "unavailable":
            self.disabled = True


def _transition(snapshot: ProgressSnapshot) -> object:
    """Identify meaningful changes without treating elapsed time as a transition.

    Returns:
        A comparable key for transition detection.
    """
    observation = snapshot.quota_observation
    quota = None if observation is None else (observation.scope, observation.windows)
    waits = tuple(
        (wait.call_id, wait.reason, wait.attempt_number) for wait in snapshot.call_waits
    )
    return (
        snapshot.run_id,
        snapshot.phase,
        snapshot.final_status,
        snapshot.counts,
        snapshot.retry_reasons,
        waits,
        quota,
    )


def _render(snapshot: ProgressSnapshot, is_tty: bool) -> str:
    """Produce one short display line, with explicit truncation when needed.

    Returns:
        A complete terminal or redirected message.
    """
    c = snapshot.counts
    remaining = (
        c.calls_queued
        + c.calls_stopped_not_started
        + c.calls_active
        + c.calls_retry_wait
        + c.calls_evidence_pending
    )
    calls = (
        f"calls completed/success={c.calls_succeeded} failed={c.calls_failed} "
        f"cancelled={c.calls_cancelled} remaining={remaining} "
        f"(queued={c.calls_queued} active={c.calls_active} "
        f"retry-wait={c.calls_retry_wait} "
        f"not-started={c.calls_stopped_not_started} "
        f"evidence-pending={c.calls_evidence_pending})"
    )
    attempts = (
        f"attempts started={c.attempts_started} active={c.attempts_active} "
        f"success={c.attempts_succeeded} failed={c.attempts_failed} "
        f"cancelled={c.attempts_cancelled} "
        f"evidence-pending={c.attempts_evidence_pending} "
        f"retries={c.retries_started}"
    )
    probes = (
        f"probes started={c.probes_started} active={c.probes_active} "
        f"completed={c.probes_completed} failed={c.probes_failed} "
        f"cancelled={c.probes_cancelled} evidence-pending={c.probes_evidence_pending}"
    )
    waits = (
        ",".join(
            f"{_safe(w.call_id)}:{w.reason}:attempt={w.attempt_number}:"
            f"elapsed={w.elapsed_seconds:.1f}s:"
            f"remaining={_number(w.remaining_seconds, 's')}"
            for w in snapshot.call_waits
        )
        or "none"
    )
    reasons = (
        ",".join(f"{reason}={count}" for reason, count in snapshot.retry_reasons)
        or "none"
    )
    status = snapshot.final_status or "none"
    line = (
        f"run={_safe(snapshot.run_id)} phase={snapshot.phase} final={status} | "
        f"{calls} | "
        f"{attempts} reasons={reasons} | {probes} | waits={waits} | {_quota(snapshot)}"
    )
    if len(line) > 4000:
        line = line[:3986] + "... [truncated]"
    return (
        ("\r\x1b[2K" + line + ("\n" if snapshot.phase == "final" else ""))
        if is_tty
        else line + "\n"
    )


def _quota(snapshot: ProgressSnapshot) -> str:
    """Format the supplied observation, preserving unknowns and source age.

    Returns:
        A quota status summary.
    """
    observation = snapshot.quota_observation
    if observation is None:
        return "quota=unknown"
    scope = observation.scope
    scope_text = (
        "unknown"
        if scope is None
        else f"{_safe(scope.provider_id)}/{_safe(scope.allowance_id)}"
    )
    ages = dict(snapshot.quota_window_ages_seconds)
    windows = (
        ";".join(
            _window(observation, window, ages.get(window.window_id))
            for window in observation.windows
        )
        or "unknown"
    )
    return f"quota scope={scope_text} windows={windows}"


def _window(
    observation: QuotaObservation, window: QuotaWindowObservation, age: float | None
) -> str:
    """Describe one quota window using only the supplied producer-based age.

    Returns:
        The window status and freshness summary.
    """
    freshness = _freshness(
        window.source_observed_at_utc, age, observation.valid_until_utc
    )
    reset = _safe(window.reset_at_utc) if window.reset_at_utc is not None else "unknown"
    return (
        f"{_safe(window.window_id)}:state={window.state}:"
        f"usage={_number(window.usage_percent, '%')}:"
        f"reset-hint={reset}:age={_number(age, 's')}:{freshness}"
    )


def _freshness(timestamp: str | None, age: float | None, expiry: str | None) -> str:
    """Compare the observed age with expiry without reading a clock.

    Returns:
        Fresh, stale, or unknown freshness.
    """
    if timestamp is None or age is None or expiry is None:
        return "freshness=unknown"
    try:
        observed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        until = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
        if observed.utcoffset() is None or until.utcoffset() is None:
            return "freshness=unknown"
        fresh = observed + timedelta(seconds=age) <= until
    except ValueError, OverflowError:
        return "freshness=unknown"
    return "freshness=fresh" if fresh else "freshness=stale"


def _number(value: float | None, suffix: str) -> str:
    """Format a supplied number or an explicitly unknown value.

    Returns:
        The formatted value.
    """
    return "unknown" if value is None else f"{value:.1f}{suffix}"


def _safe(value: str) -> str:
    """Keep identifiers on one line without terminal control characters.

    Returns:
        An escaped identifier.
    """
    escaped = ascii(value)[1:-1]
    return escaped if len(escaped) <= 100 else escaped[:97] + "..."
