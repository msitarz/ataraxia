# SPDX-License-Identifier: Apache-2.0
"""Typed wiring for source-backed Codex quota observations.

The passive source lookup and observation normalization remain injectable
leaves because their file correlation and telemetry schema are unverified.
The active poll recipe and assessment remain injectable because their CLI and
quota semantics are unverified.
"""

from asyncio import CancelledError
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from script.eval.model import (
    AttemptEvidence,
    QuotaObservation,
    QuotaProbeEvidence,
    QuotaProbeRequest,
    QuotaScope,
    QuotaState,
)
from script.eval.runner.ports import (
    AttemptCall,
    QuotaStatusReader,
    Runtime,
)
from script.eval.runner.quota_evidence import attach_quota_probe_evidence
from script.process_supervisor import (
    AttemptCancelled,
    AttemptFailureEvidence,
    AttemptRequest,
    AttemptResult,
    Completed,
    DispatchStop,
    InfrastructureFailure,
    OutputLimitExceeded,
    TimedOut,
    failure_evidence,
)


class RawCodexQuotaStatusSource(Protocol):
    """Read one opaque local session selected by its invocation thread ID."""

    async def read_session_for_thread(
        self, thread_id: str, /
    ) -> RawCodexSessionSnapshot | None:
        """Return only the source snapshot associated with this thread ID."""
        ...


@dataclass(frozen=True)
class RawCodexSessionSnapshot:
    """Untrusted session bytes and an opaque sanitized source coordinate."""

    content: bytes
    source_coordinate: str


@dataclass(frozen=True)
class CodexQuotaSettings:
    """Probe CLI identity and finite supervisor limits.

    The CLI recipe itself remains unverified and belongs to a pending leaf.
    """

    executable_path: Path
    empty_read_only_cwd: Path
    timeout_seconds: float
    cleanup_timeout_seconds: float
    output_limit_bytes: int
    grace_seconds: float


type ExtractThreadId = Callable[[bytes | None], str | None]
type NormalizeSession = Callable[
    [RawCodexSessionSnapshot | None, QuotaScope | None, str], QuotaObservation
]
type BuildProbeRequest = Callable[
    [QuotaProbeRequest, CodexQuotaSettings], AttemptRequest
]
type AssessProbe = Callable[
    [AttemptEvidence, QuotaObservation | None], tuple[QuotaState, str | None]
]


@dataclass(frozen=True, kw_only=True)
class CodexQuotaStatusReader(QuotaStatusReader):
    """Read passive telemetry and expose separate, supervised quota polls.

    Responsibilities:

    - correlate settled invocation telemetry to its private source lookup;
    - normalize source data to provider-neutral scoped observations;
    - run a separate probe through the injected supervisor call;
    - associate process facts and quota assessment with probe evidence.

    Thread IDs remain private to this adapter. Source lookup, thread extraction,
    normalization, the probe recipe, and quota assessment remain explicit
    unimplemented leaves; no quota availability or source schema is inferred.
    """

    source: RawCodexQuotaStatusSource
    quota_scope: QuotaScope | None
    settings: CodexQuotaSettings
    attempt_call: AttemptCall
    runtime: Runtime
    extract_thread_id: ExtractThreadId | None = None
    normalize_session: NormalizeSession | None = None
    build_probe_request: BuildProbeRequest | None = None
    assess_probe: AssessProbe | None = None

    @property
    def expected_scope(self) -> QuotaScope | None:
        """The verified scope paired with this reader, when known."""
        return self.quota_scope

    async def observe_settled_attempt(
        self, evidence: AttemptEvidence, /
    ) -> QuotaObservation:
        """Look up this attempt's source session and normalize it once.

        Returns:
            The injected provider-neutral observation.
        """
        return await self._observe_telemetry(evidence)

    async def poll(
        self, request: QuotaProbeRequest, stop_dispatch: DispatchStop, /
    ) -> QuotaProbeEvidence:
        """Run a separate supervised poll and retain facts on raised errors.

        If cancellation or another exception escapes after dispatch, attach its
        available process and quota facts to that same exception. Callers use
        the original request object with ``quota_probe_evidence``. A missing
        match is incomplete evidence and cannot establish availability.

        Returns:
            The process evidence paired with its normalized quota observation.
        """
        build_request = self.build_probe_request or _build_probe_attempt_request
        assess_probe = self.assess_probe or _assess_probe
        attempt_request = build_request(request, self.settings)
        started_at_utc = self.runtime.utc_now()
        outcome: AttemptResult | None = None
        attempt: AttemptEvidence | None = None
        ended_at_utc: str | None = None
        observation: QuotaObservation | None = None
        try:
            outcome = await self.attempt_call(attempt_request, stop_dispatch)
            ended_at_utc = self.runtime.utc_now()
            attempt = _attempt_evidence(
                attempt_request, outcome, started_at_utc, ended_at_utc
            )
            observation = await self._observe_telemetry(attempt)
            quota_state, classification_basis = assess_probe(attempt, observation)
            return QuotaProbeEvidence(
                request=request,
                process=attempt,
                quota_state=quota_state,
                observation=observation,
                classification_basis=classification_basis,
            )
        except BaseException as error:
            if ended_at_utc is None:
                ended_at_utc = _read_end_time(self.runtime)
            if attempt is None:
                attempt = _attempt_evidence_for_error(
                    attempt_request,
                    outcome,
                    error,
                    started_at_utc,
                    ended_at_utc,
                )
            attach_quota_probe_evidence(
                error,
                QuotaProbeEvidence(
                    request=request,
                    process=attempt,
                    quota_state="unknown",
                    observation=observation,
                    classification_basis="probe assessment did not complete",
                ),
            )
            raise

    async def _observe_telemetry(self, attempt: AttemptEvidence, /) -> QuotaObservation:
        """Correlate captured thread telemetry and normalize its source.

        Returns:
            The injected source-backed observation.
        """
        extract_thread_id = self.extract_thread_id or _extract_thread_id
        normalize_session = self.normalize_session or _normalize_session
        thread_id = extract_thread_id(attempt.usage_telemetry)
        snapshot = (
            await self.source.read_session_for_thread(thread_id)
            if thread_id is not None
            else None
        )
        return normalize_session(snapshot, self.expected_scope, self.runtime.utc_now())


def _attempt_evidence(
    request: AttemptRequest,
    outcome: AttemptResult,
    started_at_utc: str,
    ended_at_utc: str,
    /,
) -> AttemptEvidence:
    """Retain a returned result and its captured stdout bytes.

    Returns:
        Process evidence for the exact request and returned result.
    """
    output = outcome.observation.output
    return AttemptEvidence(
        control_flow="returned",
        outcome=outcome,
        error_type=None,
        diagnostic=None,
        request=request,
        started_at_utc=started_at_utc,
        ended_at_utc=ended_at_utc,
        usage_telemetry=None if output is None else output.stdout,
    )


def _attempt_evidence_for_error(
    request: AttemptRequest,
    outcome: AttemptResult | None,
    error: BaseException,
    started_at_utc: str,
    ended_at_utc: str | None,
    /,
) -> AttemptEvidence:
    """Preserve supervisor facts while describing the original raised flow.

    Returns:
        Available process evidence associated with the original error.
    """
    settled_outcome: AttemptResult | AttemptCancelled | AttemptFailureEvidence | None
    if outcome is not None:
        settled_outcome = outcome
    elif isinstance(error, AttemptCancelled):
        settled_outcome = error
    else:
        attached_result = vars(error).get("process_supervisor_outcome")
        settled_outcome = (
            attached_result
            if isinstance(
                attached_result,
                (Completed, TimedOut, OutputLimitExceeded, InfrastructureFailure),
            )
            else failure_evidence(error)
        )
    observation = None if settled_outcome is None else settled_outcome.observation
    usage_telemetry = (
        None
        if observation is None or observation.output is None
        else observation.output.stdout
    )
    return AttemptEvidence(
        control_flow=(
            "returned"
            if outcome is not None
            else "cancelled"
            if isinstance(error, CancelledError)
            else "raised"
        ),
        outcome=settled_outcome,
        error_type=None if outcome is not None else type(error).__name__,
        diagnostic=None if outcome is not None else _error_diagnostic(error),
        request=request,
        started_at_utc=started_at_utc,
        ended_at_utc=ended_at_utc,
        usage_telemetry=usage_telemetry,
    )


def _read_end_time(runtime: Runtime, /) -> str | None:
    """Read an end time without replacing the primary exception.

    Returns:
        The observed timestamp or ``None`` if the clock fails.
    """
    try:
        return runtime.utc_now()
    except Exception:
        return None


def _error_diagnostic(error: BaseException, /) -> str:
    """Format an error without letting a broken ``__str__`` mask it.

    Returns:
        The exception's display text or a safe fallback.
    """
    try:
        return str(error)
    except Exception:
        return "exception diagnostic unavailable"


def _extract_thread_id(usage_telemetry: bytes | None, /) -> str | None:
    """Extract an invocation thread identifier from unverified telemetry."""
    del usage_telemetry
    raise NotImplementedError("Codex thread telemetry extraction is unverified")


def _normalize_session(
    snapshot: RawCodexSessionSnapshot | None,
    scope: QuotaScope | None,
    read_at_utc: str,
    /,
) -> QuotaObservation:
    """Normalize unverified session data without asserting quota state."""
    del snapshot, scope, read_at_utc
    raise NotImplementedError("Codex session schema and scope are unverified")


def _build_probe_attempt_request(
    request: QuotaProbeRequest,
    settings: CodexQuotaSettings,
    /,
) -> AttemptRequest:
    """Build the exact supervised request after the Codex recipe is reviewed."""
    del request, settings
    raise NotImplementedError("Codex probe CLI recipe is unverified")


def _assess_probe(
    attempt: AttemptEvidence,
    observation: QuotaObservation | None,
    /,
) -> tuple[QuotaState, str | None]:
    """Assess provider-specific availability only after source verification."""
    del attempt, observation
    raise NotImplementedError(
        "Codex scope, window completeness, and freshness are unverified"
    )
