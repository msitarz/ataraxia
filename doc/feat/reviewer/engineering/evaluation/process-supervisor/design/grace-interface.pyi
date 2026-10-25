# SPDX-License-Identifier: Apache-2.0
"""Accepted AC-4 public delta; not an importable runtime API.

Baseline: script/process_supervisor.py at 9df46f001408fbbebb5735b9477a1b0b190a0274.
See ../architecture.md and ../README.md AC-4 for lifecycle and acceptance rules.
The historical reviewed-interface.pyi stays unchanged. This non-shadowing file
shows only changed shapes, not an independently usable replacement module.
Unchanged public shapes and methods remain defined by the active module; its
runtime cleanup evidence now uses these deltas throughout result paths.
"""

from dataclasses import dataclass
from typing import Literal, Protocol

from script.process_supervisor import AttemptRequest as BaselineAttemptRequest
from script.process_supervisor import ProcessHandle

@dataclass(frozen=True)
class AttemptRequest(BaselineAttemptRequest):
    """Extend the baseline request; construction rejects invalid grace.

    grace_seconds is finite, nonnegative, non-bool, and strictly less than
    cleanup_timeout_seconds. Invalid values raise ValueError before launch.
    Baseline fields, validation and zero-output-limit semantics are unchanged.
    """

    grace_seconds: float = 0.0

@dataclass(frozen=True)
class SignalAttempt:
    """One ordered OS group-signal request, with its original diagnostic.

    no_target records ProcessLookupError; it does not prove group absence.
    Missing outcome is unknown, never implicitly successful.
    """

    signal: Literal["SIGTERM", "SIGKILL"]
    outcome: Literal["sent", "no_target", "failed", "unknown"]
    diagnostic: str | None

@dataclass(frozen=True)
class CleanupEvidence:
    """Replace the baseline single signal fields with ordered observations.

    Owned cleanup requires KILL alone at zero grace, or TERM then KILL at
    positive grace. No-launch uses an empty tuple; acquisition uncertainty and
    missing required observations remain unsafe. Direct-wait fields are unchanged.
    """

    process: Literal["not_started", "owned", "acquisition_uncertain"]
    signals: tuple[SignalAttempt, ...]
    direct_wait: Literal["not_started", "reaped", "failed", "expired", "unknown"]
    wait_diagnostic: str | None

    @property
    def dispatch_permitted(self) -> bool:
        """Accept only exact owned sequences and successful signal/wait evidence.

        Owned identities must be exactly ("SIGKILL",) or ("SIGTERM", "SIGKILL"),
        every outcome sent/no_target without diagnostics, and direct_wait reaped
        without a diagnostic. Missing final KILL, unknown outcomes, duplicates
        and reordered sequences block dispatch.
        Failed TERM blocks dispatch even after successful KILL. The adapter
        selects the expected sequence from validated grace; no request/config
        field is added here. Proven no-launch requires empty signal evidence,
        no direct wait and no diagnostic. Acquisition uncertainty is unsafe;
        cancellation independently stops dispatch in the caller.
        """
        ...

@dataclass(frozen=True)
class CleanupOutcome:
    """Same envelope, carrying the active CleanupEvidence shape."""

    evidence: CleanupEvidence
    exit_status: int | None = None

class ProcessEffects(Protocol):
    """Partial protocol delta: acquire and capture remain as in the baseline."""

    async def cleanup(
        self,
        handle: ProcessHandle,
        timeout_seconds: float,
        grace_seconds: float,
        /,
    ) -> CleanupOutcome:
        """Use one loop.time deadline for grace, pipe handling and direct wait.

        Composition passes both validated request limits unchanged and shields
        this task against repeated owner cancellation. Zero sends KILL only;
        positive sends TERM, drains/discards during grace only when TERM was
        sent, then requests KILL even after leader exit or budget expiry.
        TERM failed/no_target skips grace. Explicit pipe closure follows KILL
        even on signal failure. Direct wait uses only the remaining budget;
        exhausted budget reports expiry. Retained capture is unchanged.
        """
        ...
