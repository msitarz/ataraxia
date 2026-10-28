# SPDX-License-Identifier: Apache-2.0
"""Coordinator state; durable history and each in-flight fact have one owner."""

from asyncio import CancelledError
from dataclasses import dataclass
from typing import Literal

from script.eval.model import (
    AttemptEvidence,
    AttemptNumber,
    AttemptRecord,
    CapacityWaitContext,
    QuotaObservation,
    QuotaProbeEvidence,
    QuotaProbeRecord,
    QuotaProbeRequest,
    QuotaProbeSchedule,
    QuotaTelemetryEvent,
    QuotaWaitContext,
    RetryAssessment,
    WaitEvent,
    WaitId,
    WaitRecord,
)
from script.eval.runner.ports import EffectiveCall
from script.process_supervisor import AttemptResult


@dataclass(frozen=True)
class CallHistory:
    """Durable records for one position; the active attempt is not in history."""

    call: EffectiveCall
    attempts: tuple[AttemptRecord, ...]
    waits: tuple[WaitRecord, ...]


@dataclass(frozen=True)
class AttemptWrite:
    """Captured attempt and classification retained until the write succeeds."""

    number: AttemptNumber
    evidence: AttemptEvidence
    assessment: RetryAssessment | None


@dataclass(frozen=True)
class WaitWrite:
    """A failed wait event and its pending final summary, if closing."""

    event: WaitEvent
    record: WaitRecord | None


@dataclass(frozen=True)
class CallEvidenceFailure:
    """A failed obligation and error; history retains any durable attempt."""

    obligation: AttemptWrite | WaitWrite | QuotaTelemetryEvent
    error: BaseException


@dataclass(frozen=True)
class CallWait:
    """A call-local wait from preparation through durable end.

    A prepared wait has a sampled delay but no submitted start write. The owner
    submits and retains that write until it settles. ``start_phase`` determines
    whether cancellation must close the wait; monotonic time and the sampled
    delay support progress without a parallel timer ledger.
    """

    wait_id: WaitId
    context: CapacityWaitContext
    started_at_utc: str
    started_monotonic: float
    start_phase: Literal["prepared", "submitted", "durable"]
    end_record: WaitRecord | None


@dataclass(frozen=True)
class Queued:
    """Runnable or gated planned position; history distinguishes a retry."""

    history: CallHistory


@dataclass(frozen=True)
class Attempting:
    """One dispatched invocation, including its supervisor cleanup."""

    history: CallHistory
    attempt_number: AttemptNumber


@dataclass(frozen=True)
class Recording:
    """A captured attempt whose required write has not yet settled."""

    history: CallHistory
    attempt: AttemptWrite


@dataclass(frozen=True)
class ObservingQuota:
    """The attempt is durable; the adapter is ingesting its passive evidence."""

    history: CallHistory
    attempt_number: AttemptNumber
    evidence: AttemptEvidence


@dataclass(frozen=True)
class RecordingTelemetry:
    """The attempt is durable and its observed telemetry write is pending."""

    history: CallHistory
    event: QuotaTelemetryEvent


@dataclass(frozen=True)
class RetryWait:
    """A capacity delay owned by this call, not the quota gate."""

    history: CallHistory
    wait: CallWait


@dataclass(frozen=True)
class Finished:
    """A durable terminal call outcome."""

    history: CallHistory
    outcome: Literal["success", "failure", "cancelled"]


@dataclass(frozen=True)
class EvidencePending:
    """The failed obligation retains the attempt or wait facts for inspection."""

    history: CallHistory
    failure: CallEvidenceFailure


@dataclass(frozen=True)
class Stopped:
    """Stop forbids further dispatch; empty attempt history is not started."""

    history: CallHistory
    outcome: Literal["not_started", "failure", "cancelled"]


type CallState = (
    Queued
    | Attempting
    | Recording
    | ObservingQuota
    | RecordingTelemetry
    | RetryWait
    | Finished
    | EvidencePending
    | Stopped
)


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


@dataclass(frozen=True)
class ProbePrepared:
    """Durable intent made before actual poll timing exists."""

    schedule: QuotaProbeSchedule
    pause_wait_id: WaitId


@dataclass(frozen=True)
class ProbeNotDispatched:
    """Close preparation without a process or probe-budget charge."""

    prepared: ProbePrepared
    cause: Literal["bound", "stop", "cancelled"]
    ended_at_utc: str
    elapsed_seconds: float


@dataclass(frozen=True)
class ProbeDispatched:
    """Actual poll invocation with its exact request and actual timing."""

    request: QuotaProbeRequest


type ProbeDispatchEvent = ProbePrepared | ProbeNotDispatched | ProbeDispatched


@dataclass(frozen=True)
class PreparingProbe:
    """Schedule and pause identity while preparation is retained and settled."""

    waiting: Waiting
    preparation: ProbePrepared


@dataclass(frozen=True)
class Probing:
    """The current exact request is retained while the invoked poll runs."""

    waiting: Waiting
    request: QuotaProbeRequest


@dataclass(frozen=True)
class RecordingProbe:
    """Captured probe evidence remains active until its write settles."""

    waiting: Waiting
    evidence: QuotaProbeEvidence


@dataclass(frozen=True)
class ProbeEvidencePending:
    """An invoked probe lacks durable evidence or its required write failed."""

    waiting: Waiting
    request: QuotaProbeRequest
    evidence: QuotaProbeEvidence | None
    error: BaseException


@dataclass(frozen=True)
class QuotaEvidencePending:
    """A failed wait or probe journal write retains its obligation.

    A dispatch journal may fail while the invoked probe is still settling. Its
    state remains attached until the owner captures and persists that outcome.
    """

    waiting: Waiting
    obligation: WaitWrite | ProbeDispatchEvent
    error: BaseException
    probe: Probing | RecordingProbe | ProbeEvidencePending | None


@dataclass(frozen=True)
class QuotaStopped:
    """No recovery may reopen dispatch."""


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


@dataclass(frozen=True)
class QuotaHistory:
    """Durable quota waits and probes; in-flight facts belong to quota state."""

    waits: tuple[WaitRecord, ...]
    probes: tuple[QuotaProbeRecord, ...]


@dataclass(frozen=True)
class StopReason:
    """First stop and original owner or leaf cancellation, if one occurs later.

    Internal sibling cancellations do not replace the primary control flow.
    Recording failure is retained and attached as cause when cancellation wins.
    """

    first: BaseException | AttemptResult
    cancellation: CancelledError | None
    cancellation_origin: Literal["owner", "leaf"] | None
    recording_failure: BaseException | None
