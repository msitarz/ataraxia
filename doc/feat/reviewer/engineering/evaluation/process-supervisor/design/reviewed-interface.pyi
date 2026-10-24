# SPDX-License-Identifier: Apache-2.0
"""Historical reviewed interface from revision 2d1863fe1d5324.

The active implementation is ``script/process_supervisor.py``. This retained
file records the interface that guided the wiring; it is outside active module
resolution and is not a second interface definition.

This experimental scope has the following accepted limits:

- Cleanup immediately signals the owned POSIX group and waits for the direct
  CLI, without a graceful TERM/grace/KILL period or orderly-flushing guarantee.
- Signal outcome and direct-child wait are observations, not proof that every
  descendant exited; the boundary does not discover process trees, probe group
  absence or zombies, or contain escaped children.
- The Evaluation trusts upstream Codex and OS lifecycle behavior beyond those
  observations.
- The expected workload uses supported controls to disable optional model
  command and tool access to avoid tool-launched work, but this does not
  establish that Codex launches no internal subprocesses; retained tool
  declarations and accepted uncertainty are recorded in the Evaluation
  protocol.
- If this supervisor is itself SIGKILLed or OOM-killed, it cannot clean up or
  recover orphan work.
- Blocking process creation may outlast an async deadline and delay
  cancellation or other tasks.
- Direct termination may interrupt buffered output or local state writes.
- The boundary has no additional guard against PID/PGID reuse.

See the child Work's architecture.md for the current status and evidence.
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
