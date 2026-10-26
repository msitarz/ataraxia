# SPDX-License-Identifier: Apache-2.0
"""Pure orchestration boundary for ordered evaluation planning."""

from dataclasses import dataclass
from typing import Protocol

from script.eval.model import FrozenInputs, FrozenPlan, HarnessConfig, PlannedCall


@dataclass(frozen=True)
class GroupedInputs:
    """Snapshots grouped by the directory positions in one configuration."""

    snapshots: tuple[tuple[int, tuple[int, ...]], ...]


@dataclass(frozen=True)
class ComposedContexts:
    """Composed contexts in deterministic positions, before call expansion."""

    boundary_bytes: tuple[bytes, ...]
    prompts: tuple[tuple[tuple[int, ...], bytes], ...]


class InputGrouper(Protocol):
    """Group frozen source indices by configured directory position."""

    def group(self, inputs: FrozenInputs, config: HarnessConfig, /) -> GroupedInputs:
        """Return ordered groups of indices into ``inputs.sources``."""


class ContextComposer(Protocol):
    """Compose each source selection into exact prompt bytes."""

    def compose(
        self,
        inputs: FrozenInputs,
        grouped: GroupedInputs,
        config: HarnessConfig,
        /,
    ) -> ComposedContexts:
        """Compose from frozen source bytes and return contexts in stable order."""


class CallScheduler(Protocol):
    """Expand composed contexts over model and effort settings."""

    def schedule(
        self, composed: ComposedContexts, config: HarnessConfig, /
    ) -> tuple[PlannedCall, ...]:
        """Return ordered calls with their final zero-based positions."""


class PlanBuilder(Protocol):
    """Public pure planning boundary."""

    def plan(self, inputs: FrozenInputs, config: HarnessConfig, /) -> FrozenPlan:
        """Compose exact snapshot bytes and return the complete ordered plan."""


class _UnimplementedInputGrouper:
    def group(self, inputs: FrozenInputs, config: HarnessConfig, /) -> GroupedInputs:
        raise NotImplementedError("source grouping is not implemented yet")


class _UnimplementedContextComposer:
    def compose(
        self,
        inputs: FrozenInputs,
        grouped: GroupedInputs,
        config: HarnessConfig,
        /,
    ) -> ComposedContexts:
        raise NotImplementedError(
            "separator decoding and prompt composition are not implemented yet"
        )


class _UnimplementedCallScheduler:
    def schedule(
        self, composed: ComposedContexts, config: HarnessConfig, /
    ) -> tuple[PlannedCall, ...]:
        raise NotImplementedError("scheduled call expansion is not implemented yet")


class PurePlanBuilder(PlanBuilder):
    """Wire pure planning steps and assemble a frozen plan.

    The caller owns and supplies the run identity. Constructing a planner and
    calling it use no clock, random source, filesystem, Git, or model process.
    """

    def __init__(
        self,
        run_id: str,
        *,
        grouper: InputGrouper | None = None,
        composer: ContextComposer | None = None,
        scheduler: CallScheduler | None = None,
    ) -> None:
        self._run_id = run_id
        self._grouper = grouper if grouper is not None else _UnimplementedInputGrouper()
        self._composer = (
            composer if composer is not None else _UnimplementedContextComposer()
        )
        self._scheduler = (
            scheduler if scheduler is not None else _UnimplementedCallScheduler()
        )

    def plan(self, inputs: FrozenInputs, config: HarnessConfig, /) -> FrozenPlan:
        """Wire planning steps and return the immutable plan value.

        Returns:
            The plan assembled from caller-supplied identities and collaborators.
        """
        grouped = self._grouper.group(inputs, config)
        composed = self._composer.compose(inputs, grouped, config)
        calls = self._scheduler.schedule(composed, config)
        return FrozenPlan(
            run_id=self._run_id,
            configuration=config,
            repository_root=inputs.repository_root,
            head_commit=inputs.head_commit,
            snapshots=inputs.sources,
            boundary_bytes=composed.boundary_bytes,
            instructions_file=inputs.instructions_file,
            calls=calls,
        )
