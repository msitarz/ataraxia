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

import asyncio
from asyncio import CancelledError
from dataclasses import dataclass, replace
import math
from pathlib import Path
from time import monotonic
from typing import Literal, Never, Protocol


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

    def __post_init__(self) -> None:
        """Reject invalid protocol limits before any acquisition effect.

        Raises:
            ValueError: A timeout or output limit violates the protocol.
        """
        if (
            isinstance(self.timeout_seconds, bool)
            or not isinstance(self.timeout_seconds, (int, float))
            or not math.isfinite(self.timeout_seconds)
            or self.timeout_seconds <= 0
        ):
            raise ValueError("timeout_seconds must be positive and finite")
        if (
            isinstance(self.cleanup_timeout_seconds, bool)
            or not isinstance(self.cleanup_timeout_seconds, (int, float))
            or not math.isfinite(self.cleanup_timeout_seconds)
            or self.cleanup_timeout_seconds <= 0
        ):
            raise ValueError("cleanup_timeout_seconds must be positive and finite")
        if (
            isinstance(self.output_limit_bytes, bool)
            or not isinstance(self.output_limit_bytes, int)
            or self.output_limit_bytes < 0
        ):
            raise ValueError("output_limit_bytes must be a nonnegative integer")


@dataclass(frozen=True)
class CleanupEvidence:
    """Separate group-signal and direct-child wait observations."""

    process: Literal["not_started", "owned", "acquisition_uncertain"]
    signal: Literal["not_started", "sent", "no_target", "failed", "unknown"]
    signal_diagnostic: str | None
    direct_wait: Literal["not_started", "reaped", "failed", "expired", "unknown"]
    wait_diagnostic: str | None

    @property
    def dispatch_permitted(self) -> bool:
        """Whether the observations permit another dispatch.

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
    """Available facts, with absent output distinct from observed empty streams."""

    output: CapturedOutput | None
    elapsed_seconds: float | None
    cleanup: CleanupEvidence


@dataclass(frozen=True)
class Completed:
    """Normal child completion, including nonzero exit status."""

    observation: AttemptObservation
    # asyncio's POSIX convention: nonnegative means exit code; -N means signal N.
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
    """Cancellation plus lifecycle evidence and any post-kill child status."""

    def __init__(
        self, observation: AttemptObservation, exit_status: int | None = None
    ) -> None:
        super().__init__("process-supervisor attempt cancelled")
        self.observation = observation
        self.exit_status = exit_status


@dataclass(frozen=True)
class AttemptFailureEvidence:
    """Structured cleanup evidence on an original escaping programming error.

    The supervisor stores this value in the original exception's instance
    dictionary, preserving its type, message, and traceback.
    """

    observation: AttemptObservation
    exit_status: int | None
    stop_dispatch_diagnostic: str | None = None


def failure_evidence(error: BaseException) -> AttemptFailureEvidence | None:
    """Return structured supervisor evidence attached to an escaping error.

    Returns:
        The attached evidence, or ``None`` when the error escaped before the
        supervisor acquired enough information to create it.
    """
    evidence = vars(error).get("process_supervisor_evidence")
    return evidence if isinstance(evidence, AttemptFailureEvidence) else None


def stop_dispatch_diagnostic(error: BaseException) -> str | None:
    """Return a stop-hook failure diagnostic retained on the original error."""
    evidence = failure_evidence(error)
    if evidence is not None and evidence.stop_dispatch_diagnostic is not None:
        return evidence.stop_dispatch_diagnostic
    diagnostic = vars(error).get("process_supervisor_stop_dispatch_diagnostic")
    return diagnostic if isinstance(diagnostic, str) else None


@dataclass(frozen=True)
class NotLaunched:
    """Acquisition proves no child started and no acquisition operation remains."""

    error_type: str
    diagnostic: str


@dataclass(frozen=True)
class CleanupOutcome:
    """Cleanup facts, including a direct-child status observed after signaling."""

    evidence: CleanupEvidence
    exit_status: int | None = None


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

    Acquisition, capture, or cleanup cancellation propagates as
    ``AttemptCancelled``. Unexpected errors propagate unchanged; acquired
    failures carry evidence, while raw acquisition errors do not.

    Returns:
        The terminal result supplied by the capture effect, with cleanup and
        elapsed evidence attached by this composition.

    Raises:
        RuntimeError: An impossible acquisition settlement violates an invariant.
    """
    process_effects = effects if effects is not None else NativeProcessEffects()
    attempt_clock = clock if clock is not None else SystemClock()
    started_at = attempt_clock.monotonic()
    execution_deadline = started_at + request.timeout_seconds
    acquisition = await _settle_acquisition(process_effects, request)
    if acquisition.cancellation is not None:
        return await _finish_cancelled_acquisition(
            acquisition, process_effects, request, attempt_clock, started_at
        )
    if acquisition.error is not None:
        raise acquisition.error
    if acquisition.acquired is None:
        raise RuntimeError("acquisition settled without a handle or cancellation")
    if isinstance(acquisition.acquired, NotLaunched):
        acquired = acquisition.acquired
        observation = AttemptObservation(
            CapturedOutput(b"", b""),
            attempt_clock.monotonic() - started_at,
            CleanupEvidence("not_started", "not_started", None, "not_started", None),
        )
        return InfrastructureFailure(
            observation, None, acquired.error_type, acquired.diagnostic
        )
    handle = acquisition.acquired
    return await _run_owned_attempt(
        request, process_effects, attempt_clock, started_at, execution_deadline, handle
    )


async def call_supervisor(
    request: AttemptRequest, attempt: AttemptRunner, stop_dispatch: DispatchStop
) -> AttemptResult:
    """Forward one outcome and stop caller dispatch when cleanup is uncertain.

    Cancellation remains cancellation after the stop hook records the active
    evidence. The parent owns planned-call accounting and all broader policy.
    Unexpected exceptions are passed to the stop hook and re-raised unchanged.

    Returns:
        The exact attempt result returned by the runner.

    """
    try:
        outcome = await attempt(request)
    except BaseException as exc:
        # Keep the original exception or cancellation visible.
        _stop_preserving_error(stop_dispatch, exc)
        raise

    if not outcome.observation.cleanup.dispatch_permitted:
        try:
            stop_dispatch(outcome)
        except BaseException as exc:
            vars(exc)["process_supervisor_outcome"] = outcome
            raise
    return outcome


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


@dataclass(frozen=True)
class SystemClock:
    """Production monotonic clock adapter."""

    def monotonic(self) -> float:
        """Return monotonic seconds."""
        return monotonic()


class ProcessEffects(Protocol):
    """Supervisor-owned OS/asyncio effects, isolated at their actual boundary."""

    async def acquire(self, request: AttemptRequest, /) -> ProcessHandle | NotLaunched:
        """Start argv or prove that no child or pending acquisition exists.

        Expected OS launch failures may return ``NotLaunched`` with their
        normalized type and diagnostic. Unexpected errors remain exceptions.
        """
        ...

    async def capture(
        self,
        handle: ProcessHandle,
        request: AttemptRequest,
        execution_deadline: float,
        /,
    ) -> AttemptResult:
        """Return tagged output or cancellation with observed partial buffers.

        The effect owns the stream buffers and translates cancellation into
        ``AttemptCancelled`` with its retained partial prefixes subject to the
        requested output limit. If raw cancellation escapes, composition has
        no byte observations.
        """
        ...

    async def cleanup(
        self, handle: ProcessHandle, timeout_seconds: float, /
    ) -> CleanupOutcome:
        """Signal the group and await the direct child within the timeout.

        The adapter enforces the positive finite timeout and converts expected
        OS failures into evidence. Composition keeps awaiting a retained task;
        it cannot impose a hard bound on a cancellation-resistant adapter.
        """
        ...


@dataclass(frozen=True)
class NativeProcessEffects:
    """Placeholder for the OS adapter; leaf process behavior is still pending."""

    async def acquire(self, request: AttemptRequest, /) -> ProcessHandle | NotLaunched:
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
    ) -> CleanupOutcome:
        """Pending process-group signaling and bounded cleanup."""
        raise NotImplementedError("group signaling and bounded cleanup are pending")


class AttemptRunner(Protocol):
    """Caller-owned port for one supervisor attempt."""

    async def __call__(self, request: AttemptRequest, /) -> AttemptResult:
        """Run one attempt using the supplied request."""
        ...


class DispatchStop(Protocol):
    """Parent-owned hook that records the active outcome and stops new work.

    Implementations should not raise; hook failures on exception paths are
    retained as diagnostics while the original exception propagates, and hook
    failures on unsafe-result paths propagate directly.
    """

    def __call__(self, reason: AttemptResult | BaseException, /) -> None:
        """Record the stop reason and prevent later dispatch."""
        ...


@dataclass(frozen=True)
class _AcquisitionSettlement:
    acquired: ProcessHandle | NotLaunched | None
    cancellation: CancelledError | None
    error: Exception | None


@dataclass(frozen=True)
class _CleanupSettlement:
    outcome: CleanupOutcome
    cancellation: CancelledError | None
    error: Exception | None
    adapter_cancelled: bool = False


async def _settle_acquisition(
    effects: ProcessEffects, request: AttemptRequest
) -> _AcquisitionSettlement:
    """Wait for acquisition to settle even when the owner task is cancelled.

    Returns:
        The acquired handle or proven no-launch outcome, any cancellation, and
        an acquisition error that completed after cancellation.
    """
    acquisition = asyncio.create_task(effects.acquire(request))
    cancellation: CancelledError | None = None
    while True:
        try:
            acquired = await asyncio.shield(acquisition)
            return _AcquisitionSettlement(acquired, cancellation, None)
        except CancelledError as exc:
            if acquisition.cancelled():
                return _AcquisitionSettlement(None, cancellation or exc, None)
            cancellation = cancellation or exc
        except Exception as exc:
            return _AcquisitionSettlement(None, cancellation, exc)


async def _finish_cancelled_acquisition(
    acquisition: _AcquisitionSettlement,
    effects: ProcessEffects,
    request: AttemptRequest,
    clock: Clock,
    started_at: float,
) -> Never:
    """Propagate acquisition cancellation after ownership and evidence settle.

    Raises:
        AttemptCancelled: Acquisition settled after owner cancellation.
    """
    cancellation = acquisition.cancellation
    if isinstance(acquisition.acquired, NotLaunched):
        observation = AttemptObservation(
            CapturedOutput(b"", b""),
            clock.monotonic() - started_at,
            CleanupEvidence("not_started", "not_started", None, "not_started", None),
        )
        stopped = AttemptCancelled(observation)
        stopped.add_note(
            f"Acquisition safely failed: {acquisition.acquired.error_type}: "
            f"{acquisition.acquired.diagnostic}"
        )
        stopped.add_note(
            f"Acquisition was cancelled: {_error_diagnostic(cancellation)}"
        )
        raise stopped from (acquisition.error or cancellation)
    if acquisition.acquired is None:
        diagnostic = _error_diagnostic(acquisition.error) if acquisition.error else None
        observation = AttemptObservation(
            None,
            clock.monotonic() - started_at,
            CleanupEvidence(
                "acquisition_uncertain", "unknown", diagnostic, "unknown", diagnostic
            ),
        )
        if acquisition.error is not None:
            stopped = AttemptCancelled(observation)
            stopped.add_note(f"Acquisition also failed: {diagnostic}")
            stopped.add_note(
                f"Acquisition was cancelled: {_error_diagnostic(cancellation)}"
            )
            raise stopped from acquisition.error
        raise AttemptCancelled(observation) from cancellation
    cleanup = await _settle_cleanup(
        effects, acquisition.acquired, request.cleanup_timeout_seconds
    )
    observation = _observation(None, cleanup.outcome.evidence, clock, started_at)
    stopped = AttemptCancelled(observation, cleanup.outcome.exit_status)
    _explain_cleanup_settlement(stopped, cleanup)
    stopped.add_note(f"Acquisition was cancelled: {_error_diagnostic(cancellation)}")
    raise stopped from (cleanup.error or cancellation)


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

    """
    try:
        result = await effects.capture(handle, request, execution_deadline)
    except CancelledError as exc:
        cancellation = exc
        result = None
        error = None
    except (Exception, KeyboardInterrupt, SystemExit) as exc:
        cancellation = None
        result = None
        error = exc
    else:
        cancellation = None
        error = None
    return await _finalize_owned_attempt(
        result, error, cancellation, effects, handle, request, clock, started_at
    )


async def _settle_cleanup(
    effects: ProcessEffects, handle: ProcessHandle, timeout_seconds: float
) -> _CleanupSettlement:
    """Retain cleanup through repeated cancellation until its adapter settles.

    Returns:
        Final cleanup outcome, any waiting cancellation, and an unexpected
        cleanup error. Unexpected errors retain their type and message in the
        unknown cleanup evidence.
    """
    cleanup_task = asyncio.create_task(effects.cleanup(handle, timeout_seconds))
    cancellation: CancelledError | None = None
    while True:
        try:
            outcome = await asyncio.shield(cleanup_task)
            return _CleanupSettlement(outcome, cancellation, None)
        except CancelledError as exc:
            cancellation = cancellation or exc
            if cleanup_task.cancelled():
                diagnostic = _error_diagnostic(exc)
                outcome = CleanupOutcome(
                    CleanupEvidence(
                        "owned", "unknown", diagnostic, "unknown", diagnostic
                    )
                )
                return _CleanupSettlement(outcome, cancellation, None, True)
        except Exception as exc:
            diagnostic = _error_diagnostic(exc)
            outcome = CleanupOutcome(
                CleanupEvidence("owned", "unknown", diagnostic, "unknown", diagnostic)
            )
            return _CleanupSettlement(outcome, cancellation, exc)


async def _finalize_owned_attempt(
    result: AttemptResult | None,
    error: BaseException | None,
    cancellation: CancelledError | None,
    effects: ProcessEffects,
    handle: ProcessHandle,
    request: AttemptRequest,
    clock: Clock,
    started_at: float,
) -> AttemptResult:
    """Apply cleanup once, then resolve cancellation, errors, and results.

    Returns:
        The terminal result after cleanup evidence is attached.
    """
    cleanup = await _settle_cleanup(effects, handle, request.cleanup_timeout_seconds)
    leaf_cancellation = (
        cancellation if isinstance(cancellation, AttemptCancelled) else None
    )
    output = (
        result.observation.output
        if result is not None
        else leaf_cancellation.observation.output
        if leaf_cancellation is not None
        else None
    )
    observation = _observation(output, cleanup.outcome.evidence, clock, started_at)
    status = (
        result.exit_status
        if result is not None and result.exit_status is not None
        else cleanup.outcome.exit_status
    )
    return _apply_finalization_policy(
        result, error, cancellation, leaf_cancellation, cleanup, observation, status
    )


def _apply_finalization_policy(
    result: AttemptResult | None,
    error: BaseException | None,
    cancellation: CancelledError | None,
    leaf_cancellation: AttemptCancelled | None,
    cleanup: _CleanupSettlement,
    observation: AttemptObservation,
    status: int | None,
) -> AttemptResult:
    """Apply cancellation, error, and result precedence after cleanup.

    Returns:
        The terminal result when neither cancellation nor an error takes
        precedence.
    """
    if cleanup.cancellation is not None or cancellation is not None:
        _raise_cancelled_finalization(
            error, cancellation, leaf_cancellation, cleanup, observation, status
        )
    if error is not None:
        _attach_failure_evidence(error, observation, status)
        raise error
    if cleanup.error is not None:
        _attach_failure_evidence(cleanup.error, observation, status)
        raise cleanup.error
    assert result is not None, "attempt finalization must have a terminal value"
    if isinstance(result, Completed):
        return replace(result, observation=observation)
    return replace(result, observation=observation, exit_status=status)


def _raise_cancelled_finalization(
    error: BaseException | None,
    cancellation: CancelledError | None,
    leaf_cancellation: AttemptCancelled | None,
    cleanup: _CleanupSettlement,
    observation: AttemptObservation,
    status: int | None,
) -> Never:
    """Raise cancellation while retaining the best available evidence."""
    cause = (
        None
        if leaf_cancellation is not None
        else cancellation or error or cleanup.error or cleanup.cancellation
    )
    stopped = leaf_cancellation or AttemptCancelled(observation, status)
    stopped.observation = observation
    if stopped.exit_status is None:
        stopped.exit_status = status
    _explain_cleanup_settlement(stopped, cleanup)
    if error is not None:
        stopped.add_note(f"Capture also failed: {_error_diagnostic(error)}")
    if leaf_cancellation is not None:
        raise stopped
    if cause is not None:
        raise stopped from cause
    raise stopped


def _error_diagnostic(error: BaseException | None) -> str:
    """Format an exception with its type and message for retained evidence.

    Returns:
        The type-qualified diagnostic, or a placeholder for absent errors.
    """
    if error is None:
        return "unknown error"
    return f"{type(error).__name__}: {error}"


def _explain_cleanup_settlement(
    error: BaseException, settlement: _CleanupSettlement
) -> None:
    """Retain unexpected cleanup errors and cancellations as exception notes."""
    if settlement.error is not None:
        error.add_note(
            f"Cleanup raised unexpectedly: {_error_diagnostic(settlement.error)}"
        )
    if settlement.cancellation is not None:
        if settlement.adapter_cancelled:
            error.add_note("The cleanup adapter cancelled itself.")
            return
        error.add_note(
            f"Cleanup wait received cancellation: "
            f"{_error_diagnostic(settlement.cancellation)}"
        )


def _attach_failure_evidence(
    error: BaseException, observation: AttemptObservation, exit_status: int | None
) -> None:
    """Attach structured evidence without replacing the original exception."""
    vars(error)["process_supervisor_evidence"] = AttemptFailureEvidence(
        observation, exit_status
    )


def _stop_preserving_error(stop_dispatch: DispatchStop, error: BaseException) -> None:
    """Call the stop hook while retaining the attempt's control-flow object."""
    try:
        stop_dispatch(error)
    except BaseException as hook_error:
        diagnostic = _error_diagnostic(hook_error)
        evidence = failure_evidence(error)
        if evidence is not None:
            vars(error)["process_supervisor_evidence"] = replace(
                evidence, stop_dispatch_diagnostic=diagnostic
            )
        else:
            vars(error)["process_supervisor_stop_dispatch_diagnostic"] = diagnostic


def _observation(
    output: CapturedOutput | None,
    cleanup: CleanupEvidence,
    clock: Clock,
    started_at: float,
) -> AttemptObservation:
    """Build attempt evidence after cleanup and its final clock observation.

    Returns:
        The output, elapsed time through cleanup, and cleanup evidence.
    """
    return AttemptObservation(output, clock.monotonic() - started_at, cleanup)
