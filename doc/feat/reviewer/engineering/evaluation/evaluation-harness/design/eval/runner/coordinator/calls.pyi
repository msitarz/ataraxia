# SPDX-License-Identifier: Apache-2.0
"""Historical reviewed pure transition signatures; async owner remains planned."""

from asyncio import CancelledError, Semaphore

from script.eval.evidence import EvidenceStore
from script.eval.model import (
    AttemptEvidence,
    AttemptRecord,
    HarnessConfig,
    QuotaTelemetryEvent,
    RetryAssessment,
    WaitRecord,
)
from script.eval.runner.coordinator.call_states import (
    Attempting,
    CallState,
    CallWait,
    EvidencePending,
    Finished,
    ObservingQuota,
    Queued,
    Recording,
    RecordingTelemetry,
    RetryWait,
    Stopped,
)
from script.eval.runner.coordinator.state import (
    StopReason,
    WaitWrite,
)
from script.eval.runner.ports import (
    AttemptCall,
    OutcomeClassifier,
    QuotaStatusReader,
    Runtime,
)

from .control import RunControl

def capture_attempt(
    state: Attempting, evidence: AttemptEvidence, assessment: RetryAssessment | None, /
) -> Recording:
    """Retain settled supervisor evidence and its classification before writing."""
    ...

def attempt_persisted(
    state: Recording,
    record: AttemptRecord,
    config: HarnessConfig,
    stop: StopReason | None,
    capacity_wait: CallWait | None,
    /,
) -> ObservingQuota | RetryWait | Queued | Finished | Stopped:
    """Append the durable record and decide using policy and supplied wait facts.

    Passive observation is selected only when enabled. Retry eligibility uses
    the independent allowances in history, safe cleanup, and no-result evidence.
    A supplied capacity wait is prepared with sampled context and jitter; the
    owner submits its start only if selected. An infrastructure retry queues
    without a capacity delay. Stop wins.
    """
    ...

def capture_telemetry(
    state: ObservingQuota, event: QuotaTelemetryEvent, /
) -> RecordingTelemetry:
    """Retain the adapter observation as the exact event to be written."""
    ...

def telemetry_persisted(
    state: RecordingTelemetry,
    config: HarnessConfig,
    stop: StopReason | None,
    capacity_wait: CallWait | None,
    /,
) -> RetryWait | Queued | Finished | Stopped:
    """Decide after durable telemetry with the same retry policy.

    A supplied capacity wait is prepared, not yet submitted.
    """
    ...

def attempt_write_failed(state: Recording, error: BaseException, /) -> EvidencePending:
    """Retain the captured attempt, error, and prior durable history."""
    ...

def telemetry_write_failed(
    state: RecordingTelemetry, error: BaseException, /
) -> EvidencePending:
    """Retain the exact telemetry event, error, and durable attempt history."""
    ...

def call_wait_write_failed(
    state: RetryWait, obligation: WaitWrite, error: BaseException, /
) -> EvidencePending:
    """Retain the exact failed wait input and already durable history."""
    ...

def call_wait_started(
    state: RetryWait,
    cancellation: CancelledError | None,
    stop: StopReason | None,
    closure: WaitRecord | None,
    /,
) -> RetryWait:
    """Mark a successfully settled submitted start durable.

    Cancellation or stop requires a durable end.

    When cancellation or stop occurred, closure supplies the pending end record
    retained in the returned wait. The owner writes it before propagation.
    A normal start may proceed to the cancellable wait.
    """
    ...

def call_wait_completed(
    state: RetryWait, record: WaitRecord, stop: StopReason | None, /
) -> Queued | Stopped:
    """Append a durably closed wait before requeueing or honoring stop."""
    ...

class CallOwner:
    """Own and expose one call's current state through all submitted effects."""

    def __init__(
        self,
        initial: Queued,
        config: HarnessConfig,
        control: RunControl,
        slots: Semaphore,
        attempt: AttemptCall,
        classifier: OutcomeClassifier,
        quota_status: QuotaStatusReader,
        evidence: EvidenceStore,
        runtime: Runtime,
    ) -> None: ...
    @property
    def state(self) -> CallState: ...
    async def run(self) -> CallState:
        """Settle the call or stop it; retain submitted writes during cancellation."""
        ...
