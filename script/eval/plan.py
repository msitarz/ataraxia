# SPDX-License-Identifier: Apache-2.0
"""Pure orchestration boundary for ordered evaluation planning."""

from collections.abc import Callable
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


type GroupInputs = Callable[[FrozenInputs, HarnessConfig], GroupedInputs]
type ComposeContexts = Callable[
    [FrozenInputs, GroupedInputs, HarnessConfig], ComposedContexts
]
type ScheduleCalls = Callable[
    [ComposedContexts, HarnessConfig], tuple[PlannedCall, ...]
]


class PlanBuilder(Protocol):
    """Public pure planning boundary."""

    def plan(self, inputs: FrozenInputs, config: HarnessConfig, /) -> FrozenPlan:
        """Return a plan over the supplied frozen inputs and validated config.

        Leaf implementations may raise ``NotImplementedError`` while planning
        behavior remains unfinished; an empty plan is not a valid substitute.
        """


class PurePlanBuilder(PlanBuilder):
    """Wire pure planning steps and assemble a frozen plan.

    The caller owns and supplies the run identity. Constructing a planner and
    calling it use no clock, random source, filesystem, Git, or model process.
    """

    def __init__(
        self,
        run_id: str,
        *,
        grouper: GroupInputs | None = None,
        composer: ComposeContexts | None = None,
        scheduler: ScheduleCalls | None = None,
    ) -> None:
        """Select pure collaborators and retain the caller's run identity.

        Args:
            run_id: Identity created and owned by the caller.
            grouper: Source-grouping operation, or the unfinished default.
            composer: Context-composition operation, or the unfinished default.
            scheduler: Matrix-expansion operation, or the unfinished default.
        """
        self._run_id = run_id
        self._grouper = grouper if grouper is not None else _group_inputs
        self._composer = composer if composer is not None else _compose_contexts
        self._scheduler = scheduler if scheduler is not None else _schedule_calls

    def plan(self, inputs: FrozenInputs, config: HarnessConfig, /) -> FrozenPlan:
        """Wire grouping, composition, and expansion into an immutable plan.

        Composition receives frozen sources; the instruction snapshot is
        forwarded separately into the plan.
        Errors from leaf operations propagate; unfinished defaults do not
        fabricate an empty plan.

        Returns:
            A plan assembled from caller-supplied identity and collaborators.
        """
        grouped = self._grouper(inputs, config)
        composed = self._composer(inputs, grouped, config)
        calls = self._scheduler(composed, config)
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


def _group_inputs(inputs: FrozenInputs, config: HarnessConfig, /) -> GroupedInputs:
    """Phase gate until frozen sources are grouped by directory position."""
    raise NotImplementedError("source grouping is not implemented yet")


def _compose_contexts(
    inputs: FrozenInputs,
    grouped: GroupedInputs,
    config: HarnessConfig,
    /,
) -> ComposedContexts:
    """Phase gate until separators and selected source bytes are composed."""
    raise NotImplementedError(
        "separator decoding and prompt composition are not implemented yet"
    )


def _schedule_calls(
    composed: ComposedContexts, config: HarnessConfig, /
) -> tuple[PlannedCall, ...]:
    """Phase gate until ordered context, model, and effort calls are expanded."""
    raise NotImplementedError("scheduled call expansion is not implemented yet")
