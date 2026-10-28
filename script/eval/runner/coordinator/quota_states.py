# SPDX-License-Identifier: Apache-2.0
"""Pure quota recovery decisions over durable and sampled facts."""

from asyncio import CancelledError
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Literal

from script.eval.model import (
    AttemptNumber,
    HarnessConfig,
    QuotaObservation,
    QuotaProbeEvidence,
    QuotaProbeRecord,
    QuotaProbeRequest,
    QuotaProbeSchedule,
    QuotaScope,
    QuotaWaitContext,
    WaitEnd,
    WaitId,
    WaitRecord,
)
from script.eval.runner.policy import quota_probe_allowed, safe_process_cleanup
from script.eval.runner.ports import EffectiveCall

from .state import StopReason, WaitWrite


@dataclass(frozen=True)
class PauseOrigin:
    """The first exhaustion closes dispatch before fallible persistence."""

    call: EffectiveCall
    attempt_number: AttemptNumber


@dataclass(frozen=True)
class PauseTrigger:
    """The latched origin and its validated, durably recorded observation."""

    origin: PauseOrigin
    observation: QuotaObservation


@dataclass(frozen=True)
class Open:
    """The quota gate is open."""


@dataclass(frozen=True)
class Draining:
    """A recognized exhaustion closes dispatch while attempts settle."""

    context: QuotaWaitContext

    def probe_eligible(
        self, expected_scope: QuotaScope | None, now_utc: str, /
    ) -> bool:
        """Check the drained trigger before any paid probe preparation.

        Returns:
            Whether the normalized trigger is fresh, scoped, and exhausted.
        """
        return probe_eligible(self.context.quota_observation, expected_scope, now_utc)

    def started(
        self,
        waiting: Waiting,
        cancellation: CancelledError | None,
        stop: StopReason | None,
        closure: WaitRecord | None,
        /,
    ) -> Waiting:
        """Retain a durable start and any closure required by cancellation.

        Returns:
            The next state built from the supplied facts.

        Raises:
            ValueError: The supplied facts do not belong to the same lifecycle.
        """
        if waiting.context != self.context or waiting.start_phase != "submitted":
            raise ValueError("submitted wait does not match pause")
        if (cancellation is not None or stop is not None) and closure is None:
            raise ValueError("stopped wait requires closure")
        cancelled = cancellation is not None or (
            stop is not None and stop.cancellation is not None
        )
        if cancelled and closure is not None and closure.end != "cancelled":
            raise ValueError("cancelled wait requires cancelled closure")
        if closure is not None and (
            closure.wait_id != waiting.wait_id or closure.context != waiting.context
        ):
            raise ValueError("closure does not belong to wait")
        return replace(waiting, start_phase="durable", end_record=closure)


@dataclass(frozen=True)
class Waiting:
    """One global wait retains trigger, cumulative bound, and start persistence."""

    context: QuotaWaitContext
    wait_id: WaitId
    started_at_utc: str
    started_monotonic: float
    start_phase: Literal["submitted", "durable"]
    end_record: WaitRecord | None
    observation: QuotaObservation

    def probe_eligible(
        self, expected_scope: QuotaScope | None, now_utc: str, /
    ) -> bool:
        """Recheck the pause and current observation against the reader binding.

        Returns:
            Whether the current exhaustion can authorize another probe.
        """
        return (
            expected_scope is not None
            and self.context.quota_observation.scope == expected_scope
            and probe_eligible(self.observation, expected_scope, now_utc)
        )

    def matches_closure(self, record: WaitRecord, /) -> bool:
        """Check that the pending closure belongs to this durable wait.

        Returns:
            Whether the phase, pending record, wait identity, and context match.
        """
        return (
            self.start_phase == "durable"
            and self.end_record == record
            and record.wait_id == self.wait_id
            and record.context == self.context
        )

    def completed(
        self,
        history: QuotaHistory,
        record: WaitRecord,
        stop: StopReason | None,
        remaining_seconds: float | None,
        now_utc: str,
        /,
    ) -> tuple[QuotaHistory, Open | QuotaStopped]:
        """Open only after durable closure and a still-fresh scoped observation.

        Returns:
            The next state built from the supplied facts.

        Raises:
            ValueError: The supplied facts do not belong to the same lifecycle.
        """
        if not self.matches_closure(record):
            raise ValueError("closure does not belong to durable wait")
        history = replace(history, waits=(*history.waits, record))
        if stop is not None or (
            remaining_seconds is not None and remaining_seconds <= 0
        ):
            return history, QuotaStopped()
        if (
            record.end == "quota_available"
            and _fresh(self.observation, self.context.quota_observation.scope, now_utc)
            and all(window.state == "available" for window in self.observation.windows)
        ):
            return history, Open()
        return history, QuotaStopped()

    def journal_failed(
        self, obligation: WaitWrite | ProbeDispatchEvent, error: BaseException, /
    ) -> QuotaEvidencePending:
        """Retain the failed journal input and any dispatched probe.

        Returns:
            The pending obligation and any active probe.
        """
        return QuotaEvidencePending(self, (QuotaWriteFailure(obligation, error),), None)


@dataclass(frozen=True)
class ProbePrepared:
    """Durable intent made before actual poll timing exists."""

    schedule: QuotaProbeSchedule
    pause_wait_id: WaitId


@dataclass(frozen=True)
class ProbeNotDispatched:
    """Close preparation without a process or probe-budget charge."""

    prepared: ProbePrepared
    cause: Literal["bound", "stop", "cancelled", "unknown"]
    ended_at_utc: str
    elapsed_seconds: float


@dataclass(frozen=True)
class ProbeDispatched:
    """Actual poll invocation with its exact request and actual timing."""

    request: QuotaProbeRequest


@dataclass(frozen=True)
class PreparingProbe:
    """Schedule and pause identity while preparation is retained and settled."""

    waiting: Waiting
    preparation: ProbePrepared

    def dispatch_gate(
        self,
        config: HarnessConfig,
        probes_used: int,
        remaining_seconds: float | None,
        stop: StopReason | None,
        cancellation: CancelledError | None,
        expected_scope: QuotaScope | None,
        ended_at_utc: str,
        elapsed_seconds: float,
        /,
    ) -> PreparingProbe | ProbeNotDispatched:
        """Gate a prepared probe using newly sampled policy and control facts.

        An invalid observation closes preparation as unknown. The owner must
        persist that event, close the wait as unknown, and stop without reopening
        dispatch. The adapter owns window completeness and source ordering.

        Returns:
            The next state built from the supplied facts.
        """
        cause: Literal["cancelled", "stop", "bound", "unknown"] | None = _control_end(
            stop, cancellation, remaining_seconds
        )
        if cause is None and not quota_probe_allowed(config, probes_used):
            cause = "bound"
        if cause is None and not self.waiting.probe_eligible(
            expected_scope, ended_at_utc
        ):
            cause = "unknown"
        if cause is None:
            return self
        return ProbeNotDispatched(
            self.preparation, cause, ended_at_utc, elapsed_seconds
        )

    def matches_request(self, request: QuotaProbeRequest, /) -> bool:
        """Check that a request belongs to this preparation and pause.

        Returns:
            Whether its schedule, pause identities, and quota scope match.
        """
        return (
            request.schedule == self.preparation.schedule
            and request.pause_wait_id == self.preparation.pause_wait_id
            and request.pause_wait_id == self.waiting.wait_id
            and request.schedule.scope == self.waiting.context.quota_observation.scope
        )

    def dispatched(self, request: QuotaProbeRequest, /) -> Probing:
        """Retain the exact request at actual invocation.

        Returns:
            The next state built from the supplied facts.

        Raises:
            ValueError: The supplied facts do not belong to the same lifecycle.
        """
        if not self.matches_request(request):
            raise ValueError("request does not belong to prepared probe")
        return Probing(self.waiting, request)

    def journal_failed(
        self, obligation: WaitWrite | ProbeDispatchEvent, error: BaseException, /
    ) -> QuotaEvidencePending:
        """Retain the failed journal input and any dispatched probe.

        Returns:
            The pending obligation and any active probe.
        """
        return QuotaEvidencePending(
            self.waiting, (QuotaWriteFailure(obligation, error),), None
        )


@dataclass(frozen=True)
class Probing:
    """The current exact request is retained while the invoked poll runs."""

    waiting: Waiting
    request: QuotaProbeRequest

    def capture(
        self, evidence: QuotaProbeEvidence | None, error: BaseException | None, /
    ) -> RecordingProbe | ProbeEvidencePending:
        """Keep exact-request evidence, or retain an unresolved obligation.

        Returns:
            The next state built from the supplied facts.
        """
        if evidence is None or evidence.request is not self.request:
            return ProbeEvidencePending(
                self.waiting,
                self.request,
                None,
                error
                if error is not None
                else ValueError("missing or mismatched probe evidence"),
            )
        return RecordingProbe(self.waiting, evidence)

    def journal_failed(
        self, obligation: WaitWrite | ProbeDispatchEvent, error: BaseException, /
    ) -> QuotaEvidencePending:
        """Retain the failed journal input and any dispatched probe.

        Returns:
            The pending obligation and any active probe.
        """
        return QuotaEvidencePending(
            self.waiting, (QuotaWriteFailure(obligation, error),), self
        )


@dataclass(frozen=True)
class RecordingProbe:
    """Captured probe evidence remains active until its write settles."""

    waiting: Waiting
    evidence: QuotaProbeEvidence

    def matches_record(self, record: QuotaProbeRecord, /) -> bool:
        """Check that a durable probe record matches the captured evidence.

        Returns:
            Whether the exact request and captured quota facts match.
        """
        return (
            record.request is self.evidence.request
            and record.quota_state == self.evidence.quota_state
            and record.observation == self.evidence.observation
        )

    def persisted(
        self,
        history: QuotaHistory,
        record: QuotaProbeRecord,
        stop: StopReason | None,
        remaining_seconds: float | None,
        now_utc: str,
        monotonic_now: float,
        /,
    ) -> tuple[QuotaHistory, Waiting]:
        """Append a durable probe and retain a pending closure when required.

        Returns:
            The next state built from the supplied facts.

        Raises:
            ValueError: The supplied facts do not belong to the same lifecycle.
        """
        if not self.matches_record(record):
            raise ValueError("probe record does not match request")
        history = replace(history, probes=(*history.probes, record))
        waiting = replace(
            self.waiting, observation=record.observation or self.waiting.observation
        )
        end: WaitEnd | None = _control_end(stop, None, remaining_seconds)
        if end is None:
            end = _probe_end(record, waiting, now_utc)
        if end is not None:
            closure = WaitRecord(
                wait_id=waiting.wait_id,
                context=waiting.context,
                started_at_utc=waiting.started_at_utc,
                ended_at_utc=now_utc,
                elapsed_seconds=max(0.0, monotonic_now - waiting.started_monotonic),
                end=end,
                diagnostic=None,
            )
            waiting = replace(waiting, end_record=closure)
        return history, waiting

    def write_failed(self, error: BaseException, /) -> ProbeEvidencePending:
        """Retain captured probe evidence and the original write error.

        Returns:
            The next state built from the supplied facts.
        """
        return ProbeEvidencePending(
            self.waiting, self.evidence.request, self.evidence, error
        )

    def journal_failed(
        self, obligation: WaitWrite | ProbeDispatchEvent, error: BaseException, /
    ) -> QuotaEvidencePending:
        """Retain the failed journal input and any dispatched probe.

        Returns:
            The pending obligation and any active probe.
        """
        return QuotaEvidencePending(
            self.waiting, (QuotaWriteFailure(obligation, error),), self
        )


@dataclass(frozen=True)
class ProbeEvidencePending:
    """An invoked probe lacks durable evidence or its required write failed."""

    waiting: Waiting
    request: QuotaProbeRequest
    evidence: QuotaProbeEvidence | None
    error: BaseException

    def journal_failed(
        self, obligation: WaitWrite | ProbeDispatchEvent, error: BaseException, /
    ) -> QuotaEvidencePending:
        """Retain the failed journal input and any dispatched probe.

        Returns:
            The pending obligation and any active probe.
        """
        return QuotaEvidencePending(
            self.waiting, (QuotaWriteFailure(obligation, error),), self
        )


@dataclass(frozen=True)
class QuotaWriteFailure:
    """The exact failed quota journal input and its original error."""

    obligation: WaitWrite | ProbeDispatchEvent
    error: BaseException


@dataclass(frozen=True)
class QuotaEvidencePending:
    """Journal failures and any invoked probe remain owned until settlement.

    The nonempty sequence preserves each failed write in order, including a
    later wait closure after a dispatch journal failure. Probe state remains
    attached while its independently required evidence settles.
    """

    waiting: Waiting
    failures: tuple[QuotaWriteFailure, *tuple[QuotaWriteFailure, ...]]
    probe: Probing | RecordingProbe | ProbeEvidencePending | None

    def journal_failed(
        self, obligation: WaitWrite | ProbeDispatchEvent, error: BaseException, /
    ) -> QuotaEvidencePending:
        """Retain a later failure without duplicating the same captured failure.

        Returns:
            The pending state with its previous failures and probe preserved.
        """
        if any(
            item.obligation is obligation and item.error is error
            for item in self.failures
        ):
            return self
        return replace(
            self, failures=(*self.failures, QuotaWriteFailure(obligation, error))
        )


@dataclass(frozen=True)
class QuotaStopped:
    """No recovery may reopen dispatch."""


@dataclass(frozen=True)
class QuotaHistory:
    """Durable quota waits and probes; in-flight facts belong to quota state."""

    waits: tuple[WaitRecord, ...]
    probes: tuple[QuotaProbeRecord, ...]


type ProbeDispatchEvent = ProbePrepared | ProbeNotDispatched | ProbeDispatched

type QuotaState = (
    Open
    | Draining
    | Waiting
    | PreparingProbe
    | Probing
    | RecordingProbe
    | ProbeEvidencePending
    | QuotaEvidencePending
    | QuotaStopped
)


def _control_end(
    stop: StopReason | None,
    cancellation: CancelledError | None,
    remaining_seconds: float | None,
    /,
) -> Literal["cancelled", "stop", "bound"] | None:
    """Select cancellation, stop, then bound in control precedence order.

    Returns:
        The first applicable control outcome, or None to continue.
    """
    if cancellation is not None or (stop is not None and stop.cancellation is not None):
        return "cancelled"
    if stop is not None:
        return "stop"
    if remaining_seconds is not None and remaining_seconds <= 0:
        return "bound"
    return None


def probe_eligible(
    observation: QuotaObservation | None,
    expected_scope: QuotaScope | None,
    now_utc: str,
    /,
) -> bool:
    """Check a normalized trigger without interpreting provider-specific windows.

    The adapter owns completeness and source ordering. All supplied windows
    must be known and at least one exhausted; equality with expiry is fresh.

    Returns:
        Whether the observation authorizes considering a paid probe.
    """
    return (
        _fresh(observation, expected_scope, now_utc)
        and observation is not None
        and any(window.state == "exhausted" for window in observation.windows)
    )


def _fresh(
    observation: QuotaObservation | None,
    expected_scope: QuotaScope | None,
    now_utc: str,
    /,
) -> bool:
    """Check whether a scoped observation remains valid at the supplied time.

    Returns:
        Whether the observation is scoped, complete, and fresh.
    """
    if (
        observation is None
        or expected_scope is None
        or observation.scope != expected_scope
        or observation.valid_until_utc is None
        or not observation.windows
    ):
        return False
    if any(
        window.state not in {"available", "exhausted"} for window in observation.windows
    ):
        return False
    try:
        expiry = datetime.fromisoformat(
            observation.valid_until_utc.replace("Z", "+00:00")
        )
        now = datetime.fromisoformat(now_utc.replace("Z", "+00:00"))
    except ValueError:
        return False
    return expiry.tzinfo is not None and now.tzinfo is not None and now <= expiry


def _probe_end(
    record: QuotaProbeRecord, waiting: Waiting, now_utc: str, /
) -> WaitEnd | None:
    observation = record.observation
    if record.control_flow != "returned" or record.outcome_kind != "completed":
        return "unknown"
    if record.cleanup is None or record.cleanup.process != "owned":
        return "unknown"
    if not safe_process_cleanup(record) or not _fresh(
        observation, waiting.context.quota_observation.scope, now_utc
    ):
        return "unknown"
    if observation is None:
        return "unknown"
    if record.quota_state == "exhausted" and any(
        window.state == "exhausted" for window in observation.windows
    ):
        return None
    if (
        record.quota_state == "available"
        and record.exit_status == 0
        and all(window.state == "available" for window in observation.windows)
    ):
        return "quota_available"
    return "unknown"
