# SPDX-License-Identifier: Apache-2.0
"""Codex quota source, normalization, polling, and lifecycle behavior."""

import asyncio
from collections.abc import Callable
import json
from pathlib import Path
from threading import Event
import tomllib
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
    LocalCodexQuotaStatusSource,
    RawCodexQuotaStatusSource,
    RawCodexSessionSnapshot,
    codex_quota_scope_from_identity,
)
from script.eval.runner.ports import AttemptCall
import script.eval.runner.quota_evidence as quota_evidence_module
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
    OutputLimitExceeded,
    SignalAttempt,
    TimedOut,
    call_supervisor,
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


class SequenceRuntime(FixedRuntime):
    """Return ordered timestamps for one probe, end, and source read."""

    def __init__(self, timestamps: tuple[str, ...]) -> None:
        self.timestamps = iter(timestamps)

    @override
    def utc_now(self) -> str:
        return next(self.timestamps)


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
        [RawCodexSessionSnapshot | None, QuotaScope | None, str, float],
        QuotaObservation,
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
    *,
    output_limit_bytes: int = 1024,
    probe_instructions_file: Path = Path("/tmp/instructions.txt"),
) -> CodexQuotaStatusReader:
    """Compose reader ports with deterministic test collaborators."""
    reader = CodexQuotaStatusReader(
        source=source,
        quota_scope=scope,
        settings=CodexQuotaSettings(
            executable_path=Path("/opt/codex"),
            empty_read_only_cwd=Path("/tmp/empty"),
            probe_instructions_file=probe_instructions_file,
            timeout_seconds=10.0,
            cleanup_timeout_seconds=2.0,
            output_limit_bytes=output_limit_bytes,
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


def make_identity_scope() -> QuotaScope:
    """Build the opaque scope corresponding to synthetic session metadata."""
    return codex_quota_scope_from_identity(
        "openai", "synthetic-account-id", "synthetic-user-id"
    )


SYNTHETIC_THREAD_ID = "d5fdfd18-8048-4be5-a89e-5a6cbf677a10"


def session_rows(
    thread_id: str = SYNTHETIC_THREAD_ID,
    timestamp: str = "2026-10-27T09:59:59Z",
    primary_used: int | float = 35,
    secondary_used: int | float = 21,
    ordinal: int = 17,
    *,
    metadata_overrides: dict[str, object] | None = None,
    secondary_present: bool = True,
) -> list[dict[str, object]]:
    """Return synthetic CLI 0.164.0 metadata and one quota event."""
    metadata: dict[str, object] = {
        "id": thread_id,
        "session_id": thread_id,
        "model_provider": "openai",
        "cli_version": "0.164.0",
        "creator_account_id": "synthetic-account-id",
        "creator_user_id": "synthetic-user-id",
    }
    if metadata_overrides is not None:
        metadata.update(metadata_overrides)
    limits: dict[str, object] = {
        "limit_id": "codex",
        "primary": {
            "used_percent": primary_used,
            "window_minutes": 300,
            "resets_at": 1793035268,
        },
        "credits": {"has_credits": False, "unlimited": False, "balance": "0"},
        "individual_limit": None,
        "spend_control_reached": None,
        "rate_limit_reached_type": None,
    }
    if secondary_present:
        limits["secondary"] = {
            "used_percent": secondary_used,
            "window_minutes": 10080,
            "resets_at": 1793603901,
        }
    return [
        {"type": "session_meta", "payload": metadata},
        {
            "type": "event_msg",
            "timestamp": timestamp,
            "ordinal": ordinal,
            "payload": {"type": "token_count", "rate_limits": limits},
        },
    ]


def write_rollout(
    sessions_directory: Path,
    thread_id: str,
    rows: list[dict[str, object]],
    /,
) -> Path:
    """Write one synthetic rollout at the observed date-directory depth."""
    directory = sessions_directory / "2026" / "10" / "27"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"rollout-2026-10-27T09-59-59-{thread_id}.jsonl"
    path.write_text(
        "".join(f"{json.dumps(row, separators=(',', ':'))}\n" for row in rows),
        encoding="utf-8",
    )
    return path


def make_local_reader(
    sessions_directory: Path,
    scope: QuotaScope | None,
    *,
    max_age: float = 60.0,
    runtime: FixedRuntime | None = None,
    attempt_call: AttemptCall | None = None,
) -> CodexQuotaStatusReader:
    """Compose the concrete local source through the public reader boundary."""
    return CodexQuotaStatusReader(
        source=LocalCodexQuotaStatusSource(sessions_directory),
        quota_scope=scope,
        settings=CodexQuotaSettings(
            executable_path=Path("/opt/codex"),
            empty_read_only_cwd=Path("/tmp/empty"),
            probe_instructions_file=Path("/tmp/instructions.txt"),
            timeout_seconds=10.0,
            cleanup_timeout_seconds=2.0,
            output_limit_bytes=1024,
            grace_seconds=0.0,
        ),
        attempt_call=unused_attempt_call if attempt_call is None else attempt_call,
        runtime=FixedRuntime() if runtime is None else runtime,
        max_observation_age_seconds=max_age,
    )


def thread_started(thread_id: str = SYNTHETIC_THREAD_ID) -> bytes:
    """Return the synthetic JSONL event used by the public attempt path."""
    return json.dumps({"type": "thread.started", "thread_id": thread_id}).encode()


def make_probe_request(
    probe_id: str = "probe-1", scope: QuotaScope | None = None
) -> QuotaProbeRequest:
    """Build a retained quota request with a distinct identity."""
    return QuotaProbeRequest(
        schedule=QuotaProbeSchedule(
            run_id="run-1",
            probe_id=QuotaProbeId(probe_id),
            scope=make_scope() if scope is None else scope,
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
            cleanup=CleanupEvidence(
                "owned",
                (
                    SignalAttempt("SIGTERM", "sent", None),
                    SignalAttempt("SIGKILL", "sent", None),
                ),
                "reaped",
                None,
            ),
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
        max_age: float,
        /,
    ) -> QuotaObservation:
        assert snapshot is self.snapshot
        assert scope is self.scope
        assert read_at_utc == "2026-10-27T10:00:00Z"
        assert max_age.is_integer() and int(max_age) == 60
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
        tuple[RawCodexSessionSnapshot | None, QuotaScope | None, str, float]
    ] = []

    def normalize_session(
        received: RawCodexSessionSnapshot | None,
        received_scope: QuotaScope | None,
        read_at_utc: str,
        max_age: float,
    ) -> QuotaObservation:
        source.events.append("normalize")
        normalized_inputs.append((received, received_scope, read_at_utc, max_age))
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
    assert normalized_inputs == [(snapshot, scope, "2026-10-27T10:00:00Z", 60.0)]
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
        max_age: float,
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
        lambda snapshot, scope, read_at, max_age: pytest.fail(
            "normalization must not follow a failed source lookup"
        ),
    )

    # When
    with pytest.raises(OSError, match="session read failed") as raised:
        await reader.observe_settled_attempt(make_attempt_evidence(b"telemetry"))

    # Then
    assert raised.value is source_error
    assert source.thread_ids == ["thread-opaque-2"]


async def test_default_thread_extraction_correlates_the_json_event() -> None:
    # Given
    source = RecordingSource(None)
    reader = make_reader(source, None, None, None)

    # When
    observation = await reader.observe_settled_attempt(
        make_attempt_evidence(
            b'{"type":"thread.started","thread_id":"01a1781b-a54f-7763-9f82-74709e5e0fcf"}\n'
        )
    )

    # Then
    assert source.thread_ids == ["01a1781b-a54f-7763-9f82-74709e5e0fcf"]
    assert observation.scope is None


async def test_default_probe_recipe_uses_fixed_supervised_arguments() -> None:
    # Given
    source = RecordingSource(None)
    request = make_probe_request()
    stdout = (
        b'{"type":"thread.started","thread_id":"'
        b'01a1781b-a54f-7763-9f82-74709e5e0fcf"}\n'
    )
    attempt_call = RecordingAttemptCall(make_process_result(stdout, b""))
    reader = make_reader(
        source,
        request.schedule.scope,
        None,
        None,
        attempt_call,
        output_limit_bytes=0,
    )

    # When
    result = await reader.poll(request, stop_dispatch)

    # Then
    assert source.thread_ids == ["01a1781b-a54f-7763-9f82-74709e5e0fcf"]
    assert len(attempt_call.calls) == 1
    assert attempt_call.calls[0][0].argv == (
        "/opt/codex",
        "exec",
        "--json",
        "--color",
        "never",
        "--ignore-user-config",
        "--sandbox",
        "read-only",
        "--skip-git-repo-check",
        "--cd",
        "/tmp/empty",
        "-m",
        "gpt-6-luna",
        "-c",
        'model_reasoning_effort="none"',
        "-c",
        'model_instructions_file="/tmp/instructions.txt"',
        "-c",
        "agents.enabled=false",
        "-c",
        "skills.bundled.enabled=false",
        "-c",
        "memories.use_memories=false",
        "-c",
        'approval_policy="never"',
        "-c",
        'web_search="disabled"',
        "-c",
        "features.request_user_input=false",
        "--disable",
        "plugins",
        "--disable",
        "apps",
        "--disable",
        "shell_tool",
        "--disable",
        "multi_agent",
        "--disable",
        "browser_use",
        "--disable",
        "computer_use",
        "--disable",
        "image_generation",
        "--disable",
        "view_image",
        "--disable",
        "sleep_tool",
        "--disable",
        "code_mode",
        "--disable",
        "skill_search",
        "--",
        "Check the current Codex quota. Reply READY.",
    )
    assert "--ephemeral" not in attempt_call.calls[0][0].argv
    assert attempt_call.calls[0][0].output_limit_bytes == 0
    assert result.quota_state == "unknown"


async def test_poll_refuses_a_request_outside_the_verified_scope() -> None:
    # Given
    attempt_call = RecordingAttemptCall(make_process_result(b"", b""))
    reader = make_reader(RecordingSource(None), make_scope(), None, None, attempt_call)
    request = make_probe_request(scope=make_identity_scope())

    # When
    with pytest.raises(ValueError, match="does not match"):
        await reader.poll(request, stop_dispatch)

    # Then
    assert attempt_call.calls == []


async def test_probe_instructions_path_is_valid_unicode_toml() -> None:
    # Given
    instructions = Path("/tmp/quota-probe-🧭.txt")
    request = make_probe_request()
    attempt_call = RecordingAttemptCall(make_process_result(thread_started(), b""))
    reader = make_reader(
        RecordingSource(None),
        request.schedule.scope,
        None,
        None,
        attempt_call,
        probe_instructions_file=instructions,
    )

    # When
    await reader.poll(request, stop_dispatch)

    # Then
    argv = attempt_call.calls[0][0].argv
    assignments = [
        argv[index + 1] for index, argument in enumerate(argv[:-1]) if argument == "-c"
    ]
    settings = tomllib.loads("\n".join(assignments))
    assert settings["model_instructions_file"] == str(instructions)
    assert settings["web_search"] == "disabled"
    assert settings["approval_policy"] == "never"
    assert settings["features"]["request_user_input"] is False


async def test_local_source_projects_one_rollout_through_public_reader(
    tmp_path: Path,
) -> None:
    # Given
    sessions = tmp_path / "sessions"
    rows = session_rows()
    rows.insert(1, {"type": "response_item", "payload": {"text": "secret sentinel"}})
    rollout = write_rollout(sessions, SYNTHETIC_THREAD_ID, rows)
    reader = make_local_reader(sessions, make_identity_scope())

    # When
    observation = await reader.observe_settled_attempt(
        make_attempt_evidence(thread_started())
    )

    # Then
    assert [window.state for window in observation.windows] == [
        "available",
        "available",
    ]
    assert [window.usage_percent for window in observation.windows] == [35.0, 21.0]
    assert all(window.source_sequence == 17 for window in observation.windows)
    source = LocalCodexQuotaStatusSource(sessions)
    snapshot = await source.read_session_for_thread(SYNTHETIC_THREAD_ID)
    assert snapshot is not None
    assert snapshot.requested_thread_id == SYNTHETIC_THREAD_ID
    assert str(rollout) not in snapshot.source_coordinate
    assert b"secret sentinel" not in snapshot.content
    assert b"synthetic-account-id" in snapshot.content
    assert "synthetic-account-id" not in repr(snapshot)
    assert SYNTHETIC_THREAD_ID not in repr(snapshot)


@pytest.mark.parametrize(
    ("metadata_overrides", "secondary_present", "timestamp", "primary_used"),
    [
        (
            {"id": "2bb35892-bde9-4727-bef3-05cb8ba9a021"},
            True,
            "2026-10-27T09:59:59Z",
            35,
        ),
        (
            {"session_id": "2bb35892-bde9-4727-bef3-05cb8ba9a021"},
            True,
            "2026-10-27T09:59:59Z",
            35,
        ),
        ({"cli_version": "0.165.0"}, True, "2026-10-27T09:59:59Z", 35),
        (
            {"creator_user_id": "different-synthetic-user"},
            True,
            "2026-10-27T09:59:59Z",
            35,
        ),
        ({}, False, "2026-10-27T09:59:59Z", 35),
        ({}, True, "2026-10-27T09:57:00Z", 35),
        ({}, True, "2026-10-27T10:00:01Z", 35),
        ({}, True, "2026-10-27T09:59:59Z", True),
    ],
)
async def test_local_reader_fails_closed_on_untrusted_session_rows(
    tmp_path: Path,
    metadata_overrides: dict[str, object],
    secondary_present: bool,
    timestamp: str,
    primary_used: int | float,
) -> None:
    # Given
    sessions = tmp_path / "sessions"
    rows = session_rows(
        timestamp=timestamp,
        primary_used=primary_used,
        metadata_overrides=metadata_overrides,
        secondary_present=secondary_present,
    )
    write_rollout(sessions, SYNTHETIC_THREAD_ID, rows)
    reader = make_local_reader(sessions, make_identity_scope())

    # When
    observation = await reader.observe_settled_attempt(
        make_attempt_evidence(thread_started())
    )

    # Then
    if metadata_overrides or not secondary_present or isinstance(primary_used, bool):
        assert observation.scope is None
    else:
        assert observation.scope == make_identity_scope()
    assert [window.state for window in observation.windows] == ["unknown", "unknown"]
    if timestamp != "2026-10-27T09:59:59Z":
        assert observation.windows[0].usage_percent == pytest.approx(35.0)
        assert observation.windows[0].source_observed_at_utc == timestamp
        assert observation.windows[0].source_sequence == 17


async def test_local_source_rejects_ambiguous_rollout_candidates(
    tmp_path: Path,
) -> None:
    # Given
    sessions = tmp_path / "sessions"
    write_rollout(sessions, SYNTHETIC_THREAD_ID, session_rows())
    second = sessions / "2026" / "10" / "28"
    second.mkdir(parents=True)
    (second / f"rollout-another-{SYNTHETIC_THREAD_ID}.jsonl").write_text(
        "{}\n", encoding="utf-8"
    )
    source = LocalCodexQuotaStatusSource(sessions)

    # When
    snapshot = await source.read_session_for_thread(SYNTHETIC_THREAD_ID)

    # Then
    assert snapshot is None


async def test_local_source_rejects_rollouts_over_its_read_bound(
    tmp_path: Path,
) -> None:
    # Given
    sessions = tmp_path / "sessions"
    rollout = write_rollout(sessions, SYNTHETIC_THREAD_ID, session_rows())
    with rollout.open("r+b") as stream:
        stream.truncate(128 * 1024 * 1024 + 1)
    source = LocalCodexQuotaStatusSource(sessions)

    # When
    snapshot = await source.read_session_for_thread(SYNTHETIC_THREAD_ID)

    # Then
    assert snapshot is None


async def test_local_source_rejects_a_truncated_rollout_tail(tmp_path: Path) -> None:
    # Given
    sessions = tmp_path / "sessions"
    rollout = write_rollout(sessions, SYNTHETIC_THREAD_ID, session_rows())
    rollout.write_bytes(rollout.read_bytes() + b'{"type":"event_msg"')
    source = LocalCodexQuotaStatusSource(sessions)

    # When
    snapshot = await source.read_session_for_thread(SYNTHETIC_THREAD_ID)

    # Then
    assert snapshot is None


async def test_local_source_file_read_does_not_block_event_loop(tmp_path: Path) -> None:
    # Given
    entered = Event()
    release = Event()

    class BlockingSource(LocalCodexQuotaStatusSource):
        @override
        def _read_session_for_thread(
            self, thread_id: str, /
        ) -> RawCodexSessionSnapshot | None:
            del thread_id
            entered.set()
            assert release.wait(2.0)
            return None

    source = BlockingSource(tmp_path)
    pending = asyncio.create_task(source.read_session_for_thread(SYNTHETIC_THREAD_ID))

    # When
    assert await asyncio.wait_for(asyncio.to_thread(entered.wait), timeout=1.0)
    await asyncio.sleep(0)

    # Then
    assert not pending.done()
    release.set()
    assert await pending is None


async def test_exact_source_reread_is_idempotent_and_conflict_fails_closed(
    tmp_path: Path,
) -> None:
    # Given
    sessions = tmp_path / "sessions"
    rollout = write_rollout(sessions, SYNTHETIC_THREAD_ID, session_rows())
    reader = make_local_reader(sessions, make_identity_scope())
    attempt = make_attempt_evidence(thread_started())

    # When
    first = await reader.observe_settled_attempt(attempt)
    second = await reader.observe_settled_attempt(attempt)
    rollout.write_bytes(
        rollout.read_bytes().replace(b'"used_percent":35', b'"used_percent":91', 1)
    )
    conflicting = await reader.observe_settled_attempt(attempt)

    # Then
    assert [window.state for window in first.windows] == ["available", "available"]
    assert [window.state for window in second.windows] == ["available", "available"]
    assert [window.state for window in conflicting.windows] == ["unknown", "unknown"]
    assert (
        conflicting.diagnostic == "quota source repeated an ordinal with changed facts"
    )
    assert conflicting.windows[0].usage_percent == pytest.approx(91.0)


async def test_exact_source_reread_does_not_refresh_producer_age(
    tmp_path: Path,
) -> None:
    # Given
    sessions = tmp_path / "sessions"
    write_rollout(sessions, SYNTHETIC_THREAD_ID, session_rows())
    runtime = SequenceRuntime(("2026-10-27T10:00:00Z", "2026-10-27T10:00:02Z"))
    reader = make_local_reader(
        sessions, make_identity_scope(), max_age=1.0, runtime=runtime
    )
    attempt = make_attempt_evidence(thread_started())

    # When
    first = await reader.observe_settled_attempt(attempt)
    repeated = await reader.observe_settled_attempt(attempt)

    # Then
    assert first.windows[0].state == "available"
    assert repeated.windows[0].state == "unknown"
    assert repeated.windows[0].source_observed_at_utc == "2026-10-27T09:59:59Z"
    assert repeated.windows[0].source_sequence == 17
    assert repeated.windows[0].usage_percent == pytest.approx(35.0)


async def test_older_available_record_cannot_replace_fresh_exhaustion(
    tmp_path: Path,
) -> None:
    # Given
    sessions = tmp_path / "sessions"
    rollout = write_rollout(
        sessions,
        SYNTHETIC_THREAD_ID,
        session_rows(timestamp="2026-10-27T09:59:59Z", primary_used=100),
    )
    reader = make_local_reader(sessions, make_identity_scope())
    attempt = make_attempt_evidence(thread_started())

    # When
    exhausted = await reader.observe_settled_attempt(attempt)
    second_day = sessions / "2026" / "10" / "28"
    second_day.mkdir(parents=True)
    moved_rollout = second_day / rollout.name
    rollout.rename(moved_rollout)
    content = moved_rollout.read_bytes()
    content = content.replace(b"2026-10-27T09:59:59Z", b"2026-10-27T09:59:58Z", 1)
    content = content.replace(b'"used_percent":100', b'"used_percent":35', 1)
    content = content.replace(b'"ordinal":17', b'"ordinal":18', 1)
    moved_rollout.write_bytes(content)
    older = await reader.observe_settled_attempt(attempt)

    # Then
    assert exhausted.windows[0].state == "exhausted"
    assert older.windows[0].state == "unknown"
    assert older.windows[0].usage_percent == pytest.approx(35.0)


async def test_repeated_old_source_cannot_override_newer_other_source() -> None:
    # Given
    source = RecordingSource(None)
    reader = make_reader(source, make_identity_scope(), None, None)
    attempt = make_attempt_evidence(thread_started())

    def snapshot(
        coordinate: str, timestamp: str, primary_used: int, ordinal: int
    ) -> RawCodexSessionSnapshot:
        rows = session_rows(
            timestamp=timestamp, primary_used=primary_used, ordinal=ordinal
        )
        content = b"\n".join(
            json.dumps(row, separators=(",", ":")).encode() for row in rows
        )
        return RawCodexSessionSnapshot(content, coordinate, SYNTHETIC_THREAD_ID)

    old_record = snapshot("coordinate-old", "2026-10-27T09:59:58Z", 35, 17)
    source.snapshot = old_record

    # When
    first = await reader.observe_settled_attempt(attempt)
    source.snapshot = snapshot("coordinate-new", "2026-10-27T09:59:59Z", 100, 18)
    newer = await reader.observe_settled_attempt(attempt)
    source.snapshot = old_record
    repeated_old = await reader.observe_settled_attempt(attempt)

    # Then
    assert first.windows[0].state == "available"
    assert newer.windows[0].state == "exhausted"
    assert repeated_old.windows[0].state == "unknown"
    assert repeated_old.diagnostic == "quota snapshot is older than a prior observation"


async def test_past_reset_hint_does_not_override_exhausted_usage(
    tmp_path: Path,
) -> None:
    # Given
    sessions = tmp_path / "sessions"
    rows = session_rows(primary_used=100)
    quota_row = rows[-1]
    payload = quota_row["payload"]
    assert isinstance(payload, dict)
    limits = payload["rate_limits"]
    assert isinstance(limits, dict)
    primary = limits["primary"]
    assert isinstance(primary, dict)
    primary["resets_at"] = 0
    write_rollout(sessions, SYNTHETIC_THREAD_ID, rows)
    reader = make_local_reader(sessions, make_identity_scope())

    # When
    observation = await reader.observe_settled_attempt(
        make_attempt_evidence(thread_started())
    )

    # Then
    assert observation.windows[0].state == "exhausted"
    assert observation.windows[0].reset_at_utc == "1970-01-01T00:00:00Z"


@pytest.mark.parametrize("reset_value", [None, "invalid-synthetic-reset"])
async def test_invalid_reset_hint_preserves_known_exhaustion(
    tmp_path: Path, reset_value: object
) -> None:
    # Given
    sessions = tmp_path / "sessions"
    rows = session_rows(primary_used=100)
    payload = rows[-1]["payload"]
    assert isinstance(payload, dict)
    limits = payload["rate_limits"]
    assert isinstance(limits, dict)
    primary = limits["primary"]
    assert isinstance(primary, dict)
    if reset_value is None:
        del primary["resets_at"]
    else:
        primary["resets_at"] = reset_value
    write_rollout(sessions, SYNTHETIC_THREAD_ID, rows)
    reader = make_local_reader(sessions, make_identity_scope())

    # When
    observation = await reader.observe_settled_attempt(
        make_attempt_evidence(thread_started())
    )

    # Then
    assert observation.windows[0].state == "exhausted"
    assert observation.windows[0].reset_at_utc is None


@pytest.mark.parametrize(
    ("primary_used", "expected_state"),
    [(35, "available"), (100, "exhausted")],
)
async def test_probe_assesses_only_fresh_scoped_local_telemetry(
    tmp_path: Path, primary_used: int, expected_state: QuotaState
) -> None:
    # Given
    scope = make_identity_scope()
    sessions = tmp_path / "sessions"
    write_rollout(
        sessions,
        SYNTHETIC_THREAD_ID,
        session_rows(timestamp="2026-10-27T09:59:59Z", primary_used=primary_used),
    )
    runtime = SequenceRuntime((
        "2026-10-27T09:59:58Z",
        "2026-10-27T10:00:01Z",
        "2026-10-27T10:00:02Z",
    ))
    attempt = RecordingAttemptCall(
        make_process_result(thread_started(), b"synthetic stderr")
    )
    reader = make_local_reader(sessions, scope, runtime=runtime, attempt_call=attempt)
    request = make_probe_request(scope=scope)

    # When
    result = await reader.poll(request, stop_dispatch)

    # Then
    assert result.quota_state == expected_state
    assert result.observation is not None
    assert result.observation.scope == scope
    assert len(attempt.calls) == 1


@pytest.mark.parametrize(
    ("primary_used", "exit_status", "safe_cleanup", "expected_state"),
    [
        (100, 1, True, "exhausted"),
        (35, 1, True, "unknown"),
        (35, 0, False, "unknown"),
        (100, 1, False, "unknown"),
        (35, 0, True, "available"),
    ],
)
async def test_probe_assessment_requires_safe_settlement(
    tmp_path: Path,
    primary_used: int,
    exit_status: int,
    safe_cleanup: bool,
    expected_state: QuotaState,
) -> None:
    # Given
    scope = make_identity_scope()
    sessions = tmp_path / "sessions"
    write_rollout(
        sessions,
        SYNTHETIC_THREAD_ID,
        session_rows(timestamp="2026-10-27T09:59:59Z", primary_used=primary_used),
    )
    completed = make_process_result(thread_started(), b"synthetic stderr")
    cleanup = (
        completed.observation.cleanup
        if safe_cleanup
        else CleanupEvidence(
            "owned",
            (SignalAttempt("SIGTERM", "sent", None),),
            "expired",
            None,
        )
    )
    process = Completed(
        AttemptObservation(completed.observation.output, 0.25, cleanup), exit_status
    )
    runtime = SequenceRuntime((
        "2026-10-27T09:59:58Z",
        "2026-10-27T10:00:01Z",
        "2026-10-27T10:00:02Z",
    ))
    attempt = RecordingAttemptCall(process)
    reader = make_local_reader(sessions, scope, runtime=runtime, attempt_call=attempt)
    request = make_probe_request(scope=scope)

    # When
    result = await reader.poll(request, stop_dispatch)

    # Then
    assert result.quota_state == expected_state
    assert len(attempt.calls) == 1


@pytest.mark.parametrize("failure", [TimedOut, OutputLimitExceeded])
async def test_non_completed_probe_outcomes_never_confirm_quota_state(
    tmp_path: Path, failure: type[TimedOut] | type[OutputLimitExceeded]
) -> None:
    # Given
    scope = make_identity_scope()
    sessions = tmp_path / "sessions"
    write_rollout(
        sessions,
        SYNTHETIC_THREAD_ID,
        session_rows(timestamp="2026-10-27T09:59:59Z", primary_used=100),
    )
    completed = make_process_result(thread_started(), b"synthetic stderr")
    process = failure(completed.observation, 1)
    runtime = SequenceRuntime((
        "2026-10-27T09:59:58Z",
        "2026-10-27T10:00:01Z",
        "2026-10-27T10:00:02Z",
    ))
    reader = make_local_reader(
        sessions, scope, runtime=runtime, attempt_call=RecordingAttemptCall(process)
    )

    # When
    result = await reader.poll(make_probe_request(scope=scope), stop_dispatch)

    # Then
    assert result.quota_state == "unknown"


def test_scope_hash_is_stable_and_does_not_retain_identity() -> None:
    # Given
    account = "private-synthetic-account"
    user = "private-synthetic-user"

    # When
    first = codex_quota_scope_from_identity("openai", account, user)
    second = codex_quota_scope_from_identity("openai", account, user)

    # Then
    assert first == second
    assert account not in repr(first)
    assert user not in repr(first)
    with pytest.raises(ValueError, match="OpenAI provider"):
        codex_quota_scope_from_identity("other", account, user)


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
        exit_status=None,
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
        max_age: float,
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


async def test_assessment_error_retains_normalized_observation_and_process() -> None:
    # Given
    quota_request = make_probe_request()
    attempt_request = make_probe_attempt_request()
    process_result = make_process_result(b"assessment stdout", b"assessment stderr")
    observation = QuotaObservation(
        scope=quota_request.schedule.scope,
        read_at_utc="2026-10-27T10:00:00Z",
        source_coordinate="opaque-source",
        windows=(),
        diagnostic="normalized before assessment",
    )
    assessor_error = RuntimeError("assessment failed")

    async def attempt_call(
        request: AttemptRequest, stop: DispatchStop, /
    ) -> AttemptResult:
        await asyncio.sleep(0)
        assert request is attempt_request
        del stop
        return process_result

    def fail_assessment(
        attempt: AttemptEvidence, received: QuotaObservation | None, /
    ) -> tuple[QuotaState, str | None]:
        assert received is observation
        assert attempt.outcome is process_result
        raise assessor_error

    reader = make_reader(
        RecordingSource(None),
        quota_request.schedule.scope,
        lambda raw: None,
        lambda snapshot, scope, read_at, max_age: observation,
        attempt_call,
        lambda request, settings: attempt_request,
        fail_assessment,
    )

    # When
    with pytest.raises(RuntimeError, match="assessment failed") as raised:
        await reader.poll(quota_request, stop_dispatch)

    # Then
    assert raised.value is assessor_error
    evidence = quota_probe_evidence(assessor_error, quota_request)
    assert evidence is not None
    assert evidence.observation is observation
    assert evidence.quota_state == "unknown"
    assert evidence.process.outcome is process_result
    assert evidence.process.request is attempt_request
    assert evidence.process.usage_telemetry == b"assessment stdout"


async def test_call_supervisor_attached_outcome_is_retained_on_stop_error() -> None:
    # Given
    quota_request = make_probe_request()
    attempt_request = make_probe_attempt_request()
    stdout = b"settled despite stop-hook error"
    process_result = Completed(
        observation=AttemptObservation(
            output=CapturedOutput(stdout, b"real stderr"),
            elapsed_seconds=0.5,
            cleanup=CleanupEvidence("owned", (), "expired", None),
        ),
        exit_status=0,
    )
    stop_error = RuntimeError("dispatch stop failed")

    async def attempt(request: AttemptRequest, /) -> AttemptResult:
        await asyncio.sleep(0)
        assert request is attempt_request
        return process_result

    async def attempt_call(
        request: AttemptRequest, stop: DispatchStop, /
    ) -> AttemptResult:
        return await call_supervisor(request, attempt, stop)

    def failing_stop(outcome: AttemptResult | BaseException, /) -> None:
        assert outcome is process_result
        raise stop_error

    reader = make_reader(
        RecordingSource(None),
        quota_request.schedule.scope,
        lambda raw: None,
        None,
        attempt_call,
        lambda request, settings: attempt_request,
    )

    # When
    with pytest.raises(RuntimeError, match="dispatch stop failed") as raised:
        await reader.poll(quota_request, failing_stop)

    # Then
    assert raised.value is stop_error
    evidence = quota_probe_evidence(stop_error, quota_request)
    assert evidence is not None
    assert evidence.process.control_flow == "raised"
    assert evidence.process.outcome is process_result
    assert evidence.process.request is attempt_request
    assert evidence.process.usage_telemetry is stdout
    assert process_result.observation.output is not None
    assert process_result.observation.output.stderr == b"real stderr"


def test_malformed_preexisting_evidence_is_not_overwritten() -> None:
    # Given
    class ErrorWithEvidence(RuntimeError):
        _ataraxia_quota_probe_evidence: object

    error = ErrorWithEvidence("malformed evidence")
    malformed = ("not quota evidence",)
    error._ataraxia_quota_probe_evidence = malformed
    request = make_probe_request()
    evidence = QuotaProbeEvidence(
        request=request,
        process=AttemptEvidence(
            control_flow="raised",
            outcome=None,
            error_type="RuntimeError",
            diagnostic="failure",
            request=make_probe_attempt_request(),
            started_at_utc="2026-10-27T10:00:00Z",
            ended_at_utc="2026-10-27T10:00:00Z",
            usage_telemetry=None,
        ),
        quota_state="unknown",
        observation=None,
        classification_basis="incomplete",
    )

    # When
    quota_evidence_module.attach_quota_probe_evidence(error, evidence)

    # Then
    assert error._ataraxia_quota_probe_evidence is malformed
    assert quota_probe_evidence(error, request) is None


def test_evidence_attachment_failure_does_not_replace_primary_error() -> None:
    # Given
    class UnavailableExceptionAttributes(RuntimeError):
        """Simulate a raised exception with inaccessible instance storage."""

        def __getattribute__(self, name: str, /) -> object:
            if name == "__dict__":
                raise RuntimeError("attribute storage unavailable")
            return super().__getattribute__(name)

    error = UnavailableExceptionAttributes("primary error")
    request = make_probe_request()
    evidence = QuotaProbeEvidence(
        request=request,
        process=AttemptEvidence(
            control_flow="raised",
            outcome=None,
            error_type="RuntimeError",
            diagnostic="failure",
            request=make_probe_attempt_request(),
            started_at_utc="2026-10-27T10:00:00Z",
            ended_at_utc="2026-10-27T10:00:00Z",
            usage_telemetry=None,
        ),
        quota_state="unknown",
        observation=None,
        classification_basis="incomplete",
    )

    # When
    quota_evidence_module.attach_quota_probe_evidence(error, evidence)

    # Then
    assert str(error) == "primary error"
    assert quota_probe_evidence(error, request) is None


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
