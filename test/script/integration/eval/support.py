# SPDX-License-Identifier: Apache-2.0
"""Shared bounded Git setup and typed evidence inputs for eval integration tests."""

from dataclasses import replace
import os
from pathlib import Path
import subprocess

from script.eval.model import (
    AttemptEvidence,
    AttemptRecord,
    AttemptResult,
    ControlFlow,
    DirectoryOption,
    FrozenPlan,
    HarnessConfig,
    QuotaAllowanceId,
    QuotaObservation,
    QuotaProbeId,
    QuotaProbeRequest,
    QuotaProbeSchedule,
    QuotaProviderId,
    QuotaScope,
)
from script.process_supervisor import (
    AttemptCancelled,
    AttemptFailureEvidence,
    AttemptObservation,
    AttemptRequest,
    CapturedOutput,
    CleanupEvidence,
    Completed,
    InfrastructureFailure,
    OutputLimitExceeded,
    TimedOut,
)


def git_test_environment() -> dict[str, str]:
    """Isolate fixture Git commands from ambient config and variables."""
    environment = {
        name: value for name, value in os.environ.items() if not name.startswith("GIT_")
    }
    environment.update({
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_COUNT": "2",
        "GIT_CONFIG_KEY_0": "core.fsmonitor",
        "GIT_CONFIG_VALUE_0": "false",
        "GIT_CONFIG_KEY_1": "core.hooksPath",
        "GIT_CONFIG_VALUE_1": os.devnull,
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "LC_ALL": "C",
        "LANG": "C",
    })
    return environment


def git(repository: Path, *arguments: str) -> bytes:
    """Run one bounded Git command in a disposable test repository."""
    result = subprocess.run(
        ["git", "-C", os.fspath(repository), *arguments],
        capture_output=True,
        check=True,
        env=git_test_environment(),
        timeout=10,
    )
    return result.stdout


def make_repository(path: Path) -> Path:
    """Create a disposable repository with a known first commit."""
    path.mkdir()
    git(path, "init", "-q", "-b", "master")
    git(path, "config", "user.email", "tests@example.invalid")
    git(path, "config", "user.name", "Evidence tests")
    (path / "context").mkdir()
    (path / "context" / "input.txt").write_bytes(b"context")
    git(path, "add", "--all")
    git(path, "commit", "-qm", "fixture")
    return path


def frozen_plan(repository: Path = Path("/work")) -> FrozenPlan:
    """Build the minimum plan accepted by evidence persistence."""
    configuration = HarnessConfig(
        ordered_options=(DirectoryOption(position=0, path=Path("context")),),
        models=("model-a",),
        efforts=("low",),
        concurrency=1,
        output_directory=Path("results"),
        dry_run=False,
        timeout_seconds=5.0,
        cleanup_timeout_seconds=2.0,
        grace_seconds=0.0,
        output_limit_bytes=0,
        instructions_file_path=None,
    )
    return FrozenPlan(
        run_id="run-1",
        configuration=configuration,
        repository_root=repository,
        head_commit="fixture-head",
        snapshots=(),
        boundary_bytes=(),
        instructions_file=None,
        calls=(),
    )


def attempt_evidence(
    *,
    outcome: AttemptResult | AttemptCancelled | AttemptFailureEvidence | None = None,
    control_flow: ControlFlow = "returned",
    error_type: str | None = None,
    diagnostic: str | None = None,
    ended_at_utc: str | None = "2026-10-26T00:00:01Z",
) -> AttemptEvidence:
    """Build one returned process observation with exact byte streams."""
    request = AttemptRequest(
        argv=("codex", "exec"),
        cwd=Path("/work"),
        timeout_seconds=5.0,
        cleanup_timeout_seconds=2.0,
        output_limit_bytes=0,
        stdin="devnull",
    )
    settled = outcome or Completed(
        AttemptObservation(
            output=CapturedOutput(b"out", b"err"),
            elapsed_seconds=1.0,
            cleanup=CleanupEvidence("owned", (), "reaped", None),
        ),
        exit_status=0,
    )
    return AttemptEvidence(
        control_flow=control_flow,
        outcome=settled,
        error_type=error_type,
        diagnostic=diagnostic,
        request=request,
        started_at_utc="2026-10-26T00:00:00Z",
        ended_at_utc=ended_at_utc,
        usage_telemetry=None,
    )


def supervisor_outcome_cases() -> tuple[
    tuple[
        str,
        AttemptEvidence,
        str,
        str | None,
        int | None,
        str,
        bool,
        str | None,
        str | None,
    ],
    ...,
]:
    """Build controlled outcomes spanning returned, cancelled, and raised flows."""
    cleanup = CleanupEvidence("owned", (), "reaped", None)
    observed = AttemptObservation(
        output=CapturedOutput(b"\x00\xff", b"\xfe"),
        elapsed_seconds=1.25,
        cleanup=cleanup,
    )
    request_evidence = attempt_evidence()
    base = request_evidence
    return (
        (
            "timeout",
            replace(base, outcome=TimedOut(observed, -9)),
            "timed_out",
            "timed_out",
            -9,
            "supervisor_observation",
            True,
            None,
            None,
        ),
        (
            "overflow",
            replace(base, outcome=OutputLimitExceeded(observed, -9)),
            "output_limit_exceeded",
            "output_limit_exceeded",
            -9,
            "supervisor_observation",
            True,
            None,
            None,
        ),
        (
            "cancelled",
            replace(
                base,
                outcome=AttemptCancelled(observed, -15),
                control_flow="cancelled",
            ),
            "cancelled",
            "cancelled",
            -15,
            "supervisor_observation",
            True,
            None,
            None,
        ),
        (
            "infrastructure",
            replace(
                base,
                outcome=InfrastructureFailure(
                    observed, -5, "SpawnError", "spawn failed"
                ),
            ),
            "infrastructure_failure",
            "infrastructure_failure",
            -5,
            "supervisor_observation",
            True,
            "SpawnError",
            "spawn failed",
        ),
        (
            "attached-exception",
            replace(
                base,
                outcome=AttemptFailureEvidence(observed, -11, "stop hook failed"),
                control_flow="raised",
                error_type="RuntimeError",
                diagnostic="original failure",
            ),
            "unexpected_exception",
            "exception",
            -11,
            "supervisor_observation",
            True,
            "RuntimeError",
            "original failure; supervisor: stop hook failed",
        ),
        (
            "unobserved-exception",
            replace(
                base,
                outcome=None,
                control_flow="raised",
                error_type="ValueError",
                diagnostic="failed before acquisition",
                ended_at_utc=None,
            ),
            "unexpected_exception",
            "exception",
            None,
            "unavailable",
            False,
            "ValueError",
            "failed before acquisition",
        ),
    )


def stream_bytes(record: AttemptRecord) -> tuple[bytes | None, bytes | None]:
    """Read retained streams as bytes while preserving unavailable references."""
    stdout = (
        Path(record.stdout_artifact).read_bytes() if record.stdout_artifact else None
    )
    stderr = (
        Path(record.stderr_artifact).read_bytes() if record.stderr_artifact else None
    )
    return stdout, stderr


def quota_probe_request(probe_id: str = "probe-1") -> QuotaProbeRequest:
    """Build a periodic probe request for one opaque quota scope."""
    return QuotaProbeRequest(
        schedule=QuotaProbeSchedule(
            run_id="run-1",
            probe_id=QuotaProbeId(probe_id),
            scope=QuotaScope(
                provider_id=QuotaProviderId("codex"),
                allowance_id=QuotaAllowanceId("a1"),
            ),
            reason="periodic",
            created_at_utc="2026-10-26T00:00:00Z",
            due_at_utc="2026-10-26T00:00:01Z",
            interval_seconds=1.0,
            reset_hint_at_utc=None,
        ),
        pause_wait_id=None,
        poll_started_at_utc="2026-10-26T00:00:01Z",
        scheduled_wait_seconds=1.0,
        scheduled_wait_elapsed_basis="monotonic",
    )


def empty_quota_observation() -> QuotaObservation:
    """Build known scope with an observed empty set of quota windows."""
    return QuotaObservation(
        scope=quota_probe_request().schedule.scope,
        read_at_utc="2026-10-26T00:00:02Z",
        source_coordinate="session:1",
        windows=(),
        diagnostic=None,
    )
