# SPDX-License-Identifier: Apache-2.0
"""Composition of a frozen evaluation plan and one provider-bound run.

Standalone parsing and lifecycle are supplied by the command adapters.
"""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from script.eval.evidence import EvidenceStore
from script.eval.inputs import RepositoryReader
from script.eval.model import DryRunReport, FrozenPlan, HarnessConfig, RunRecord
from script.eval.options import parse_config as parse_config
from script.eval.plan import PlanBuilder
from script.eval.runner import AttemptRequestBuilder, BoundRun, CliBindingResolver
from script.eval.runner.coordinator.settlement import SettledFailure, settle
from script.eval.tokens import TokenEstimator, build_dry_run_report


class RunCoordinator(Protocol):
    """One already bound run, owned until its final record is settled."""

    async def run(self) -> RunRecord:
        """Execute the bound run and return its final record."""
        ...


class CoordinatorFactory(Protocol):
    """Construct a provider coordinator after evidence and requests exist."""

    def __call__(
        self, bound_run: BoundRun, evidence: EvidenceStore, /
    ) -> RunCoordinator:
        """Bind the run and its store to one coordinator."""
        ...


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
    on_plan: Callable[[FrozenPlan], None] | None = None

    async def execute(self, config: HarnessConfig, /) -> DryRunReport | RunRecord:
        """Prepare a plan, then estimate it or run its bound requests.

        Blocking preparation and provider binding run off the event loop. A
        cancelled preparation is retained until it settles and cannot dispatch.

        Returns:
            The dry-run report or the coordinator's final record.

        """
        inputs = await _run_blocking(self.repository.freeze, config)
        plan = self.planner.plan(inputs, config)
        if self.on_plan is not None:
            self.on_plan(plan)
        if config.dry_run:
            return await _run_blocking(build_dry_run_report, plan, self.estimator)
        binding = await _run_blocking(self.binding_resolver.resolve, config)
        output = config.output_directory
        assert output is not None  # Validated execution configuration.
        evidence = self.evidence_factory()
        prepared = await evidence.create(output, plan)
        calls = tuple(
            self.request_builder.build(plan, call, binding, prepared, config)
            for call in plan.calls
        )
        bound = BoundRun(plan, binding, prepared, calls)
        return await self.coordinator_factory(bound, evidence).run()


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
