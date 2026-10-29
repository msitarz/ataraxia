# SPDX-License-Identifier: Apache-2.0
"""Nonblocking terminal and silent progress sinks."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import islice
from typing import Literal, Protocol

from script.eval.model import (
    QuotaObservation,
    QuotaScope,
    QuotaWindowId,
    QuotaWindowObservation,
    RetryClass,
)
from script.eval.runner.ports import (
    ProgressCounts,
    ProgressFinalStatus,
    ProgressRunPhase,
    ProgressSnapshot,
    Runtime,
)

type Admission = Literal["accepted", "dropped", "unavailable"]


class ProgressAdmission(Protocol):
    """Offer one bounded message promptly; acceptance is not delivery."""

    def __call__(self, text: str, /) -> Admission:
        """Admit, drop, or refuse a message without waiting."""
        ...


class Presentation(Protocol):
    """Own rendering and throttle state for a terminal sink."""

    def prepare(
        self,
        snapshot: ProgressSnapshot,
        now: float,
        is_tty: bool,
        interval_seconds: float,
        tty_columns: int,
        /,
    ) -> str | None:
        """Select and render an update, or skip it."""
        ...

    def settle(
        self, snapshot: ProgressSnapshot, now: float, result: Admission, /
    ) -> None:
        """Record the outcome of an attempted write."""
        ...


class SilentProgressSink:
    """Discard snapshots without touching evaluation or evidence."""

    def publish(self, snapshot: ProgressSnapshot, /) -> None:
        """Discard a snapshot."""


class TerminalProgressSink:
    """Compose a monotonic presentation decision with prompt admission."""

    def __init__(
        self,
        admit: ProgressAdmission,
        is_tty: bool,
        runtime: Runtime,
        interval_seconds: float,
        /,
        *,
        presentation: Presentation | None = None,
        tty_columns: int = 80,
    ) -> None:
        """Retain the composition dependencies for synchronous publication.

        Raises:
            ValueError: The supplied terminal width is less than two columns.
        """
        if tty_columns < 2:
            raise ValueError("tty_columns must be at least 2")
        self.tty_columns = tty_columns
        self.admit = admit
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
            snapshot, now, self.is_tty, self.interval_seconds, self.tty_columns
        )
        if message is None:
            return
        try:
            result = self.admit(_bounded(message))
        except OSError:
            result = "unavailable"
        self._presentation.settle(snapshot, now, result)


class _TerminalPresentation:
    """Track attempts and render bounded updates without retaining a queue."""

    def __init__(self) -> None:
        self.disabled = False
        self.last_attempt: float | None = None
        self.last_transition: _Transition | None = None

    def prepare(
        self,
        snapshot: ProgressSnapshot,
        now: float,
        is_tty: bool,
        interval_seconds: float,
        tty_columns: int,
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
            and not _detail_changed(self.last_transition, transition)
            and now - self.last_attempt < interval_seconds
        ):
            return None
        if is_tty and snapshot.phase != "final":
            return (
                "\r\x1b[2K"
                + _render(snapshot, False, tty_columns)
                + _live_line(snapshot, tty_columns)
            )
        return _render(snapshot, is_tty, tty_columns)

    def settle(
        self, snapshot: ProgressSnapshot, now: float, result: Admission, /
    ) -> None:
        """Bound retry cadence after a failed write and disable unavailable output."""
        self.last_attempt = now
        self.last_transition = _transition(snapshot)
        if result == "unavailable":
            self.disabled = True


@dataclass(frozen=True)
class _Transition:
    """Snapshot facts whose changes warrant immediate presentation."""

    run_id: str
    phase: ProgressRunPhase
    final_status: ProgressFinalStatus | None
    counts: ProgressCounts
    retry_reasons: tuple[tuple[RetryClass, int], ...]
    waits: tuple[tuple[str, Literal["infrastructure", "capacity"], int], ...]
    quota: (
        tuple[QuotaScope | None, tuple[QuotaWindowObservation, ...], str | None] | None
    )


def _transition(snapshot: ProgressSnapshot) -> _Transition:
    """Identify meaningful changes without treating elapsed time as a transition.

    Returns:
        A comparable key for transition detection.
    """
    observation = snapshot.quota_observation
    quota = (
        None
        if observation is None
        else (observation.scope, observation.windows, observation.valid_until_utc)
    )
    waits = tuple(
        (wait.call_id, wait.reason, wait.attempt_number) for wait in snapshot.call_waits
    )
    return _Transition(
        snapshot.run_id,
        snapshot.phase,
        snapshot.final_status,
        snapshot.counts,
        snapshot.retry_reasons,
        waits,
        quota,
    )


def _detail_changed(previous: _Transition | None, current: _Transition) -> bool:
    """Detect changes that warrant a permanent TTY detail line.

    Returns:
        Whether phase, quota, or wait identity changed since the last write.
    """
    return previous is None or (
        previous.run_id != current.run_id
        or previous.phase != current.phase
        or previous.quota != current.quota
        or previous.waits != current.waits
    )


def _render(snapshot: ProgressSnapshot, is_tty: bool, tty_columns: int) -> str:
    """Produce one short display line, with explicit truncation when needed.

    Returns:
        A complete terminal or redirected message.
    """
    if is_tty and snapshot.phase != "final":
        return _live_line(snapshot, tty_columns)
    c = snapshot.counts
    remaining = (
        c.calls_queued
        + c.calls_stopped_not_started
        + c.calls_active
        + c.calls_retry_wait
        + c.calls_evidence_pending
    )
    calls = (
        f"calls completed={c.calls_succeeded + c.calls_failed + c.calls_cancelled} "
        f"success={c.calls_succeeded} failed={c.calls_failed} "
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
    waits = _waits(snapshot)
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


def _live_line(snapshot: ProgressSnapshot, columns: int) -> str:
    """Render a single ASCII row, reserving the last column against wrapping.

    Returns:
        A carriage-return refresh bounded to the caller-supplied width.
    """
    c = snapshot.counts
    completed = c.calls_succeeded + c.calls_failed + c.calls_cancelled
    remaining = (
        c.calls_queued
        + c.calls_stopped_not_started
        + c.calls_active
        + c.calls_retry_wait
        + c.calls_evidence_pending
    )
    text = (
        f"{_safe(snapshot.run_id)} {snapshot.phase} "
        f"done={completed} fail={c.calls_failed} left={remaining} "
        f"a={c.attempts_active} r={c.retries_started} p={c.probes_active}"
    )
    width = columns - 1
    if len(text) > width:
        text = text[: max(0, width - 1)] + "~"
    return "\r\x1b[2K" + text


def _waits(snapshot: ProgressSnapshot) -> str:
    """Render a bounded number of waits with an omission marker.

    Returns:
        The wait summaries, or none when no calls are waiting.
    """
    text = (
        ",".join(
            f"{_safe(wait.call_id)}:{wait.reason}:attempt={wait.attempt_number}:"
            f"elapsed={wait.elapsed_seconds:.1f}s:"
            f"remaining={_number(wait.remaining_seconds, 's')}"
            for wait in islice(snapshot.call_waits, 8)
        )
        or "none"
    )
    if len(snapshot.call_waits) > 8:
        text += ",... [truncated]"
    return text


def _age_for(snapshot: ProgressSnapshot, window_id: QuotaWindowId) -> float | None:
    """Find the supplied producer age for one window.

    Returns:
        The matching age or None when unavailable.
    """
    return next(
        (
            age
            for identity, age in snapshot.quota_window_ages_seconds
            if identity == window_id
        ),
        None,
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
    windows = (
        ";".join(
            _window(observation, window, _age_for(snapshot, window.window_id))
            for window in islice(observation.windows, 8)
        )
        or "unknown"
    )
    if len(observation.windows) > 8:
        windows += ";... [truncated]"
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
    escaped = ascii(value[:100])[1:-1]
    return (
        escaped if len(value) <= 100 and len(escaped) <= 100 else escaped[:97] + "..."
    )


def _bounded(message: str) -> str:
    """Bound UTF-8 output with a visible truncation marker.

    Returns:
        The original message or a complete UTF-8 prefix with a marker.
    """
    data = message.encode("utf-8")
    limit = 16 * 1024
    if len(data) <= limit:
        return message
    marker = "... [truncated]\n"
    return data[: limit - len(marker)].decode("utf-8", errors="ignore") + marker
