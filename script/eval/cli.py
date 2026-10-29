# SPDX-License-Identifier: Apache-2.0
"""Composition of a frozen evaluation plan and one provider-bound run.

Argument parsing, terminal output, and signal handling are not implemented yet.
"""

import asyncio
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol

from .evidence import EvidenceStore
from .inputs import RepositoryReader
from .model import DryRunReport, HarnessConfig, RunRecord
from .plan import PlanBuilder
from .runner import AttemptRequestBuilder, BoundRun, CliBindingResolver
from .runner.coordinator.settlement import SettledFailure, settle
from .tokens import TokenEstimator, build_dry_run_report


class RunCoordinator(Protocol):
    """One already bound run, owned until its final record is settled."""

    async def run(self) -> RunRecord:
        """Execute the bound run and return its final record."""
        ...


class CoordinatorFactory(Protocol):
    """Construct a provider coordinator after evidence and requests exist."""

    def __call__(
        self, bound_run: BoundRun, evidence: EvidenceStore, config: HarnessConfig, /
    ) -> RunCoordinator:
        """Bind the run and its store to one coordinator."""
        ...


def parse_config(argv: Sequence[str], /) -> HarnessConfig:
    """Parse ordered options without performing I/O (not yet implemented)."""
    raise NotImplementedError("CLI argument parsing is not implemented")


@dataclass(frozen=True)
class Composition:
    """Connect explicit collaborators, deferring execution-only construction.

    For example, dry run freezes and plans inputs, then estimates them without
    constructing an evidence store or resolving a provider binding.
    """

    repository: RepositoryReader
    planner: PlanBuilder
    estimator: TokenEstimator
    binding_resolver: CliBindingResolver
    request_builder: AttemptRequestBuilder
    evidence_factory: Callable[[], EvidenceStore]
    coordinator_factory: CoordinatorFactory

    async def execute(self, config: HarnessConfig, /) -> DryRunReport | RunRecord:
        """Prepare a plan, then estimate it or run its bound requests.

        Blocking preparation and provider binding run off the event loop. A
        cancelled preparation is retained until it settles and cannot dispatch.

        Returns:
            The dry-run report or the coordinator's final record.

        Raises:
            ValueError: Execution has no output directory.
        """
        inputs = await _run_blocking(self.repository.freeze, config)
        plan = self.planner.plan(inputs, config)
        if config.dry_run:
            return await _run_blocking(build_dry_run_report, plan, self.estimator)
        binding = await _run_blocking(self.binding_resolver.resolve, config)
        output = config.output_directory
        if output is None:
            raise ValueError("execution requires an output directory")
        evidence = self.evidence_factory()
        prepared = await evidence.create(output, plan)
        calls = tuple(
            self.request_builder.build(plan, call, binding, prepared, config)
            for call in plan.calls
        )
        bound = BoundRun(plan, binding, prepared, calls)
        return await self.coordinator_factory(bound, evidence, config).run()


async def _run_blocking[**P, T](
    operation: Callable[P, T], /, *args: P.args, **kwargs: P.kwargs
) -> T:
    """Retain a submitted thread operation before propagating cancellation.

    Returns:
        The operation's value after it settles.
    """
    result = await settle(
        asyncio.create_task(asyncio.to_thread(operation, *args, **kwargs))
    )
    if result.cancellation is not None:
        if isinstance(result, SettledFailure):
            raise result.cancellation from result.error
        raise result.cancellation
    if isinstance(result, SettledFailure):
        raise result.error
    return result.value
