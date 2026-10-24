# SPDX-License-Identifier: Apache-2.0
"""Wiring tests for the experimental process-supervisor increment."""

import asyncio
from dataclasses import dataclass, replace
from pathlib import Path
from typing import override

import pytest

from script.process_supervisor import (
    AttemptCancelled,
    AttemptObservation,
    AttemptRequest,
    AttemptResult,
    CapturedOutput,
    CleanupEvidence,
    Completed,
    InfrastructureFailure,
    NativeProcessEffects,
    OutputLimitExceeded,
    ProcessHandle,
    TimedOut,
    call_supervisor,
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

    async def acquire(self, request: AttemptRequest, /) -> ProcessHandle:
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
    ) -> CleanupEvidence:
        self.events.append(CleanupCall(handle, timeout_seconds))
        self.clock.value = 13.5
        return CleanupEvidence("owned", "sent", None, "reaped", None)


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
    stops: list[AttemptResult | asyncio.CancelledError] = []

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
    stops: list[AttemptResult | asyncio.CancelledError] = []

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
