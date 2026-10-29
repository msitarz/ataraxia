# SPDX-License-Identifier: Apache-2.0
"""Standalone execution, signal ownership, and explicit exit status."""

import asyncio
from collections.abc import Callable, Coroutine
import signal
import sys
from uuid import uuid4

from script.eval.cli import Composition
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
from script.eval.runner import BoundRun
from script.eval.runner.adapters import (
    CodexAttemptRequestBuilder,
    CodexCliBindingResolver,
    CodexOutcomeClassifier,
    SilentProgressSink,
    SystemRuntime,
)
from script.eval.runner.coordinator import Coordinator
from script.eval.tokens import tiktoken_estimator
from script.process_supervisor import (
    AttemptRequest,
    AttemptResult,
    DispatchStop,
    call_supervisor,
    run_attempt,
)


async def _attempt(request: AttemptRequest, stop: DispatchStop, /) -> AttemptResult:
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

    def coordinator(bound: BoundRun, evidence: EvidenceStore, /) -> Coordinator:
        return Coordinator(
            bound,
            evidence,
            _attempt,
            CodexOutcomeClassifier(),
            UnavailableQuota(),
            runtime,
            SilentProgressSink(),
        )

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


async def execute(
    config: HarnessConfig, status: EvidenceStatus
) -> DryRunReport | RunRecord:
    """Refuse unsupported scoped quota and execute one composition.

    Returns:
        A dry-run report or final run record.

    Raises:
        ValueError: Execution requests quota waiting without a verified scope.
    """
    if config.quota_wait_enabled and not config.dry_run:
        raise ValueError(
            "quota waiting unavailable: provider quota scope is not verified"
        )
    return await create_composition(status).execute(config)


def main() -> int:
    """Run one owned event loop and map outcomes to process status.

    Exit 0 means success, 1 means a failed run or invalid prerequisites,
    2 means command-line validation failure, 3 means incomplete evidence,
    and 130 means cancellation. Progress is silent until a prompt nonblocking
    stderr transport is available.

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
) -> int:
    """Own signals and the run task until its work settles.

    Returns:
        The process status for the settled operation.
    """
    loop = asyncio.get_running_loop()
    task = asyncio.create_task(operation(config, status))
    previous = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
    installed: list[signal.Signals] = []
    try:
        for sig in previous:
            loop.add_signal_handler(sig, task.cancel)
            installed.append(sig)
        try:
            result = await task
        except asyncio.CancelledError:
            return 130
        except Exception as error:
            sys.stderr.write(f"evaluation failed: {error}\n")
            return (
                3 if status.started and (status.failed or not status.finalized) else 1
            )
        _print_result(result)
        return _exit_status(result)
    finally:
        for sig in installed:
            loop.remove_signal_handler(sig)
            signal.signal(sig, previous[sig])


def _exit_status(result: DryRunReport | RunRecord) -> int:
    if isinstance(result, DryRunReport):
        return 0
    if result.state == "incomplete":
        return 3
    return 1 if any(call.state != "complete" for call in result.calls) else 0


def _print_result(result: DryRunReport | RunRecord) -> None:
    if isinstance(result, RunRecord):
        sys.stdout.write(
            f"run {result.run_id}: {result.state}; "
            f"{len(result.calls)} scheduled calls\n"
        )
        return
    sys.stdout.write(
        "Estimates exclude unavailable automatic CLI and system context; "
        "default system instructions remain when no override is supplied.\n"
    )
    for call in result.estimates:
        for estimate in (call.context, call.instructions_file):
            if estimate is not None:
                sys.stdout.write(
                    f"{call.position}: {estimate.basis} model={estimate.model} "
                    f"tokens={estimate.token_count} method={estimate.method} "
                    f"library={estimate.library_version} "
                    f"tokenizer={estimate.tokenizer_version} "
                    f"compatibility={estimate.compatibility} "
                    f"diagnostic={estimate.diagnostic}\n"
                )


def _announce_plan(plan: FrozenPlan) -> None:
    """Display the frozen matrix size before any binding or dispatch."""
    sys.stdout.write(f"scheduled calls: {len(plan.calls)}\n")
    sys.stdout.flush()
