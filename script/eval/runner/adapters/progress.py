# SPDX-License-Identifier: Apache-2.0
"""Nonblocking terminal and silent progress sinks."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import islice
from typing import Literal, Protocol

from script.eval.model import (
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

MAX_DETAILS = 8
MAX_REPORT_CHARS = 12000
MAX_REPORT_BYTES = 16000

type Admission = Literal["accepted", "dropped", "unavailable"]


class ProgressAdmission(Protocol):
    """Offer one bounded message promptly; acceptance is not delivery."""

    def __call__(self, text: str, /, *, important: bool = False) -> Admission:
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
        color: bool = False,
    ) -> None:
        """Retain the composition dependencies for synchronous publication.

        Raises:
            ValueError: The supplied terminal width is less than two columns.
        """
        if tty_columns < 2:
            raise ValueError("tty_columns must be at least 2")
        self.color = color
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
        message = _bounded(message)
        if self.color:
            message = "\x1b[36m" + message.removesuffix("\n") + "\x1b[0m\n"
        try:
            result = self.admit(_bounded(message), important=snapshot.phase == "final")
        except OSError:
            result = "unavailable"
        self._presentation.settle(snapshot, now, result)


class _TerminalPresentation:
    """Track attempts and render bounded updates without retaining a queue."""

    def __init__(self) -> None:
        self.disabled = False
        self.last_attempt: float | None = None
        self.last_transition: _Transition | None = None
        self.last_admitted: _Transition | None = None

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
        return _render(snapshot, is_tty, tty_columns)

    def settle(
        self, snapshot: ProgressSnapshot, now: float, result: Admission, /
    ) -> None:
        """Bound retry cadence after a failed write and disable unavailable output."""
        self.last_attempt = now
        self.last_transition = _transition(snapshot)
        if result == "accepted":
            self.last_admitted = self.last_transition
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
    """Detect changes that warrant an immediate detailed update.

    Returns:
        Whether phase, quota, or wait identity changed since the prior fact.
    """
    return previous is None or (
        previous.run_id != current.run_id
        or previous.phase != current.phase
        or previous.quota != current.quota
        or previous.waits != current.waits
    )


def _render(snapshot: ProgressSnapshot, is_tty: bool, tty_columns: int) -> str:
    """Render distinct evidence-backed metrics as readable complete lines.

    Returns:
        A newline-terminated report.
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
    status = snapshot.final_status or snapshot.phase
    lines = [
        f"Run: {_safe(snapshot.run_id)}",
        f"Status: {status} — This is execution status, not a verdict.",
        "Calls",
        f"  Completed: {completed} — Includes failed and cancelled calls.",
        f"  Succeeded: {c.calls_succeeded} — Processes completed successfully.",
        f"  Failed: {c.calls_failed} — Calls settled unsuccessfully.",
        f"  Cancelled: {c.calls_cancelled} — Calls ended by cancellation.",
        f"  Remaining: {remaining} — Calls not yet settled.",
        "Attempts",
        f"  Started: {c.attempts_started} — Attempt invocations dispatched.",
        f"  Active: {c.attempts_active} — Attempts still in progress.",
        f"  Retries: {c.retries_started} — Additional attempts dispatched.",
        "Quota probes",
        f"  Started: {c.probes_started} — Separate quota checks dispatched.",
    ]
    extra = [
        ("Queued calls", c.calls_queued, "Awaiting dispatch."),
        ("Active calls", c.calls_active, "Calls with work in progress."),
        ("Calls waiting to retry", c.calls_retry_wait, "Calls in retry backoff."),
        ("Calls not started", c.calls_stopped_not_started, "Stopped before dispatch."),
        (
            "Calls with evidence pending",
            c.calls_evidence_pending,
            "Required evidence failed.",
        ),
        ("Successful attempts", c.attempts_succeeded, "Processes completed safely."),
        ("Failed attempts", c.attempts_failed, "Attempts settled unsuccessfully."),
        ("Cancelled attempts", c.attempts_cancelled, "Attempts ended by cancellation."),
        (
            "Attempts with evidence pending",
            c.attempts_evidence_pending,
            "Required evidence failed.",
        ),
        ("Active probes", c.probes_active, "Quota checks still in progress."),
        ("Completed probes", c.probes_completed, "Quota checks settled conclusively."),
        ("Failed probes", c.probes_failed, "Quota checks failed or were inconclusive."),
        ("Cancelled probes", c.probes_cancelled, "Quota checks ended by cancellation."),
        (
            "Probes with evidence pending",
            c.probes_evidence_pending,
            "Required evidence failed.",
        ),
    ]
    lines.extend(
        f"{label}: {value} — {description}"
        for label, value, description in extra
        if value
    )
    for reason, count in snapshot.retry_reasons:
        lines.append(
            f"Retries for {reason}: {count} — Attempts dispatched for this reason."
        )
    lines.extend(_details(snapshot))
    text = "\n".join(lines)
    if len(text) > MAX_REPORT_CHARS:
        text = text[: MAX_REPORT_CHARS - 16] + "... [truncated]"
    return text + "\n"


def _details(snapshot: ProgressSnapshot) -> list[str]:
    """Render bounded retry and quota details.

    Returns:
        Complete lines describing observed details.
    """
    lines: list[str] = []
    for wait in islice(snapshot.call_waits, MAX_DETAILS):
        label = _safe(wait.call_id)
        lines.extend([
            f"Waiting call: {label} — This call is in retry backoff.",
            f"  Reason: {wait.reason} — This caused the retry wait.",
            f"  Attempt: {wait.attempt_number} — This attempt precedes the wait.",
            f"  Elapsed: {wait.elapsed_seconds:.1f}s — Time spent waiting.",
            f"  Remaining: {_number(wait.remaining_seconds, 's')} — Backoff remaining.",
        ])
    if len(snapshot.call_waits) > MAX_DETAILS:
        lines.append("Further retry waits: omitted — The report is bounded.")
    observation = snapshot.quota_observation
    if observation is None:
        lines.append("Quota: unknown — No validated observation is available.")
    else:
        scope = observation.scope
        scope_text = (
            "unknown"
            if scope is None
            else (f"{_safe(scope.provider_id)}/{_safe(scope.allowance_id)}")
        )
        lines.append(f"Quota scope: {scope_text} — Scope of the observation.")
        if not observation.windows:
            lines.append("Quota windows: unknown — No window was observed.")
        for window in islice(observation.windows, MAX_DETAILS):
            age = _age_for(snapshot, window.window_id)
            reset = _safe(window.reset_at_utc) if window.reset_at_utc else "unknown"
            freshness = _freshness(
                window.source_observed_at_utc, age, observation.valid_until_utc
            )
            lines.extend([
                f"Quota window: {_safe(window.window_id)} — Identifies this window.",
                f"  State: {window.state} — Observed availability.",
                f"  Usage: {_number(window.usage_percent, '%')} — Observed usage.",
                f"  Reset hint: {reset} — Availability is not guaranteed.",
                f"  Age: {_number(age, 's')} — Age of the observation.",
                f"  {freshness} — Observation freshness.",
            ])
        if len(observation.windows) > MAX_DETAILS:
            lines.append("Further quota windows: omitted — The report is bounded.")
    return lines


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
    limit = MAX_REPORT_BYTES
    if len(data) <= limit:
        return message
    marker = "... [truncated]\n"
    return data[: limit - len(marker)].decode("utf-8", errors="ignore") + marker
