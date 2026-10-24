# SPDX-License-Identifier: Apache-2.0
"""Reviewed typed boundary for one experimental CLI attempt.

This stub intentionally has no matching implementation module. See the child
Work's architecture.md. Remove this active stub when introducing the reviewed
implementation module.
"""

from asyncio import CancelledError
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

@dataclass(frozen=True)
class AttemptRequest:
    """One reviewed command attempt with bounded deadlines and inherited env.

    Execution and cleanup deadlines must be positive and finite.
    ``output_limit_bytes`` must be nonnegative: zero disables the byte cap while
    retaining captured output, and a positive value caps combined stdout and
    stderr bytes. Deadlines and cleanup still apply when capture is uncapped.
    """

    argv: tuple[str, ...]
    cwd: Path
    timeout_seconds: float
    cleanup_timeout_seconds: float
    # Zero is uncapped capture; positive values cap both streams.
    output_limit_bytes: int
    stdin: Literal["devnull"]

@dataclass(frozen=True)
class CleanupEvidence:
    """Separate OS group-signal and direct-child wait observations."""

    process: Literal["not_started", "owned", "acquisition_uncertain"]
    signal: Literal["not_started", "sent", "no_target", "failed", "unknown"]
    signal_diagnostic: str | None
    direct_wait: Literal["not_started", "reaped", "failed", "expired", "unknown"]
    wait_diagnostic: str | None

@dataclass(frozen=True)
class CapturedOutput:
    """Observed stdout and stderr retained separately under an optional cap."""

    stdout: bytes
    stderr: bytes

@dataclass(frozen=True)
class AttemptObservation:
    """Facts observed even when an attempt did not complete normally."""

    output: CapturedOutput
    elapsed_seconds: float | None
    cleanup: CleanupEvidence

@dataclass(frozen=True)
class Completed:
    """The CLI completed; its required exit status may be nonzero."""

    observation: AttemptObservation
    exit_status: int

@dataclass(frozen=True)
class IncompleteAttempt:
    """An attempt without normal completion, with any observed exit status."""

    observation: AttemptObservation
    exit_status: int | None

@dataclass(frozen=True)
class TimedOut(IncompleteAttempt):
    """The active attempt exceeded its deadline."""

@dataclass(frozen=True)
class OutputLimitExceeded(IncompleteAttempt):
    """Combined output exceeded the request's positive byte cap."""

@dataclass(frozen=True)
class InfrastructureFailure(IncompleteAttempt):
    """A non-cancellation failure during launch, I/O, or waiting."""

    error_type: str
    diagnostic: str

type AttemptResult = Completed | TimedOut | OutputLimitExceeded | InfrastructureFailure

class AttemptCancelled(CancelledError):
    """Cancellation propagated with best available lifecycle evidence."""

    def __init__(self, observation: AttemptObservation) -> None: ...

    observation: AttemptObservation

async def run_attempt(request: AttemptRequest) -> AttemptResult:
    """Run one attempt and clean up its owned process resources.

    CLI resolution/version discovery and retry policy belong to the caller.
    Cancellation propagates as ``AttemptCancelled`` after bounded cleanup.
    """
    ...
