# SPDX-License-Identifier: Apache-2.0
"""Standalone execution, signal ownership, and explicit exit status."""

import asyncio
from collections.abc import Callable, Coroutine, Generator
from contextlib import AbstractContextManager, contextmanager, suppress
import os
from pathlib import Path
import signal
import sys
import tempfile
from typing import Protocol
from uuid import uuid4

from script.eval.cli import Composition, RunCoordinator
from script.eval.dry_run import format_dry_run
from script.eval.evidence import EvidenceStore, create_evidence_store
from script.eval.evidence_status import EvidenceStatus
from script.eval.inputs import GitRepositoryReader
from script.eval.model import (
    AttemptEvidence,
    DryRunReport,
    FrozenPlan,
    HarnessConfig,
    QuotaObservation,
    QuotaProbeEvidence,
    QuotaProbeRequest,
    QuotaScope,
    RunRecord,
)
from script.eval.options import parse_config
from script.eval.plan import PurePlanBuilder
from script.eval.runner import BoundRun, ProgressSink
from script.eval.runner.adapters import (
    CodexAttemptRequestBuilder,
    CodexCliBindingResolver,
    CodexOutcomeClassifier,
    CodexQuotaSettings,
    CodexQuotaStatusReader,
    LocalCodexQuotaStatusSource,
    ProgressWriter,
    SilentProgressSink,
    SystemRuntime,
    TerminalProgressSink,
    open_progress_writer,
)
from script.eval.runner.adapters.codex_version import supports_quota_version
from script.eval.runner.coordinator import Coordinator
from script.eval.runner.ports import QuotaStatusReader, QuotaTelemetryError
from script.eval.tokens import tiktoken_estimator
from script.process_supervisor import (
    AttemptRequest,
    AttemptResult,
    DispatchStop,
    call_supervisor,
    run_attempt,
)

_QUOTA_MINIMUM_AGE_SECONDS = 60.0
_QUOTA_POLL_AGE_MARGIN_SECONDS = 60.0


async def _attempt(request: AttemptRequest, stop: DispatchStop, /) -> AttemptResult:
    """Forward one attempt through the existing supervisor.

    Returns:
        The supervisor's settled result.
    """
    return await call_supervisor(request, run_attempt, stop)


class UnavailableQuota:
    """Fail closed without reading provider sessions or launching probes."""

    @property
    def expected_scope(self) -> QuotaScope | None:
        """No provider scope has been verified."""
        return None

    async def observe_settled_attempt(
        self, evidence: AttemptEvidence, /
    ) -> QuotaObservation:
        """Return an explicitly unavailable observation.

        Returns:
            An observation with no inferred scope or quota values.
        """
        return QuotaObservation(
            scope=None,
            read_at_utc=SystemRuntime().utc_now(),
            source_coordinate=None,
            windows=(),
            diagnostic="quota scope unavailable",
        )

    async def poll(
        self, request: QuotaProbeRequest, stop_dispatch: DispatchStop, /
    ) -> QuotaProbeEvidence:
        """Refuse an unsupported probe.

        Raises:
            RuntimeError: Quota polling cannot be scoped.
        """
        raise RuntimeError("quota scope unavailable")


def create_composition(status: EvidenceStatus) -> Composition:
    """Assemble the concrete one-run dependencies without provider effects.

    Returns:
        A composition whose execution leaves perform their effects when invoked.
    """
    runtime = SystemRuntime()

    def coordinator(bound: BoundRun, evidence: EvidenceStore, /) -> ProgressRun:
        config = bound.plan.configuration
        sink, writer = _progress(config, runtime)
        assets: tempfile.TemporaryDirectory[str] | None = None
        try:
            quota, assets = _quota_reader(bound, runtime)
            runner = Coordinator(
                bound,
                evidence,
                _attempt,
                CodexOutcomeClassifier(cli_version=bound.binding.cli_version),
                quota,
                runtime,
                sink,
            )
        except BaseException:
            _close_progress(writer)
            if assets is not None:
                assets.cleanup()
            raise
        return ProgressRun(runner, writer, assets)

    return Composition(
        GitRepositoryReader(),
        PurePlanBuilder(str(uuid4())),
        tiktoken_estimator(),
        CodexCliBindingResolver(),
        CodexAttemptRequestBuilder(),
        lambda: status,
        coordinator,
        _announce_plan,
    )


def _quota_reader(
    bound: BoundRun, runtime: SystemRuntime
) -> tuple[QuotaStatusReader, tempfile.TemporaryDirectory[str] | None]:
    """Prepare opt-in probe assets and the existing Codex reader.

    Returns:
        The reader and its owned temporary resource, if enabled.

    Raises:
        ValueError: The CLI version or Codex home is unsupported.
    """
    config = bound.plan.configuration
    if not config.quota_wait_enabled:
        return UnavailableQuota(), None
    if not supports_quota_version(bound.binding.cli_version):
        raise ValueError("quota waiting requires Codex CLI 0.164.0 or later")
    sessions = _sessions_directory()
    assets = tempfile.TemporaryDirectory(prefix="ataraxia-quota-")
    try:
        settings = _probe_settings(bound, Path(assets.name))
        reader = CodexQuotaStatusReader(
            source=LocalCodexQuotaStatusSource(sessions),
            quota_scope=bound.binding.quota_scope,
            settings=settings,
            attempt_call=_attempt,
            runtime=runtime,
            max_observation_age_seconds=max(
                _QUOTA_MINIMUM_AGE_SECONDS,
                config.quota_poll_interval_seconds + _QUOTA_POLL_AGE_MARGIN_SECONDS,
            ),
        )
    except BaseException:
        assets.cleanup()
        raise
    return reader, assets


def _probe_settings(bound: BoundRun, root: Path) -> CodexQuotaSettings:
    """Stage frozen instructions and an empty read-only probe directory.

    Returns:
        The fixed probe's paths and finite supervisor limits.
    """
    config = bound.plan.configuration
    cwd = root / "empty"
    cwd.mkdir(mode=0o555)
    instructions = root / "instructions.txt"
    instructions.write_text("Reply only READY.\n", encoding="utf-8")
    return CodexQuotaSettings(
        bound.binding.executable_path,
        cwd,
        instructions,
        config.timeout_seconds,
        config.cleanup_timeout_seconds,
        config.output_limit_bytes,
        config.grace_seconds,
    )


async def execute(
    config: HarnessConfig, status: EvidenceStatus
) -> DryRunReport | RunRecord:
    """Execute one standalone composition.

    Returns:
        A dry-run report or final run record.
    """
    return await create_composition(status).execute(config)


def main() -> int:
    """Run one owned event loop and map outcomes to process status.

    Exit 0 means success, 1 means a failed run or invalid prerequisites,
    2 means command-line validation failure, 3 means submitted evidence setup
    or recording failed or remained incomplete (including an existing output),
    and 130 means cancellation. Progress is best effort and may be dropped
    when stderr is slow or unavailable.

    Returns:
        The process exit status.
    """
    config = parse_config(sys.argv[1:])
    try:
        with asyncio.Runner() as runner:
            status = EvidenceStatus(create_evidence_store)
            return runner.run(run_owned(config, status, execute))
    except KeyboardInterrupt:
        return 130


async def run_owned(
    config: HarnessConfig,
    status: EvidenceStatus,
    operation: Callable[
        [HarnessConfig, EvidenceStatus],
        Coroutine[object, object, DryRunReport | RunRecord],
    ],
    /,
    *,
    signals: Callable[
        [asyncio.AbstractEventLoop, asyncio.Task[object]], AbstractContextManager[None]
    ]
    | None = None,
) -> int:
    """Own signals and the run task until its work settles.

    Returns:
        The process status for the settled operation.
    """
    owner = asyncio.current_task()
    assert owner is not None
    signal_owner = _owned_signals if signals is None else signals
    with signal_owner(asyncio.get_running_loop(), owner):
        return await _settled_status(operation(config, status), status)


@contextmanager
def _owned_signals(
    loop: asyncio.AbstractEventLoop, owner: asyncio.Task[object]
) -> Generator[None]:
    """Install cancellation handlers before dispatch and restore prior handlers."""
    previous = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
    installed: list[signal.Signals] = []
    try:
        for sig in previous:
            loop.add_signal_handler(sig, owner.cancel)
            installed.append(sig)
        yield
    finally:
        for sig in installed:
            loop.remove_signal_handler(sig)
            signal.signal(sig, previous[sig])


async def _settled_status(
    operation: Coroutine[object, object, DryRunReport | RunRecord],
    status: EvidenceStatus,
) -> int:
    """Await the operation through cleanup and map its result or exception.

    Returns:
        The corresponding standalone exit status.
    """
    try:
        result = await operation
    except asyncio.CancelledError:
        return 130
    except Exception as error:
        sys.stderr.write(f"evaluation failed: {error}\n")
        return (
            3
            if isinstance(error, QuotaTelemetryError)
            or (status.started and (status.failed or not status.finalized))
            else 1
        )
    _print_result(result)
    return _exit_status(result)


def _exit_status(result: DryRunReport | RunRecord) -> int:
    """Map completed accounting to its process status.

    Returns:
        Zero for success, one for failed calls, or three for incomplete runs.
    """
    if isinstance(result, DryRunReport):
        return 0
    if result.state == "incomplete":
        return 3
    return 1 if any(call.state != "complete" for call in result.calls) else 0


def _print_result(result: DryRunReport | RunRecord) -> None:
    """Render final accounting or supplied-context estimates to stdout."""
    if isinstance(result, RunRecord):
        sys.stdout.write(
            f"run {result.run_id}: {result.state}; "
            f"{len(result.calls)} scheduled calls\n"
        )
        return
    sys.stdout.write(format_dry_run(result))


def _announce_plan(plan: FrozenPlan) -> None:
    """Display the frozen matrix size before any binding or dispatch."""
    if not plan.configuration.dry_run:
        sys.stdout.write(f"scheduled calls: {len(plan.calls)}\n")
        sys.stdout.flush()


class ProgressResource(Protocol):
    """A progress resource whose admission can be closed promptly."""

    def close(self) -> None:
        """Stop accepting progress without waiting for output."""
        ...


class ProgressRun:
    """Close progress admission when the coordinator settles."""

    def __init__(
        self,
        coordinator: RunCoordinator,
        writer: ProgressResource | None,
        assets: tempfile.TemporaryDirectory[str] | None = None,
    ) -> None:
        """Retain one coordinator and its optional progress writer."""
        self.coordinator = coordinator
        self.writer = writer
        self.assets = assets

    async def run(self) -> RunRecord:
        """Run and close progress without waiting for a blocked writer.

        Returns:
            The coordinator's final record.
        """
        try:
            return await self.coordinator.run()
        finally:
            _close_progress(self.writer)
            if self.assets is not None:
                self.assets.cleanup()


def _sessions_directory() -> Path:
    """Resolve the supported inherited Codex home without reading its contents.

    Returns:
        The sessions directory under the selected home.

    Raises:
        ValueError: The selected home is not a supported existing directory.
    """
    configured = os.environ.get("CODEX_HOME")
    home = Path.home() / ".codex" if configured is None else Path(configured)
    if configured is not None and (not configured or not home.is_absolute()):
        raise ValueError("CODEX_HOME must be a nonempty absolute directory")
    if not home.is_dir():
        raise ValueError("Codex home must be an existing directory")
    return home.resolve() / "sessions"


def _progress(
    config: HarnessConfig, runtime: SystemRuntime
) -> tuple[ProgressSink, ProgressWriter | None]:
    """Select a best-effort writer or silence without affecting the run.

    Returns:
        One progress sink and its writer, if startup succeeded.
    """
    if config.quiet:
        return SilentProgressSink(), None
    try:
        return _start_progress(config, runtime)
    except Exception:
        return SilentProgressSink(), None


def _start_progress(
    config: HarnessConfig, runtime: SystemRuntime
) -> tuple[ProgressSink, ProgressWriter | None]:
    """Prepare one optional writer and its terminal presentation.

    Returns:
        The presentation and its owned writer, or a silent sink.
    """
    fd = sys.stderr.fileno()
    is_tty = os.isatty(fd)
    try:
        columns = max(2, os.get_terminal_size(fd).columns) if is_tty else 80
    except OSError:
        columns = 80
    writer = open_progress_writer(fd)
    if writer is None:
        return SilentProgressSink(), None
    try:
        sink = TerminalProgressSink(
            writer,
            is_tty,
            runtime,
            config.progress_interval_seconds,
            tty_columns=columns,
        )
    except BaseException:
        _close_progress(writer)
        raise
    return sink, writer


def _close_progress(writer: ProgressResource | None) -> None:
    """Disable progress without concealing the run's outcome."""
    if writer is not None:
        with suppress(Exception):
            writer.close()
