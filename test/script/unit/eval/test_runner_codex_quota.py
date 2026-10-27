# SPDX-License-Identifier: Apache-2.0
"""Codex quota adapter source wiring and pending operation leaves."""

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import override

import pytest

from script.eval.model import (
    AttemptEvidence,
    QuotaAllowanceId,
    QuotaObservation,
    QuotaProbeEvidence,
    QuotaProbeId,
    QuotaProbeRequest,
    QuotaProbeSchedule,
    QuotaProviderId,
    QuotaScope,
    QuotaState,
)
from script.eval.runner import quota_probe_evidence
from script.eval.runner.adapters import (
    CodexQuotaSettings,
    CodexQuotaStatusReader,
    RawCodexQuotaStatusSource,
    RawCodexSessionSnapshot,
)
from script.eval.runner.ports import AttemptCall
from script.process_supervisor import (
    AttemptCancelled,
    AttemptFailureEvidence,
    AttemptObservation,
    AttemptRequest,
    AttemptResult,
    CapturedOutput,
    CleanupEvidence,
    Completed,
    DispatchStop,
)


class RecordingSource(RawCodexQuotaStatusSource):
    """Return a single configured snapshot and retain the lookup coordinate."""

    def __init__(self, snapshot: RawCodexSessionSnapshot | None) -> None:
        self.snapshot = snapshot
        self.thread_ids: list[str] = []
        self.events: list[str] = []

    async def read_session_for_thread(
        self, thread_id: str, /
    ) -> RawCodexSessionSnapshot | None:
        self.thread_ids.append(thread_id)
        self.events.append("lookup")
        return self.snapshot


class FixedRuntime:
    """Provide one deterministic read timestamp."""

    def utc_now(self) -> str:
        return "2026-10-27T10:00:00Z"

    def monotonic(self) -> float:
        return 1.0

    async def sleep(self, seconds: float, /) -> None:
        raise AssertionError("quota adapter does not schedule waits")

    def uniform(self, lower: float, upper: float, /) -> float:
        raise AssertionError("quota adapter does not schedule jitter")


def make_attempt_evidence(usage_telemetry: bytes | None) -> AttemptEvidence:
    """Build a settled invocation whose raw telemetry is deliberately opaque."""
    request = AttemptRequest(
        argv=("/opt/codex", "exec"),
        cwd=Path("/repo"),
        timeout_seconds=2.0,
        cleanup_timeout_seconds=1.0,
        output_limit_bytes=256,
        stdin="devnull",
    )
    return AttemptEvidence(
        control_flow="returned",
        outcome=None,
        error_type=None,
        diagnostic=None,
        request=request,
        started_at_utc="2026-10-27T09:59:59Z",
        ended_at_utc="2026-10-27T10:00:00Z",
        usage_telemetry=usage_telemetry,
    )


async def unused_attempt_call(
    request: AttemptRequest, stop_dispatch: DispatchStop, /
) -> AttemptResult:
    """Fail if passive observation accidentally invokes a probe."""
    await asyncio.sleep(0)
    del request, stop_dispatch
    raise AssertionError("passive observation must not invoke a probe")


def make_reader(
    source: RecordingSource,
    scope: QuotaScope | None,
    extract_thread_id: Callable[[bytes | None], str | None] | None,
    normalize_session: Callable[
        [RawCodexSessionSnapshot | None, QuotaScope | None, str], QuotaObservation
    ]
    | None,
    attempt_call: AttemptCall | None = None,
    build_probe_request: Callable[
        [QuotaProbeRequest, CodexQuotaSettings], AttemptRequest
    ]
    | None = None,
    assess_probe: Callable[
        [AttemptEvidence, QuotaObservation | None], tuple[QuotaState, str | None]
    ]
    | None = None,
) -> CodexQuotaStatusReader:
    """Compose reader ports with deterministic test collaborators."""
    reader = CodexQuotaStatusReader(
        source=source,
        quota_scope=scope,
        settings=CodexQuotaSettings(
            executable_path=Path("/opt/codex"),
            empty_read_only_cwd=Path("/tmp/empty"),
            timeout_seconds=10.0,
            cleanup_timeout_seconds=2.0,
            output_limit_bytes=1024,
            grace_seconds=0.0,
        ),
        attempt_call=(unused_attempt_call if attempt_call is None else attempt_call),
        runtime=FixedRuntime(),
        extract_thread_id=extract_thread_id,
        normalize_session=normalize_session,
        build_probe_request=build_probe_request,
        assess_probe=assess_probe,
    )
    return reader


def make_scope() -> QuotaScope:
    """Build an opaque provider and allowance pair for forwarding checks."""
    return QuotaScope(
        provider_id=QuotaProviderId("codex-test"),
        allowance_id=QuotaAllowanceId("scope-1"),
    )


def make_probe_request(probe_id: str = "probe-1") -> QuotaProbeRequest:
    """Build a retained quota request with a distinct identity."""
    return QuotaProbeRequest(
        schedule=QuotaProbeSchedule(
            run_id="run-1",
            probe_id=QuotaProbeId(probe_id),
            scope=make_scope(),
            reason="periodic",
            created_at_utc="2026-10-27T10:00:00Z",
            due_at_utc="2026-10-27T10:00:00Z",
            interval_seconds=1.0,
            reset_hint_at_utc=None,
        ),
        pause_wait_id=None,
        poll_started_at_utc="2026-10-27T10:00:00Z",
        scheduled_wait_seconds=0.0,
        scheduled_wait_elapsed_basis="monotonic",
    )


def make_process_result(stdout: bytes, stderr: bytes) -> Completed:
    """Build a returned supervisor observation with both captured streams."""
    return Completed(
        observation=AttemptObservation(
            output=CapturedOutput(stdout=stdout, stderr=stderr),
            elapsed_seconds=0.25,
            cleanup=CleanupEvidence("owned", (), "reaped", None),
        ),
        exit_status=0,
    )


def make_probe_attempt_request() -> AttemptRequest:
    """Build the request a verified probe recipe would supply to the port."""
    return AttemptRequest(
        argv=("/opt/codex", "exec", "--json"),
        cwd=Path("/tmp/empty"),
        timeout_seconds=10.0,
        cleanup_timeout_seconds=2.0,
        output_limit_bytes=1024,
        stdin="devnull",
    )


def stop_dispatch(outcome: AttemptResult | BaseException, /) -> None:
    """Accept the exact cleanup report without changing test state."""
    del outcome


class RecordingAttemptCall:
    """Return one process result and retain exact call arguments."""

    def __init__(self, result: AttemptResult, /) -> None:
        self.result = result
        self.calls: list[tuple[AttemptRequest, DispatchStop]] = []

    async def __call__(
        self, request: AttemptRequest, stop: DispatchStop, /
    ) -> AttemptResult:
        await asyncio.sleep(0)
        self.calls.append((request, stop))
        return self.result


class RecordingProbeRecipe:
    """Return one request and retain the exact quota request and settings."""

    def __init__(self, request: AttemptRequest, /) -> None:
        self.request = request
        self.inputs: list[tuple[QuotaProbeRequest, CodexQuotaSettings]] = []

    def __call__(
        self, request: QuotaProbeRequest, settings: CodexQuotaSettings, /
    ) -> AttemptRequest:
        self.inputs.append((request, settings))
        return self.request


class RecordingThreadExtractor:
    """Return one opaque thread identifier for the exact captured bytes."""

    def __init__(self, telemetry: bytes, /) -> None:
        self.telemetry = telemetry
        self.thread_ids: list[str] = []

    def __call__(self, raw: bytes | None, /) -> str:
        assert raw is self.telemetry
        thread_id = "opaque-probe-thread"
        self.thread_ids.append(thread_id)
        return thread_id


class RecordingNormalizer:
    """Return one generic observation after verifying scope and read time."""

    def __init__(
        self,
        snapshot: RawCodexSessionSnapshot,
        scope: QuotaScope,
        observation: QuotaObservation,
        /,
    ) -> None:
        self.snapshot = snapshot
        self.scope = scope
        self.observation = observation
        self.calls: list[RawCodexSessionSnapshot | None] = []

    def __call__(
        self,
        snapshot: RawCodexSessionSnapshot | None,
        scope: QuotaScope | None,
        read_at_utc: str,
        /,
    ) -> QuotaObservation:
        assert snapshot is self.snapshot
        assert scope is self.scope
        assert read_at_utc == "2026-10-27T10:00:00Z"
        self.calls.append(snapshot)
        return self.observation


class RecordingAssessment:
    """Return an explicitly unknown controlled assessment."""

    def __init__(self) -> None:
        self.calls: list[tuple[AttemptEvidence, QuotaObservation | None]] = []

    def __call__(
        self, attempt: AttemptEvidence, observation: QuotaObservation | None, /
    ) -> tuple[QuotaState, str | None]:
        self.calls.append((attempt, observation))
        return "unknown", "controlled assessment only"


def assert_poll_wiring(
    result: QuotaProbeEvidence,
    quota_request: QuotaProbeRequest,
    attempt_request: AttemptRequest,
    process_result: AttemptResult,
    stdout: bytes,
    source: RecordingSource,
    attempt_call: RecordingAttemptCall,
    recipe: RecordingProbeRecipe,
    extractor: RecordingThreadExtractor,
    normalizer: RecordingNormalizer,
    assessment: RecordingAssessment,
    reader: CodexQuotaStatusReader,
    stop: DispatchStop,
) -> None:
    """Check exact request forwarding and generic process association."""
    assert recipe.inputs == [(quota_request, reader.settings)]
    assert recipe.inputs[0][0] is quota_request
    assert recipe.inputs[0][1] is reader.settings
    assert attempt_call.calls == [(attempt_request, stop)]
    assert attempt_call.calls[0][0] is attempt_request
    assert attempt_call.calls[0][1] is stop
    assert source.thread_ids == ["opaque-probe-thread"]
    assert extractor.thread_ids == ["opaque-probe-thread"]
    assert normalizer.calls == [source.snapshot]
    assert len(assessment.calls) == 1
    assert assessment.calls[0][0].request is attempt_request
    assert assessment.calls[0][0].outcome is process_result
    assert assessment.calls[0][0].usage_telemetry is stdout
    assert assessment.calls[0][1] is normalizer.observation
    assert result.request is quota_request
    assert result.process is assessment.calls[0][0]
    assert result.quota_state == "unknown"
    assert result.observation is normalizer.observation
    assert not hasattr(result.process, "attempt_number")


async def test_passive_observation_forwards_exact_thread_and_raw_bytes() -> None:
    # Given
    content = b"opaque session bytes"
    snapshot = RawCodexSessionSnapshot(content, "source-opaque-7")
    source = RecordingSource(snapshot)
    scope = make_scope()
    telemetry = b"opaque invocation telemetry"
    normalized_inputs: list[
        tuple[RawCodexSessionSnapshot | None, QuotaScope | None, str]
    ] = []

    def normalize_session(
        received: RawCodexSessionSnapshot | None,
        received_scope: QuotaScope | None,
        read_at_utc: str,
    ) -> QuotaObservation:
        source.events.append("normalize")
        normalized_inputs.append((received, received_scope, read_at_utc))
        return QuotaObservation(
            scope=received_scope,
            read_at_utc=read_at_utc,
            source_coordinate=received.source_coordinate if received else None,
            windows=(),
            diagnostic="test normalization only",
        )

    reader = make_reader(
        source,
        scope,
        lambda raw: "thread-opaque-1" if raw is telemetry else None,
        normalize_session,
    )

    # When
    observation = await reader.observe_settled_attempt(make_attempt_evidence(telemetry))

    # Then
    assert source.thread_ids == ["thread-opaque-1"]
    assert source.events == ["lookup", "normalize"]
    assert normalized_inputs == [(snapshot, scope, "2026-10-27T10:00:00Z")]
    assert normalized_inputs[0][0] is snapshot
    assert normalized_inputs[0][0].content is content
    assert observation.scope is scope
    assert observation.source_coordinate == "source-opaque-7"
    assert observation.read_at_utc == "2026-10-27T10:00:00Z"


async def test_passive_observation_skips_lookup_without_correlated_thread() -> None:
    # Given
    source = RecordingSource(RawCodexSessionSnapshot(b"opaque", "source-1"))
    scope = make_scope()
    normalized_inputs: list[RawCodexSessionSnapshot | None] = []

    def normalize_session(
        snapshot: RawCodexSessionSnapshot | None,
        received_scope: QuotaScope | None,
        read_at_utc: str,
    ) -> QuotaObservation:
        normalized_inputs.append(snapshot)
        return QuotaObservation(
            scope=received_scope,
            read_at_utc=read_at_utc,
            source_coordinate=None,
            windows=(),
            diagnostic="test normalization only",
        )

    reader = make_reader(source, scope, lambda raw: None, normalize_session)

    # When
    observation = await reader.observe_settled_attempt(make_attempt_evidence(None))

    # Then
    assert source.thread_ids == []
    assert normalized_inputs == [None]
    assert observation.scope is scope


async def test_passive_lookup_preserves_source_exception() -> None:
    # Given
    source_error = OSError("session read failed")

    class FailingSource(RecordingSource):
        @override
        async def read_session_for_thread(
            self, thread_id: str, /
        ) -> RawCodexSessionSnapshot | None:
            self.thread_ids.append(thread_id)
            raise source_error

    source = FailingSource(None)
    reader = make_reader(
        source,
        make_scope(),
        lambda raw: "thread-opaque-2",
        lambda snapshot, scope, read_at: pytest.fail(
            "normalization must not follow a failed source lookup"
        ),
    )

    # When
    with pytest.raises(OSError, match="session read failed") as raised:
        await reader.observe_settled_attempt(make_attempt_evidence(b"telemetry"))

    # Then
    assert raised.value is source_error
    assert source.thread_ids == ["thread-opaque-2"]


async def test_default_thread_extraction_leaf_remains_visible() -> None:
    # Given
    source = RecordingSource(None)
    reader = make_reader(source, None, None, None)

    # When
    with pytest.raises(NotImplementedError, match="thread telemetry extraction"):
        await reader.observe_settled_attempt(make_attempt_evidence(b"unverified"))

    # Then
    assert source.thread_ids == []


async def test_default_probe_leaf_remains_visible() -> None:
    # Given
    def normalize_pending_leaf(
        snapshot: RawCodexSessionSnapshot | None,
        scope: QuotaScope | None,
        read_at_utc: str,
    ) -> QuotaObservation:
        raise AssertionError("the pending normalizer is not part of poll")

    source = RecordingSource(None)
    reader = make_reader(source, None, lambda raw: None, normalize_pending_leaf)
    request = make_probe_request()

    # When
    with pytest.raises(NotImplementedError, match="probe CLI recipe"):
        await reader.poll(request, lambda outcome: None)

    # Then
    assert source.thread_ids == []


async def test_poll_forwards_one_exact_request_and_stop_callback() -> None:
    # Given
    quota_request = make_probe_request()
    attempt_request = make_probe_attempt_request()
    stdout = b"opaque probe stdout"
    process_result = make_process_result(stdout, b"raw probe stderr")
    snapshot = RawCodexSessionSnapshot(b"opaque", "source-probe")
    source = RecordingSource(snapshot)
    observation = QuotaObservation(
        scope=quota_request.schedule.scope,
        read_at_utc="2026-10-27T10:00:00Z",
        source_coordinate="source-probe",
        windows=(),
        diagnostic="controlled normalization result",
    )
    attempt_call = RecordingAttemptCall(process_result)
    recipe = RecordingProbeRecipe(attempt_request)
    extractor = RecordingThreadExtractor(stdout)
    normalizer = RecordingNormalizer(
        snapshot, quota_request.schedule.scope, observation
    )
    assessment = RecordingAssessment()
    reader = make_reader(
        source,
        quota_request.schedule.scope,
        extractor,
        normalizer,
        attempt_call,
        recipe,
        assessment,
    )

    # When
    result = await reader.poll(quota_request, stop_dispatch)

    # Then
    assert_poll_wiring(
        result,
        quota_request,
        attempt_request,
        process_result,
        stdout,
        source,
        attempt_call,
        recipe,
        extractor,
        normalizer,
        assessment,
        reader,
        stop_dispatch,
    )


async def test_poll_preserves_cancellation_and_supervisor_observation() -> None:
    # Given
    quota_request = make_probe_request()
    attempt_request = make_probe_attempt_request()
    stdout = b"partial probe stdout"
    stderr = b"partial probe stderr"
    cancellation = asyncio.CancelledError("process attempt cancelled")
    supervisor_evidence = AttemptFailureEvidence(
        observation=AttemptObservation(
            output=CapturedOutput(stdout, stderr),
            elapsed_seconds=0.5,
            cleanup=CleanupEvidence("owned", (), "expired", None),
        ),
        exit_status=130,
    )
    vars(cancellation)["process_supervisor_evidence"] = supervisor_evidence

    async def attempt_call(
        request: AttemptRequest, stop_dispatch: DispatchStop, /
    ) -> AttemptResult:
        await asyncio.sleep(0)
        assert request is attempt_request
        raise cancellation

    reader = make_reader(
        RecordingSource(None),
        quota_request.schedule.scope,
        lambda raw: None,
        None,
        attempt_call,
        lambda request, settings: attempt_request,
    )

    # When
    with pytest.raises(asyncio.CancelledError) as raised:
        await reader.poll(quota_request, lambda outcome: None)

    # Then
    assert raised.value is cancellation
    evidence = quota_probe_evidence(raised.value, quota_request)
    assert evidence is not None
    assert evidence.process.request is attempt_request
    assert evidence.process.control_flow == "cancelled"
    assert evidence.process.outcome is supervisor_evidence
    assert evidence.process.usage_telemetry is stdout
    assert evidence.quota_state == "unknown"
    assert evidence.observation is None


async def test_poll_preserves_supervisor_cancellation_object_and_facts() -> None:
    # Given
    quota_request = make_probe_request()
    attempt_request = make_probe_attempt_request()
    cancellation = AttemptCancelled(
        AttemptObservation(
            output=CapturedOutput(b"", b""),
            elapsed_seconds=0.0,
            cleanup=CleanupEvidence("not_started", (), "not_started", None),
        )
    )

    async def attempt_call(
        request: AttemptRequest, stop: DispatchStop, /
    ) -> AttemptResult:
        await asyncio.sleep(0)
        assert request is attempt_request
        raise cancellation

    reader = make_reader(
        RecordingSource(None),
        quota_request.schedule.scope,
        lambda raw: None,
        None,
        attempt_call,
        lambda request, settings: attempt_request,
    )

    # When
    with pytest.raises(AttemptCancelled) as raised:
        await reader.poll(quota_request, stop_dispatch)

    # Then
    assert raised.value is cancellation
    evidence = quota_probe_evidence(cancellation, quota_request)
    assert evidence is not None
    assert evidence.process.outcome is cancellation
    assert evidence.process.control_flow == "cancelled"
    assert evidence.process.usage_telemetry == b""


async def test_poll_preserves_attached_unexpected_supervisor_failure() -> None:
    # Given
    quota_request = make_probe_request()
    attempt_request = make_probe_attempt_request()
    stdout = b"captured before unexpected failure"
    failure = RuntimeError("supervisor caller failed")
    supervisor_evidence = AttemptFailureEvidence(
        observation=AttemptObservation(
            output=CapturedOutput(stdout, b"stderr"),
            elapsed_seconds=0.75,
            cleanup=CleanupEvidence("owned", (), "reaped", None),
        ),
        exit_status=41,
    )
    vars(failure)["process_supervisor_evidence"] = supervisor_evidence

    async def attempt_call(
        request: AttemptRequest, stop_dispatch: DispatchStop, /
    ) -> AttemptResult:
        await asyncio.sleep(0)
        assert request is attempt_request
        raise failure

    reader = make_reader(
        RecordingSource(None),
        quota_request.schedule.scope,
        lambda raw: None,
        None,
        attempt_call,
        lambda request, settings: attempt_request,
    )

    # When
    with pytest.raises(RuntimeError, match="supervisor caller failed") as raised:
        await reader.poll(quota_request, lambda outcome: None)

    # Then
    assert raised.value is failure
    evidence = quota_probe_evidence(raised.value, quota_request)
    assert evidence is not None
    assert evidence.process.outcome is supervisor_evidence
    assert evidence.process.usage_telemetry is stdout
    assert evidence.process.request is attempt_request


async def test_postprocessing_error_keeps_returned_process_and_request_facts() -> None:
    # Given
    quota_request = make_probe_request()
    attempt_request = make_probe_attempt_request()
    process_result = make_process_result(b"actual stdout", b"actual stderr")
    postprocessing_error = ValueError("source normalization failed")

    async def attempt_call(
        request: AttemptRequest, stop_dispatch: DispatchStop, /
    ) -> AttemptResult:
        await asyncio.sleep(0)
        assert request is attempt_request
        return process_result

    def fail_normalization(
        snapshot: RawCodexSessionSnapshot | None,
        scope: QuotaScope | None,
        read_at_utc: str,
    ) -> QuotaObservation:
        raise postprocessing_error

    reader = make_reader(
        RecordingSource(None),
        quota_request.schedule.scope,
        lambda raw: "thread-for-failing-source",
        fail_normalization,
        attempt_call,
        lambda request, settings: attempt_request,
    )

    # When
    with pytest.raises(ValueError, match="source normalization failed") as raised:
        await reader.poll(quota_request, lambda outcome: None)

    # Then
    assert raised.value is postprocessing_error
    evidence = quota_probe_evidence(raised.value, quota_request)
    assert evidence is not None
    assert evidence.request is quota_request
    assert evidence.process.request is attempt_request
    assert evidence.process.control_flow == "returned"
    assert evidence.process.outcome is process_result
    assert (
        evidence.process.started_at_utc,
        evidence.process.ended_at_utc,
    ) == ("2026-10-27T10:00:00Z", "2026-10-27T10:00:00Z")
    assert evidence.process.usage_telemetry == b"actual stdout"
    assert process_result.observation.output is not None
    assert process_result.observation.output.stderr == b"actual stderr"
    assert evidence.quota_state == "unknown"
    assert evidence.observation is None


async def test_reused_exception_evidence_is_request_specific() -> None:
    # Given
    first_request = make_probe_request("probe-1")
    second_request = make_probe_request("probe-2")
    attempt_request = make_probe_attempt_request()
    shared_error = RuntimeError("shared source failure")

    async def attempt_call(
        request: AttemptRequest, stop_dispatch: DispatchStop, /
    ) -> AttemptResult:
        await asyncio.sleep(0)
        assert request is attempt_request
        raise shared_error

    reader = make_reader(
        RecordingSource(None),
        first_request.schedule.scope,
        lambda raw: None,
        None,
        attempt_call,
        lambda request, settings: attempt_request,
    )

    # When
    with pytest.raises(RuntimeError):
        await reader.poll(first_request, lambda outcome: None)
    with pytest.raises(RuntimeError) as second_raised:
        await reader.poll(second_request, lambda outcome: None)
    with pytest.raises(RuntimeError) as repeated_raised:
        await reader.poll(first_request, lambda outcome: None)

    # Then
    assert second_raised.value is shared_error
    assert repeated_raised.value is shared_error
    first_evidence = quota_probe_evidence(shared_error, first_request)
    second_evidence = quota_probe_evidence(shared_error, second_request)
    assert first_evidence is not None
    assert second_evidence is not None
    assert first_evidence.request is first_request
    assert second_evidence.request is second_request
    assert quota_probe_evidence(shared_error, make_probe_request("probe-1")) is None
    assert quota_probe_evidence(shared_error, first_request) is first_evidence
