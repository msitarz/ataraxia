# SPDX-License-Identifier: Apache-2.0
"""Historical free-function transitions; runtime state methods are authoritative.

The runtime async quota owner is authoritative; run composition remains planned.
"""

from asyncio import CancelledError

from script.eval.evidence import EvidenceStore
from script.eval.model import (
    HarnessConfig,
    QuotaObservation,
    QuotaProbeEvidence,
    QuotaProbeRecord,
    QuotaProbeRequest,
    QuotaScope,
    RunId,
    WaitRecord,
)
from script.eval.runner.coordinator.quota_states import (
    Draining,
    Open,
    PreparingProbe,
    ProbeDispatchEvent,
    ProbeEvidencePending,
    ProbeNotDispatched,
    Probing,
    QuotaEvidencePending,
    QuotaHistory,
    QuotaState,
    QuotaStopped,
    RecordingProbe,
    Waiting,
)
from script.eval.runner.coordinator.state import (
    StopReason,
    WaitWrite,
)
from script.eval.runner.ports import QuotaStatusReader, Runtime

from .control import RunControl

def quota_wait_started(
    state: Draining,
    waiting: Waiting,
    cancellation: CancelledError | None,
    stop: StopReason | None,
    closure: WaitRecord | None,
    /,
) -> Waiting:
    """Settle the durable start after drain; cancellation or stop requires closure.

    Cancellation or stop supplies a pending closure retained in Waiting. The
    owner writes it before reporting stop or propagating cancellation.
    """
    ...

def probe_eligible(
    observation: QuotaObservation | None,
    expected_scope: QuotaScope | None,
    now_utc: str,
    /,
) -> bool:
    """Require a fresh, scoped, known exhausted observation before probing."""
    ...

def probe_dispatch_gate(
    state: PreparingProbe,
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
    """Recheck freshness, reader scope, bounds and stop after preparation settles.

    A returned preparation permits the effect owner to construct the actual
    request at invocation; otherwise it must durably close the preparation.
    No request timestamp or probe charge is created here.
    """
    ...

def probe_dispatched(state: PreparingProbe, request: QuotaProbeRequest, /) -> Probing:
    """Retain the request constructed by the owner at actual invocation."""
    ...

def capture_probe(
    state: Probing, evidence: QuotaProbeEvidence | None, error: BaseException | None, /
) -> RecordingProbe | ProbeEvidencePending:
    """Retain exact-request evidence, including evidence from an exception chain.

    Missing or mismatched evidence stays pending with an explicit error; a timeout
    never becomes availability. The effect owner extracts evidence before this call.
    """
    ...

def probe_persisted(
    state: RecordingProbe,
    history: QuotaHistory,
    record: QuotaProbeRecord,
    stop: StopReason | None,
    remaining_seconds: float | None,
    now_utc: str,
    monotonic_now: float,
    /,
) -> tuple[QuotaHistory, Waiting]:
    """Append durable probe evidence and decide whether the wait must close.

    Only the trusted adapter's fresh, complete matching-scope observation for
    this pause can authorize availability at the supplied time. Stop and bounds
    win. A required closure is retained as Waiting.end_record using the supplied
    clocks; continued exhaustion leaves it empty. The owner writes that closure
    before quota_wait_completed can open or stop the quota state. The shared stop
    latch may already have closed dispatch.
    """
    ...

def quota_wait_completed(
    state: Waiting,
    history: QuotaHistory,
    record: WaitRecord,
    stop: StopReason | None,
    remaining_seconds: float | None,
    now_utc: str,
    /,
) -> tuple[QuotaHistory, Open | QuotaStopped]:
    """Append the durable wait closure before opening or stopping the gate.

    Only a quota-available closure supported by the current verified observation
    opens the gate if still fresh at the supplied time; stop, bound, and all
    other ends leave it stopped.
    """
    ...

def quota_write_failed(
    state: Waiting | PreparingProbe | Probing | RecordingProbe | ProbeEvidencePending,
    obligation: WaitWrite | ProbeDispatchEvent,
    error: BaseException,
    /,
) -> QuotaEvidencePending:
    """Retain the exact journal input, error, and any dispatched probe state.

    The owner still settles an invoked probe and its evidence after this failure.
    """
    ...

def probe_write_failed(
    state: RecordingProbe, error: BaseException, /
) -> ProbeEvidencePending:
    """Keep captured exact-request evidence when its required write fails."""
    ...

class QuotaOwner:
    """Own the current pause and its durable probe history."""

    def __init__(
        self,
        initial: Draining,
        history: QuotaHistory,
        config: HarnessConfig,
        control: RunControl,
        reader: QuotaStatusReader,
        evidence: EvidenceStore,
        runtime: Runtime,
        run_id: RunId,
    ) -> None: ...
    @property
    def state(self) -> QuotaState: ...
    @property
    def history(self) -> QuotaHistory: ...
    @property
    def observation(self) -> QuotaObservation | None: ...
    async def recover(self) -> QuotaState:
        """Recover after the run owner drains and persists all active attempts."""
        ...
