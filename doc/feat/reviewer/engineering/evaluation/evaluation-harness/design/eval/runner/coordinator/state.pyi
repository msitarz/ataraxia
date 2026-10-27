# SPDX-License-Identifier: Apache-2.0
"""Exploratory coordinator state; not an active runtime interface."""

from dataclasses import dataclass
from typing import Literal

from script.eval.model import (
    AttemptEvidence,
    AttemptRecord,
    QuotaObservation,
    QuotaProbeRecord,
    QuotaProbeRequest,
    WaitRecord,
)
from script.eval.runner.ports import EffectiveCall

@dataclass(frozen=True)
class CallHistory:
    """Durable attempts and waits owned by one planned position."""

    call: EffectiveCall
    attempts: tuple[AttemptRecord, ...]
    waits: tuple[WaitRecord, ...]
    infrastructure_retries: int
    capacity_retries: int

@dataclass(frozen=True)
class Queued:
    history: CallHistory

@dataclass(frozen=True)
class Attempting:
    history: CallHistory
    attempt_number: int

@dataclass(frozen=True)
class Recording:
    history: CallHistory
    attempt_number: int
    evidence: AttemptEvidence

@dataclass(frozen=True)
class RetryWait:
    history: CallHistory
    reason: Literal["infrastructure", "capacity", "quota"]

@dataclass(frozen=True)
class Finished:
    history: CallHistory
    outcome: Literal["success", "failure", "cancelled"]

@dataclass(frozen=True)
class EvidencePending:
    history: CallHistory
    """A required write failed; the corresponding outcome is not durable."""

@dataclass(frozen=True)
class Stopped:
    history: CallHistory
    """No further attempt is permitted; empty history remains not started."""

type CallState = (
    Queued | Attempting | Recording | RetryWait | Finished | EvidencePending | Stopped
)

@dataclass(frozen=True)
class Open:
    pass

@dataclass(frozen=True)
class Draining:
    observation: QuotaObservation

@dataclass(frozen=True)
class Waiting:
    observation: QuotaObservation
    wait_id: str
    cumulative_seconds: float

@dataclass(frozen=True)
class Probing:
    waiting: Waiting
    request: QuotaProbeRequest

@dataclass(frozen=True)
class QuotaStopped:
    pass

type QuotaState = Open | Draining | Waiting | Probing | QuotaStopped

@dataclass(frozen=True)
class ProbeHistory:
    """Durable probe results are distinct from evaluation attempts."""

    probes: tuple[QuotaProbeRecord, ...]

@dataclass(frozen=True)
class Running:
    """The run owner may dispatch subject to the quota gate."""

@dataclass(frozen=True)
class Stopping:
    """The first reason owns shutdown; sibling cancellations are secondary."""

    reason: BaseException | str
    cancellation_origin: Literal["owner", "leaf", "internal"] | None

@dataclass(frozen=True)
class Final:
    outcome: Literal["success", "failure", "cancelled", "incomplete_evidence"]

type RunPhase = Running | Stopping | Final
