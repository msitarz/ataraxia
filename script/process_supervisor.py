# SPDX-License-Identifier: Apache-2.0
"""Typed composition for one experimental CLI attempt.

Accepted limitations for this experiment:

- Cleanup immediately signals the owned POSIX group and waits for the direct
  CLI, without a graceful TERM/grace/KILL period or orderly-flushing guarantee.
- Signal outcome and direct-child wait are observations, not proof that every
  descendant exited; the boundary does not discover process trees, probe group
  absence or zombies, or contain escaped children.
- The Evaluation trusts upstream Codex and OS lifecycle behavior beyond those
  observations.
- Supported controls disable optional model command and tool access to avoid
  tool-launched work, but do not establish that Codex launches no internal
  subprocesses; retained declarations and uncertainty remain in the protocol.
- If this supervisor is itself SIGKILLed or OOM-killed, it cannot clean up or
  recover orphan work.
- Blocking process creation may outlast an async deadline and delay
  cancellation or other tasks.
- Direct termination may interrupt buffered output or local state writes.
- The boundary has no additional guard against PID/PGID reuse.

Native acquisition, capture, and cleanup operations remain pending.
"""

from asyncio import CancelledError
from dataclasses import dataclass, replace
from pathlib import Path
from time import monotonic
from typing import Literal, Protocol


@dataclass(frozen=True)
class AttemptRequest:
    """One command attempt with caller-resolved argv and protocol limits.

    The caller supplies the recorded absolute CLI path as ``argv[0]``.
    Execution and cleanup timeouts must be positive and finite.
    ``output_limit_bytes`` must be nonnegative: zero disables the byte cap while
    retaining captured output, and a positive value caps combined stdout and
    stderr bytes. Deadlines still apply when capture is uncapped.
    """

    argv: tuple[str, ...]
    cwd: Path
    timeout_seconds: float
    cleanup_timeout_seconds: float
    output_limit_bytes: int
    stdin: Literal["devnull"]


@dataclass(frozen=True)
class CleanupEvidence:
    """Separate group-signal and direct-child wait observations."""

    process: Literal["not_started", "owned", "acquisition_uncertain"]
    signal: Literal["not_started", "sent", "no_target", "failed", "unknown"]
    signal_diagnostic: str | None
    direct_wait: Literal["not_started", "reaped", "failed", "expired", "unknown"]
    wait_diagnostic: str | None

    @property
    def confirmed(self) -> bool:
        """Whether signal and direct-child wait evidence permits dispatch.

        This does not establish whole-group or descendant absence.
        """
        if self.process == "not_started":
            return (
                self.signal == "not_started"
                and self.direct_wait == "not_started"
                and self.signal_diagnostic is None
                and self.wait_diagnostic is None
            )
        return (
            self.process == "owned"
            and self.signal in {"sent", "no_target"}
            and self.direct_wait == "reaped"
        )


@dataclass(frozen=True)
class CapturedOutput:
    """Observed stdout and stderr prefixes, retained separately."""

    stdout: bytes
    stderr: bytes


@dataclass(frozen=True)
class AttemptObservation:
    """Facts available when an attempt reaches a terminal outcome."""

    output: CapturedOutput
    elapsed_seconds: float | None
    cleanup: CleanupEvidence


@dataclass(frozen=True)
class Completed:
    """Normal child completion, including nonzero exit status."""

    observation: AttemptObservation
    exit_status: int


@dataclass(frozen=True)
class IncompleteAttempt:
    """An attempt without normal completion, retaining any observed status."""

    observation: AttemptObservation
    exit_status: int | None


@dataclass(frozen=True)
class TimedOut(IncompleteAttempt):
    """The active attempt exceeded its execution deadline."""


@dataclass(frozen=True)
class OutputLimitExceeded(IncompleteAttempt):
    """Combined output exceeded the positive byte allowance."""


@dataclass(frozen=True)
class InfrastructureFailure(IncompleteAttempt):
    """A non-cancellation infrastructure failure."""

    error_type: str
    diagnostic: str


type AttemptResult = Completed | TimedOut | OutputLimitExceeded | InfrastructureFailure


class AttemptCancelled(CancelledError):
    """Cancellation propagated with the best available lifecycle evidence."""

    def __init__(self, observation: AttemptObservation) -> None:
        super().__init__("process-supervisor attempt cancelled")
        self.observation = observation


class ProcessHandle(Protocol):
    """Owned direct child and the POSIX process group assigned to it."""

    @property
    def pid(self) -> int:
        """The directly acquired CLI process identifier."""
        ...

    @property
    def process_group_id(self) -> int:
        """The POSIX group identifier owned by this invocation."""
        ...


class Clock(Protocol):
    """Monotonic clock used to bound and observe the complete attempt."""

    def monotonic(self) -> float:
        """Return monotonic seconds."""
        ...


class ProcessEffects(Protocol):
    """Supervisor-owned OS/asyncio effects, isolated at their actual boundary."""

    async def acquire(self, request: AttemptRequest, /) -> ProcessHandle:
        """Start argv exactly as recorded and return ownership of the child."""
        ...

    async def capture(
        self,
        handle: ProcessHandle,
        request: AttemptRequest,
        execution_deadline: float,
        /,
    ) -> AttemptResult:
        """Return the leaf's tagged terminal observation under the deadline."""
        ...

    async def cleanup(
        self, handle: ProcessHandle, timeout_seconds: float, /
    ) -> CleanupEvidence:
        """Signal the owned group and await the direct child within the deadline."""
        ...


@dataclass(frozen=True)
class NativeProcessEffects:
    """Placeholder for the OS adapter; leaf process behavior is still pending."""

    async def acquire(self, request: AttemptRequest, /) -> ProcessHandle:
        """Pending native child acquisition."""
        raise NotImplementedError("process acquisition is pending")

    async def capture(
        self,
        handle: ProcessHandle,
        request: AttemptRequest,
        execution_deadline: float,
        /,
    ) -> AttemptResult:
        """Pending stream capture and direct-child wait."""
        raise NotImplementedError("stream capture and direct-child wait are pending")

    async def cleanup(
        self, handle: ProcessHandle, timeout_seconds: float, /
    ) -> CleanupEvidence:
        """Pending process-group signaling and bounded cleanup."""
        raise NotImplementedError("group signaling and bounded cleanup are pending")


async def run_attempt(
    request: AttemptRequest,
    effects: ProcessEffects | None = None,
    clock: Clock | None = None,
) -> AttemptResult:
    """Compose one attempt's acquisition, observation, and cleanup effects.

    Timing starts before acquisition and ends after cleanup evidence returns.
    The default adapter explicitly leaves native process behavior pending.
    This wiring does not establish timeout enforcement, capture, cleanup, or OS
    guarantees.

    Returns:
        The terminal result supplied by the capture effect, with cleanup and
        elapsed evidence attached by this composition.

    Raises:
        AttemptCancelled: Acquisition was cancelled before ownership was known.
    """
    process_effects = effects if effects is not None else NativeProcessEffects()
    attempt_clock = clock if clock is not None else SystemClock()
    started_at = attempt_clock.monotonic()
    execution_deadline = started_at + request.timeout_seconds
    try:
        handle = await process_effects.acquire(request)
    except CancelledError as exc:
        finished_at = attempt_clock.monotonic()
        observation = AttemptObservation(
            CapturedOutput(b"", b""),
            finished_at - started_at,
            CleanupEvidence("acquisition_uncertain", "unknown", None, "unknown", None),
        )
        raise AttemptCancelled(observation) from exc
    return await _run_owned_attempt(
        request, process_effects, attempt_clock, started_at, execution_deadline, handle
    )


async def _run_owned_attempt(
    request: AttemptRequest,
    effects: ProcessEffects,
    clock: Clock,
    started_at: float,
    execution_deadline: float,
    handle: ProcessHandle,
) -> AttemptResult:
    """Forward a leaf outcome and ensure acquired-process cleanup is attempted.

    Returns:
        The leaf's result variant and fields with final cleanup and elapsed
        evidence attached.

    Raises:
        AttemptCancelled: The leaf supplied cancellation evidence.
        CancelledError: Capture or cleanup was cancelled after acquisition.
    """
    try:
        result = await effects.capture(handle, request, execution_deadline)
    except AttemptCancelled as exc:
        cleanup = await effects.cleanup(handle, request.cleanup_timeout_seconds)
        exc.observation = _observation(
            exc.observation.output, cleanup, clock, started_at
        )
        raise
    except CancelledError:
        await effects.cleanup(handle, request.cleanup_timeout_seconds)
        raise
    except Exception:
        await effects.cleanup(handle, request.cleanup_timeout_seconds)
        raise
    else:
        cleanup = await effects.cleanup(handle, request.cleanup_timeout_seconds)
        observation = _observation(
            result.observation.output, cleanup, clock, started_at
        )
        return replace(result, observation=observation)


def _observation(
    output: CapturedOutput,
    cleanup: CleanupEvidence,
    clock: Clock,
    started_at: float,
) -> AttemptObservation:
    """Build attempt evidence after cleanup and its final clock observation.

    Returns:
        The output, elapsed time through cleanup, and cleanup evidence.
    """
    return AttemptObservation(output, clock.monotonic() - started_at, cleanup)


@dataclass(frozen=True)
class SystemClock:
    """Production monotonic clock adapter."""

    def monotonic(self) -> float:
        """Return monotonic seconds."""
        return monotonic()


class AttemptRunner(Protocol):
    """Caller-owned port for one supervisor attempt."""

    async def __call__(self, request: AttemptRequest, /) -> AttemptResult:
        """Run one attempt using the supplied request."""
        ...


class DispatchStop(Protocol):
    """Parent-owned hook that records the active outcome and stops new work."""

    def __call__(self, reason: AttemptResult | CancelledError, /) -> None:
        """Record the stop reason and prevent later dispatch."""
        ...


async def call_supervisor(
    request: AttemptRequest, attempt: AttemptRunner, stop_dispatch: DispatchStop
) -> AttemptResult:
    """Forward one outcome and stop caller dispatch when cleanup is uncertain.

    Cancellation remains cancellation after the stop hook records the active
    evidence. The parent owns planned-call accounting and all broader policy.

    Returns:
        The exact attempt result returned by the runner.

    Raises:
        CancelledError: The runner was cancelled; the same cancellation is
            re-raised after the parent stop hook observes it.
    """
    try:
        outcome = await attempt(request)
    except CancelledError as exc:
        stop_dispatch(exc)
        raise

    if not outcome.observation.cleanup.confirmed:
        stop_dispatch(outcome)
    return outcome
