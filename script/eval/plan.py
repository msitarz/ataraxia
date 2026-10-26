# SPDX-License-Identifier: Apache-2.0
"""Pure orchestration boundary for ordered evaluation planning."""

from dataclasses import dataclass
from typing import Protocol

from script.eval.model import FrozenInputs, FrozenPlan, HarnessConfig, PlannedCall


@dataclass(frozen=True)
class GroupedInputs:
    """Map directory-option positions to indices in ``FrozenInputs.sources``.

    For sources ``rules/a.md`` and ``rules/b.md`` at directory position 0,
    followed by ``examples/x.py`` and ``examples/y.py`` at position 2, the
    value is ``((0, (0, 1)), (2, (2, 3)))``. Choosing one index per group
    yields ``(0, 2)``, ``(0, 3)``, ``(1, 2)``, and ``(1, 3)``. These are
    indices, not copied bytes; the composer receives ``FrozenInputs`` too.
    Grouping is an unfinished leaf and this record does not claim it is valid
    or complete for arbitrary inputs.
    """

    snapshots: tuple[tuple[int, tuple[int, ...]], ...]


@dataclass(frozen=True)
class ComposedContexts:
    """Pure context results awaiting expansion over models and efforts.

    ``boundary_bytes`` holds the exact separators for directory boundaries.
    Each ``prompts`` item pairs one ordered tuple of source indices with its
    composed bytes. The optional instructions-file snapshot is separate and
    does not belong in these context bytes.
    """

    boundary_bytes: tuple[bytes, ...]
    prompts: tuple[tuple[tuple[int, ...], bytes], ...]


class InputGrouper(Protocol):
    """Group frozen source indices by their configured directory position."""

    def group(self, inputs: FrozenInputs, config: HarnessConfig, /) -> GroupedInputs:
        """Return ordered source-index groups matching directory option order."""


class ContextComposer(Protocol):
    """Compose selected context sources, excluding the instructions snapshot."""

    def compose(
        self,
        inputs: FrozenInputs,
        grouped: GroupedInputs,
        config: HarnessConfig,
        /,
    ) -> ComposedContexts:
        """Compose selected source bytes, excluding instructions-file bytes.

        The original frozen inputs provide the bytes for the grouped indices;
        no file reads or hidden state are needed.
        """


class CallScheduler(Protocol):
    """Expand contexts over configured models and efforts in option order."""

    def schedule(
        self, composed: ComposedContexts, config: HarnessConfig, /
    ) -> tuple[PlannedCall, ...]:
        """Return calls with zero-based positions in the complete expansion."""


class PlanBuilder(Protocol):
    """Public pure planning boundary."""

    def plan(self, inputs: FrozenInputs, config: HarnessConfig, /) -> FrozenPlan:
        """Return a plan over the supplied frozen inputs and validated config.

        Leaf implementations may raise ``NotImplementedError`` while planning
        behavior remains unfinished; an empty plan is not a valid substitute.
        """


class _UnimplementedInputGrouper:
    """Phase gate for source grouping until its behavior is implemented."""

    def group(self, inputs: FrozenInputs, config: HarnessConfig, /) -> GroupedInputs:
        """Raise instead of presenting an empty grouping as a valid result."""
        raise NotImplementedError("source grouping is not implemented yet")


class _UnimplementedContextComposer:
    """Phase gate for separator decoding and source-byte composition."""

    def compose(
        self,
        inputs: FrozenInputs,
        grouped: GroupedInputs,
        config: HarnessConfig,
        /,
    ) -> ComposedContexts:
        """Raise until exact context composition has an implementation."""
        raise NotImplementedError(
            "separator decoding and prompt composition are not implemented yet"
        )


class _UnimplementedCallScheduler:
    """Phase gate for ordered context, model, and effort expansion."""

    def schedule(
        self, composed: ComposedContexts, config: HarnessConfig, /
    ) -> tuple[PlannedCall, ...]:
        """Raise until every scheduled position can be constructed."""
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
        """Select pure collaborators and retain the caller's run identity.

        Args:
            run_id: Identity created and owned by the caller.
            grouper: Source-grouping operation, or the unfinished default.
            composer: Context-composition operation, or the unfinished default.
            scheduler: Matrix-expansion operation, or the unfinished default.
        """
        self._run_id = run_id
        self._grouper = grouper if grouper is not None else _UnimplementedInputGrouper()
        self._composer = (
            composer if composer is not None else _UnimplementedContextComposer()
        )
        self._scheduler = (
            scheduler if scheduler is not None else _UnimplementedCallScheduler()
        )

    def plan(self, inputs: FrozenInputs, config: HarnessConfig, /) -> FrozenPlan:
        """Wire grouping, composition, and expansion into an immutable plan.

        Composition receives frozen sources; the instruction snapshot is
        forwarded separately into the plan.
        Errors from leaf operations propagate; unfinished defaults do not
        fabricate an empty plan.

        Returns:
            A plan assembled from caller-supplied identity and collaborators.
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
