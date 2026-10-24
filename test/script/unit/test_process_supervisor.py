# SPDX-License-Identifier: Apache-2.0
"""Wiring tests for the experimental process-supervisor increment."""

import asyncio
from dataclasses import dataclass, replace
from pathlib import Path
from typing import override

import pytest

from script.process_supervisor import (
    AttemptCancelled,
    AttemptFailureEvidence,
    AttemptObservation,
    AttemptRequest,
    AttemptResult,
    CapturedOutput,
    CleanupEvidence,
    CleanupOutcome,
    Completed,
    InfrastructureFailure,
    NativeProcessEffects,
    NotLaunched,
    OutputLimitExceeded,
    ProcessHandle,
    TimedOut,
    call_supervisor,
    failure_evidence,
    run_attempt,
)


@pytest.fixture
def attempt_request() -> AttemptRequest:
    """Provide a fully specified request with the caller's absolute CLI path."""
    return AttemptRequest(
        argv=("/usr/local/bin/codex", "exec", "--"),
        cwd=Path("/tmp/evaluation"),
        timeout_seconds=30.0,
        cleanup_timeout_seconds=5.0,
        output_limit_bytes=1_048_576,
        stdin="devnull",
    )


@dataclass(frozen=True)
class FakeHandle:
    pid: int = 701
    process_group_id: int = 701


@dataclass(frozen=True)
class ClockRead:
    value: float


@dataclass(frozen=True)
class AcquireCall:
    request: AttemptRequest


@dataclass(frozen=True)
class CaptureCall:
    handle: ProcessHandle
    request: AttemptRequest
    execution_deadline: float


@dataclass(frozen=True)
class CleanupCall:
    handle: ProcessHandle
    timeout_seconds: float


type WireEvent = ClockRead | AcquireCall | CaptureCall | CleanupCall

PENDING_CLEANUP = CleanupEvidence("owned", "not_started", None, "not_started", None)
FINAL_CLEANUP = CleanupEvidence("owned", "sent", None, "reaped", None)


class FakeClock:
    def __init__(self, events: list[WireEvent]) -> None:
        self.events = events
        self.value = 10.0

    def monotonic(self) -> float:
        self.events.append(ClockRead(self.value))
        return self.value


class FakeEffects:
    def __init__(self, events: list[WireEvent], clock: FakeClock) -> None:
        self.events = events
        self.clock = clock
        self.handle = FakeHandle()

    async def acquire(self, request: AttemptRequest, /) -> ProcessHandle | NotLaunched:
        self.events.append(AcquireCall(request))
        self.clock.value = 11.0
        return self.handle

    async def capture(
        self,
        handle: ProcessHandle,
        request: AttemptRequest,
        execution_deadline: float,
        /,
    ) -> AttemptResult:
        self.events.append(CaptureCall(handle, request, execution_deadline))
        self.clock.value = 12.0
        return Completed(
            AttemptObservation(
                CapturedOutput(b"result\n", b"diagnostic\n"),
                0.25,
                CleanupEvidence("owned", "not_started", None, "not_started", None),
            ),
            0,
        )

    async def cleanup(
        self, handle: ProcessHandle, timeout_seconds: float, /
    ) -> CleanupOutcome:
        self.events.append(CleanupCall(handle, timeout_seconds))
        self.clock.value = 13.5
        return CleanupOutcome(CleanupEvidence("owned", "sent", None, "reaped", None))


class FailingCaptureEffects(FakeEffects):
    @override
    async def capture(
        self,
        handle: ProcessHandle,
        request: AttemptRequest,
        execution_deadline: float,
        /,
    ) -> AttemptResult:
        await asyncio.sleep(0)
        await super().capture(handle, request, execution_deadline)
        raise self.error

    def __init__(
        self,
        events: list[WireEvent],
        clock: FakeClock,
        error_type: type[Exception],
    ) -> None:
        super().__init__(events, clock)
        self.error = error_type("capture failed")


class CancellingCaptureEffects(FakeEffects):
    @override
    async def capture(
        self,
        handle: ProcessHandle,
        request: AttemptRequest,
        execution_deadline: float,
        /,
    ) -> AttemptResult:
        await asyncio.sleep(0)
        await super().capture(handle, request, execution_deadline)
        raise self.cancellation

    def __init__(self, events: list[WireEvent], clock: FakeClock) -> None:
        super().__init__(events, clock)
        self.cancellation = AttemptCancelled(
            AttemptObservation(
                CapturedOutput(b"partial stdout", b"partial stderr"),
                1.25,
                CleanupEvidence("owned", "unknown", None, "unknown", None),
            )
        )


class OutcomeEffects(FakeEffects):
    @override
    async def capture(
        self,
        handle: ProcessHandle,
        request: AttemptRequest,
        execution_deadline: float,
        /,
    ) -> AttemptResult:
        self.events.append(CaptureCall(handle, request, execution_deadline))
        self.clock.value = 12.0
        return self.result

    def __init__(
        self,
        events: list[WireEvent],
        clock: FakeClock,
        result: AttemptResult,
    ) -> None:
        super().__init__(events, clock)
        self.result = result


class CancellingTaskEffects(FakeEffects):
    def __init__(self, events: list[WireEvent], clock: FakeClock) -> None:
        super().__init__(events, clock)
        self.capture_started = asyncio.Event()
        self.cleanup_started = asyncio.Event()
        self.cleanup_release = asyncio.Event()

    @override
    async def capture(
        self,
        handle: ProcessHandle,
        request: AttemptRequest,
        execution_deadline: float,
        /,
    ) -> AttemptResult:
        self.capture_started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError as exc:
            raise AttemptCancelled(
                AttemptObservation(
                    CapturedOutput(b"partial stdout", b"partial stderr"),
                    None,
                    PENDING_CLEANUP,
                )
            ) from exc
        raise AssertionError("capture wait completed without cancellation")

    @override
    async def cleanup(
        self, handle: ProcessHandle, timeout_seconds: float, /
    ) -> CleanupOutcome:
        self.events.append(CleanupCall(handle, timeout_seconds))
        self.cleanup_started.set()
        await self.cleanup_release.wait()
        self.clock.value = 13.5
        return CleanupOutcome(
            CleanupEvidence("owned", "sent", None, "reaped", None), 143
        )


class RawCancellingCaptureEffects(FakeEffects):
    def __init__(self, events: list[WireEvent], clock: FakeClock) -> None:
        super().__init__(events, clock)
        self.capture_started = asyncio.Event()

    @override
    async def capture(
        self,
        handle: ProcessHandle,
        request: AttemptRequest,
        execution_deadline: float,
        /,
    ) -> AttemptResult:
        self.capture_started.set()
        await asyncio.Event().wait()
        raise AssertionError("capture wait completed without cancellation")


class PostKillStatusEffects(FakeEffects):
    def __init__(
        self,
        events: list[WireEvent],
        clock: FakeClock,
        result: AttemptResult,
    ) -> None:
        super().__init__(events, clock)
        self.result = result

    @override
    async def capture(
        self,
        handle: ProcessHandle,
        request: AttemptRequest,
        execution_deadline: float,
        /,
    ) -> AttemptResult:
        self.events.append(CaptureCall(handle, request, execution_deadline))
        return self.result

    @override
    async def cleanup(
        self, handle: ProcessHandle, timeout_seconds: float, /
    ) -> CleanupOutcome:
        self.events.append(CleanupCall(handle, timeout_seconds))
        self.clock.value = 13.5
        return CleanupOutcome(
            CleanupEvidence("owned", "sent", None, "reaped", None), 137
        )


class DelayedAcquisitionEffects(FakeEffects):
    def __init__(self, events: list[WireEvent], clock: FakeClock) -> None:
        super().__init__(events, clock)
        self.acquire_started = asyncio.Event()
        self.acquire_release = asyncio.Event()
        self.acquire_finished = asyncio.Event()

    @override
    async def acquire(self, request: AttemptRequest, /) -> ProcessHandle | NotLaunched:
        self.events.append(AcquireCall(request))
        self.acquire_started.set()
        await self.acquire_release.wait()
        self.acquire_finished.set()
        return self.handle


class DelayedAcquisitionErrorEffects(DelayedAcquisitionEffects):
    def __init__(self, events: list[WireEvent], clock: FakeClock) -> None:
        super().__init__(events, clock)
        self.error = OSError("acquisition completed with failure")

    @override
    async def acquire(self, request: AttemptRequest, /) -> ProcessHandle | NotLaunched:
        self.events.append(AcquireCall(request))
        self.acquire_started.set()
        await self.acquire_release.wait()
        self.acquire_finished.set()
        raise self.error


class DelayedNoLaunchEffects(DelayedAcquisitionEffects):
    @override
    async def acquire(self, request: AttemptRequest, /) -> ProcessHandle | NotLaunched:
        self.events.append(AcquireCall(request))
        self.acquire_started.set()
        await self.acquire_release.wait()
        self.acquire_finished.set()
        return NotLaunched("PermissionError", "launch safely refused")


class CompletedCleanupEffects(FakeEffects):
    def __init__(
        self,
        events: list[WireEvent],
        clock: FakeClock,
        *,
        cleanup_error: Exception | None = None,
    ) -> None:
        super().__init__(events, clock)
        self.cleanup_error = cleanup_error
        self.cleanup_started = asyncio.Event()
        self.cleanup_release = asyncio.Event()

    @override
    async def capture(
        self,
        handle: ProcessHandle,
        request: AttemptRequest,
        execution_deadline: float,
        /,
    ) -> AttemptResult:
        return Completed(
            AttemptObservation(CapturedOutput(b"done", b""), 1.0, PENDING_CLEANUP),
            7,
        )

    @override
    async def cleanup(
        self, handle: ProcessHandle, timeout_seconds: float, /
    ) -> CleanupOutcome:
        self.events.append(CleanupCall(handle, timeout_seconds))
        self.cleanup_started.set()
        await self.cleanup_release.wait()
        if self.cleanup_error is not None:
            raise self.cleanup_error
        return CleanupOutcome(FINAL_CLEANUP)


class NonconfirmedCleanupEffects(FakeEffects):
    @override
    async def cleanup(
        self, handle: ProcessHandle, timeout_seconds: float, /
    ) -> CleanupOutcome:
        self.events.append(CleanupCall(handle, timeout_seconds))
        return CleanupOutcome(
            CleanupEvidence(
                "owned", "failed", "PermissionError: denied", "expired", "deadline"
            )
        )


class CleanupCrashesEffects(FailingCaptureEffects):
    @override
    async def cleanup(
        self, handle: ProcessHandle, timeout_seconds: float, /
    ) -> CleanupOutcome:
        self.events.append(CleanupCall(handle, timeout_seconds))
        raise RuntimeError("cleanup implementation bug")


class WaitingCleanupAfterCaptureFailure(FailingCaptureEffects):
    def __init__(
        self,
        events: list[WireEvent],
        clock: FakeClock,
    ) -> None:
        super().__init__(events, clock, ValueError)
        self.cleanup_started = asyncio.Event()
        self.cleanup_release = asyncio.Event()

    @override
    async def cleanup(
        self, handle: ProcessHandle, timeout_seconds: float, /
    ) -> CleanupOutcome:
        self.events.append(CleanupCall(handle, timeout_seconds))
        self.cleanup_started.set()
        await self.cleanup_release.wait()
        return CleanupOutcome(FINAL_CLEANUP)


class SuccessfulCaptureCleanupCrashesEffects(FakeEffects):
    @override
    async def cleanup(
        self, handle: ProcessHandle, timeout_seconds: float, /
    ) -> CleanupOutcome:
        self.events.append(CleanupCall(handle, timeout_seconds))
        raise RuntimeError("cleanup implementation bug")


def test_attempt_wires_request_through_owned_effect_sequence(
    attempt_request: AttemptRequest,
) -> None:
    # Given
    events: list[WireEvent] = []
    clock = FakeClock(events)
    effects = FakeEffects(events, clock)

    # When
    result = asyncio.run(run_attempt(attempt_request, effects, clock))

    # Then
    assert events == [
        ClockRead(10.0),
        AcquireCall(attempt_request),
        CaptureCall(effects.handle, attempt_request, 40.0),
        CleanupCall(effects.handle, 5.0),
        ClockRead(13.5),
    ]
    assert isinstance(result, Completed)
    assert result.exit_status == 0
    assert result.observation.output == CapturedOutput(b"result\n", b"diagnostic\n")
    assert result.observation.elapsed_seconds == pytest.approx(3.5)
    assert result.observation.cleanup.confirmed


@pytest.mark.parametrize(
    "error_type",
    [
        pytest.param(ValueError, id="programmer-error"),
        pytest.param(NotImplementedError, id="pending-leaf-error"),
    ],
)
def test_capture_failure_cleans_owned_handle_and_preserves_failure(
    attempt_request: AttemptRequest,
    error_type: type[Exception],
) -> None:
    # Given
    events: list[WireEvent] = []
    clock = FakeClock(events)
    effects = FailingCaptureEffects(events, clock, error_type)

    # When
    with pytest.raises(error_type) as raised:
        asyncio.run(run_attempt(attempt_request, effects, clock))

    # Then
    assert events[1:4] == [
        AcquireCall(attempt_request),
        CaptureCall(effects.handle, attempt_request, 40.0),
        CleanupCall(effects.handle, 5.0),
    ]
    assert raised.value is effects.error
    evidence = failure_evidence(raised.value)
    assert isinstance(evidence, AttemptFailureEvidence)
    assert evidence.observation.cleanup.confirmed


def test_default_unimplemented_acquisition_remains_visible(
    attempt_request: AttemptRequest,
) -> None:
    # Given
    clock = FakeClock([])

    # When
    with pytest.raises(NotImplementedError, match="process acquisition is pending"):
        asyncio.run(run_attempt(attempt_request, NativeProcessEffects(), clock))

    # Then
    assert clock.value == pytest.approx(10.0)


def test_capture_cancellation_cleans_owned_handle_and_propagates_evidence(
    attempt_request: AttemptRequest,
) -> None:
    # Given
    events: list[WireEvent] = []
    clock = FakeClock(events)
    effects = CancellingCaptureEffects(events, clock)

    # When
    with pytest.raises(AttemptCancelled) as raised:
        asyncio.run(run_attempt(attempt_request, effects, clock))

    # Then
    assert events[1:4] == [
        AcquireCall(attempt_request),
        CaptureCall(effects.handle, attempt_request, 40.0),
        CleanupCall(effects.handle, 5.0),
    ]
    assert raised.value is effects.cancellation
    assert raised.value.observation.output == CapturedOutput(
        b"partial stdout", b"partial stderr"
    )
    assert raised.value.observation.cleanup.confirmed
    assert raised.value.observation.elapsed_seconds == pytest.approx(3.5)


def test_repeated_task_cancellation_waits_for_cleanup_and_forwards_observed_status(
    attempt_request: AttemptRequest,
) -> None:
    # Given
    events: list[WireEvent] = []
    clock = FakeClock(events)
    effects = CancellingTaskEffects(events, clock)

    async def run_cancelled_attempt() -> AttemptCancelled:
        task = asyncio.create_task(run_attempt(attempt_request, effects, clock))
        await effects.capture_started.wait()
        task.cancel()
        await effects.cleanup_started.wait()
        task.cancel()
        effects.cleanup_release.set()
        with pytest.raises(AttemptCancelled) as raised:
            await task
        return raised.value

    # When
    cancellation = asyncio.run(run_cancelled_attempt())

    # Then
    assert cancellation.observation.output == CapturedOutput(
        b"partial stdout", b"partial stderr"
    )
    assert cancellation.observation.cleanup.confirmed
    assert cancellation.exit_status == 143
    assert events.count(CleanupCall(effects.handle, 5.0)) == 1


def test_raw_task_cancellation_reports_only_bytes_observed_by_composition(
    attempt_request: AttemptRequest,
) -> None:
    # Given
    events: list[WireEvent] = []
    clock = FakeClock(events)
    effects = RawCancellingCaptureEffects(events, clock)

    async def run_cancelled_attempt() -> AttemptCancelled:
        task = asyncio.create_task(run_attempt(attempt_request, effects, clock))
        await effects.capture_started.wait()
        task.cancel()
        with pytest.raises(AttemptCancelled) as raised:
            await task
        return raised.value

    # When
    cancellation = asyncio.run(run_cancelled_attempt())

    # Then
    assert cancellation.observation.output == CapturedOutput(b"", b"")
    assert cancellation.observation.cleanup.confirmed


def test_acquisition_cancellation_settles_owned_handle_before_cleanup(
    attempt_request: AttemptRequest,
) -> None:
    # Given
    events: list[WireEvent] = []
    clock = FakeClock(events)
    effects = DelayedAcquisitionEffects(events, clock)

    async def run_cancelled_attempt() -> AttemptCancelled:
        task = asyncio.create_task(run_attempt(attempt_request, effects, clock))
        await effects.acquire_started.wait()
        task.cancel()
        effects.acquire_release.set()
        with pytest.raises(AttemptCancelled) as raised:
            await task
        return raised.value

    # When
    cancellation = asyncio.run(run_cancelled_attempt())

    # Then
    assert cancellation.observation.cleanup.confirmed
    assert events.count(CleanupCall(effects.handle, 5.0)) == 1
    assert not any(isinstance(event, CaptureCall) for event in events)


@pytest.mark.parametrize(
    ("effects_type", "cleanup_process", "cause_type"),
    [
        pytest.param(
            DelayedAcquisitionErrorEffects,
            "acquisition_uncertain",
            OSError,
            id="acquisition-error",
        ),
        pytest.param(
            DelayedNoLaunchEffects,
            "not_started",
            asyncio.CancelledError,
            id="proven-no-launch",
        ),
    ],
)
def test_cancellation_during_acquisition_propagates_after_late_settlement(
    attempt_request: AttemptRequest,
    effects_type: type[DelayedAcquisitionEffects],
    cleanup_process: str,
    cause_type: type[BaseException],
) -> None:
    # Given
    events: list[WireEvent] = []
    clock = FakeClock(events)
    effects = effects_type(events, clock)
    stops: list[AttemptResult | asyncio.CancelledError | Exception] = []

    async def attempt(request: AttemptRequest, /) -> AttemptResult:
        return await run_attempt(request, effects, clock)

    async def cancel_during_acquisition() -> AttemptCancelled:
        task = asyncio.create_task(
            call_supervisor(attempt_request, attempt, stops.append)
        )
        await effects.acquire_started.wait()
        task.cancel()
        effects.acquire_release.set()
        with pytest.raises(AttemptCancelled) as raised:
            await task
        return raised.value

    # When
    cancellation = asyncio.run(cancel_during_acquisition())

    # Then
    assert stops == [cancellation]
    assert not any(isinstance(event, CaptureCall) for event in events)
    assert cancellation.observation.cleanup.process == cleanup_process
    assert isinstance(cancellation.__cause__, cause_type)
    assert effects.acquire_finished.is_set()


def test_proven_no_launch_returns_confirmed_infrastructure_observation(
    attempt_request: AttemptRequest,
) -> None:
    # Given
    stops: list[AttemptResult | asyncio.CancelledError | Exception] = []

    class NoLaunchEffects(FakeEffects):
        @override
        async def acquire(
            self, request: AttemptRequest, /
        ) -> ProcessHandle | NotLaunched:
            return NotLaunched("PermissionError", "launch refused")

    events: list[WireEvent] = []
    clock = FakeClock(events)
    effects = NoLaunchEffects(events, clock)

    async def attempt(request: AttemptRequest, /) -> AttemptResult:
        return await run_attempt(request, effects, clock)

    # When
    outcome = asyncio.run(call_supervisor(attempt_request, attempt, stops.append))

    # Then
    assert isinstance(outcome, InfrastructureFailure)
    assert outcome.error_type == "PermissionError"
    assert outcome.diagnostic == "launch refused"
    assert outcome.observation.cleanup.confirmed
    assert stops == []
    assert not any(isinstance(event, CleanupCall) for event in events)


def test_unexpected_acquisition_error_stops_dispatch_and_remains_an_error(
    attempt_request: AttemptRequest,
) -> None:
    # Given
    error = NotImplementedError("acquisition implementation pending")
    stops: list[AttemptResult | asyncio.CancelledError | Exception] = []

    class FailingAcquisitionEffects(FakeEffects):
        @override
        async def acquire(
            self, request: AttemptRequest, /
        ) -> ProcessHandle | NotLaunched:
            raise error

    events: list[WireEvent] = []
    clock = FakeClock(events)
    effects = FailingAcquisitionEffects(events, clock)

    async def attempt(request: AttemptRequest, /) -> AttemptResult:
        return await run_attempt(request, effects, clock)

    # When
    with pytest.raises(NotImplementedError) as raised:
        asyncio.run(call_supervisor(attempt_request, attempt, stops.append))

    # Then
    assert raised.value is error
    assert stops == [error]
    assert not any(isinstance(event, CleanupCall) for event in events)


def test_post_kill_exit_status_fills_incomplete_result_without_changing_variant(
    attempt_request: AttemptRequest,
) -> None:
    # Given
    events: list[WireEvent] = []
    clock = FakeClock(events)
    leaf_result = TimedOut(
        AttemptObservation(CapturedOutput(b"partial", b""), 2.0, PENDING_CLEANUP),
        None,
    )
    effects = PostKillStatusEffects(events, clock, leaf_result)

    # When
    result = asyncio.run(run_attempt(attempt_request, effects, clock))

    # Then
    assert isinstance(result, TimedOut)
    assert result.exit_status == 137
    assert result.observation.cleanup.confirmed


def test_cleanup_cancellation_preserves_completed_exit_status(
    attempt_request: AttemptRequest,
) -> None:
    # Given
    events: list[WireEvent] = []
    clock = FakeClock(events)
    effects = CompletedCleanupEffects(events, clock)

    async def cancel_during_cleanup() -> AttemptCancelled:
        task = asyncio.create_task(run_attempt(attempt_request, effects, clock))
        await effects.cleanup_started.wait()
        task.cancel()
        effects.cleanup_release.set()
        with pytest.raises(AttemptCancelled) as raised:
            await task
        return raised.value

    # When
    cancellation = asyncio.run(cancel_during_cleanup())

    # Then
    assert cancellation.observation.output == CapturedOutput(b"done", b"")
    assert cancellation.exit_status == 7
    assert cancellation.observation.cleanup.confirmed


def test_cleanup_programmer_error_preserves_completed_exit_status(
    attempt_request: AttemptRequest,
) -> None:
    # Given
    events: list[WireEvent] = []
    clock = FakeClock(events)
    error = RuntimeError("cleanup implementation bug")
    effects = CompletedCleanupEffects(events, clock, cleanup_error=error)
    effects.cleanup_release.set()

    # When
    with pytest.raises(RuntimeError) as raised:
        asyncio.run(run_attempt(attempt_request, effects, clock))

    # Then
    assert raised.value is error
    evidence = failure_evidence(raised.value)
    assert evidence is not None
    assert evidence.exit_status == 7
    assert evidence.observation.cleanup.wait_diagnostic == (
        "RuntimeError: cleanup implementation bug"
    )


def test_public_composition_stops_on_normalized_cleanup_failure(
    attempt_request: AttemptRequest,
) -> None:
    # Given
    events: list[WireEvent] = []
    clock = FakeClock(events)
    effects = NonconfirmedCleanupEffects(events, clock)
    stops: list[AttemptResult | asyncio.CancelledError | Exception] = []

    async def attempt(request: AttemptRequest, /) -> AttemptResult:
        return await run_attempt(request, effects, clock)

    # When
    result = asyncio.run(call_supervisor(attempt_request, attempt, stops.append))

    # Then
    assert isinstance(result, Completed)
    assert result.observation.cleanup.signal == "failed"
    assert result.observation.cleanup.direct_wait == "expired"
    assert stops == [result]


def test_unexpected_capture_error_stops_caller_with_evidence_and_original_cause(
    attempt_request: AttemptRequest,
) -> None:
    # Given
    events: list[WireEvent] = []
    clock = FakeClock(events)
    effects = FailingCaptureEffects(events, clock, ValueError)
    stops: list[AttemptResult | asyncio.CancelledError | Exception] = []

    async def attempt(request: AttemptRequest, /) -> AttemptResult:
        return await run_attempt(request, effects, clock)

    # When
    with pytest.raises(ValueError) as raised:
        asyncio.run(call_supervisor(attempt_request, attempt, stops.append))

    # Then
    assert raised.value is effects.error
    evidence = failure_evidence(raised.value)
    assert isinstance(evidence, AttemptFailureEvidence)
    assert evidence.observation.cleanup.confirmed
    assert stops == [raised.value]


def test_cleanup_programmer_error_does_not_replace_capture_error(
    attempt_request: AttemptRequest,
) -> None:
    # Given
    events: list[WireEvent] = []
    clock = FakeClock(events)
    effects = CleanupCrashesEffects(events, clock, ValueError)

    # When
    with pytest.raises(ValueError, match="capture failed") as raised:
        asyncio.run(run_attempt(attempt_request, effects, clock))

    # Then
    assert raised.value is effects.error
    evidence = failure_evidence(raised.value)
    assert isinstance(evidence, AttemptFailureEvidence)
    assert evidence.observation.cleanup.signal == "unknown"
    assert evidence.observation.cleanup.wait_diagnostic == (
        "RuntimeError: cleanup implementation bug"
    )


def test_cleanup_cancellation_retains_original_capture_error_as_cause(
    attempt_request: AttemptRequest,
) -> None:
    # Given
    events: list[WireEvent] = []
    clock = FakeClock(events)
    effects = WaitingCleanupAfterCaptureFailure(events, clock)

    async def cancel_during_cleanup() -> AttemptCancelled:
        task = asyncio.create_task(run_attempt(attempt_request, effects, clock))
        await effects.cleanup_started.wait()
        task.cancel()
        effects.cleanup_release.set()
        with pytest.raises(AttemptCancelled) as raised:
            await task
        return raised.value

    # When
    cancellation = asyncio.run(cancel_during_cleanup())

    # Then
    assert cancellation.__cause__ is effects.error
    assert cancellation.observation.cleanup.confirmed
    assert any(
        "Capture also failed: ValueError: capture failed" in note
        for note in cancellation.__notes__
    )


def test_cleanup_programmer_error_after_capture_keeps_error_and_evidence(
    attempt_request: AttemptRequest,
) -> None:
    # Given
    events: list[WireEvent] = []
    clock = FakeClock(events)
    effects = SuccessfulCaptureCleanupCrashesEffects(events, clock)

    # When
    with pytest.raises(RuntimeError, match="cleanup implementation bug") as raised:
        asyncio.run(run_attempt(attempt_request, effects, clock))

    # Then
    evidence = failure_evidence(raised.value)
    assert evidence is not None
    assert evidence.observation.cleanup.signal == "unknown"
    assert evidence.observation.cleanup.wait_diagnostic == (
        "RuntimeError: cleanup implementation bug"
    )


@pytest.mark.parametrize(
    "leaf_result",
    [
        pytest.param(
            TimedOut(
                AttemptObservation(
                    CapturedOutput(b"timed out", b""), 3.0, PENDING_CLEANUP
                ),
                0,
            ),
            id="timeout-variant",
        ),
        pytest.param(
            OutputLimitExceeded(
                AttemptObservation(
                    CapturedOutput(b"prefix", b"overflow"), 2.0, PENDING_CLEANUP
                ),
                None,
            ),
            id="output-limit-variant",
        ),
        pytest.param(
            InfrastructureFailure(
                AttemptObservation(
                    CapturedOutput(b"partial", b"error"), 1.0, PENDING_CLEANUP
                ),
                None,
                "OSError",
                "leaf diagnostic",
            ),
            id="infrastructure-variant",
        ),
    ],
)
def test_composition_preserves_noncompleted_leaf_result_variants(
    attempt_request: AttemptRequest,
    leaf_result: AttemptResult,
) -> None:
    # Given
    events: list[WireEvent] = []
    clock = FakeClock(events)
    effects = OutcomeEffects(events, clock, leaf_result)

    # When
    result = asyncio.run(run_attempt(attempt_request, effects, clock))

    # Then
    expected_observation = AttemptObservation(
        leaf_result.observation.output, 3.5, FINAL_CLEANUP
    )
    assert result == replace(leaf_result, observation=expected_observation)
    assert type(result) is type(leaf_result)


@pytest.mark.parametrize(
    ("cleanup", "should_stop"),
    [
        pytest.param(
            CleanupEvidence("owned", "sent", None, "reaped", None),
            False,
            id="owned-signal-and-reap-confirmed",
        ),
        pytest.param(
            CleanupEvidence("owned", "no_target", None, "reaped", None),
            False,
            id="owned-no-target-and-reap-confirmed",
        ),
        pytest.param(
            CleanupEvidence("not_started", "not_started", None, "not_started", None),
            False,
            id="safe-no-launch",
        ),
        pytest.param(
            CleanupEvidence("acquisition_uncertain", "unknown", None, "unknown", None),
            True,
            id="acquisition-uncertain",
        ),
        pytest.param(
            CleanupEvidence("acquisition_uncertain", "sent", None, "reaped", None),
            True,
            id="uncertain-process-despite-success-shaped-cleanup",
        ),
        pytest.param(
            CleanupEvidence("owned", "failed", "denied", "reaped", None),
            True,
            id="signal-failed",
        ),
        pytest.param(
            CleanupEvidence("owned", "sent", None, "expired", "deadline"),
            True,
            id="wait-expired",
        ),
        pytest.param(
            CleanupEvidence("owned", "unknown", None, "unknown", None),
            True,
            id="unknown-cleanup",
        ),
    ],
)
def test_caller_gate_allows_only_safe_no_launch_or_owned_cleanup(
    attempt_request: AttemptRequest,
    cleanup: CleanupEvidence,
    should_stop: bool,
) -> None:
    # Given
    result = InfrastructureFailure(
        AttemptObservation(
            CapturedOutput(b"partial", b"failure"),
            1.5,
            cleanup,
        ),
        7,
        "PermissionError",
        "permission denied",
    )
    stops: list[AttemptResult | asyncio.CancelledError | Exception] = []

    async def attempt(actual_request: AttemptRequest, /) -> InfrastructureFailure:
        assert actual_request is attempt_request
        await asyncio.sleep(0)
        return result

    # When
    returned = asyncio.run(call_supervisor(attempt_request, attempt, stops.append))

    # Then
    assert returned is result
    assert tuple(stops) == ((result,) if should_stop else ())


def test_caller_records_cancellation_then_propagates_it(
    attempt_request: AttemptRequest,
) -> None:
    # Given
    cancellation = AttemptCancelled(
        AttemptObservation(
            CapturedOutput(b"partial", b""),
            None,
            CleanupEvidence("owned", "sent", None, "reaped", None),
        )
    )
    stops: list[AttemptResult | asyncio.CancelledError | Exception] = []

    async def attempt(actual_request: AttemptRequest, /) -> Completed:
        assert actual_request is attempt_request
        await asyncio.sleep(0)
        raise cancellation

    # When
    with pytest.raises(AttemptCancelled) as raised:
        asyncio.run(call_supervisor(attempt_request, attempt, stops.append))

    # Then
    assert raised.value is cancellation
    assert stops == [cancellation]
    assert raised.value.observation.output.stdout == b"partial"
