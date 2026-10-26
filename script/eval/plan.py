# SPDX-License-Identifier: Apache-2.0
"""Pure orchestration boundary for ordered evaluation planning."""

from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
from itertools import pairwise, product
from typing import Protocol

from script.eval.model import (
    DirectoryOption,
    FrozenInputs,
    FrozenPlan,
    HarnessConfig,
    PlannedCall,
    SeparatorOption,
)


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
    """Group frozen source indices by configured directory-option position.

    Sources retain their frozen lexical order within each directory. Repeated
    directory options remain distinct groups, even when their paths are equal.

    Returns:
        Directory-option positions paired with their frozen source indices.
    """
    directory_positions = tuple(
        option.position
        for option in config.ordered_options
        if isinstance(option, DirectoryOption)
    )
    return GroupedInputs(
        snapshots=tuple(
            (
                position,
                tuple(
                    index
                    for index, source in enumerate(inputs.sources)
                    if source.directory_position == position
                ),
            )
            for position in directory_positions
        )
    )


def _compose_contexts(
    inputs: FrozenInputs,
    grouped: GroupedInputs,
    config: HarnessConfig,
    /,
) -> ComposedContexts:
    """Compose every frozen source selection using exact configured boundaries.

    The validated configuration supplies separators between successive
    directory options; omitted separators default to two LF bytes.

    Returns:
        Every source-index selection and its exact composed bytes.
    """
    directory_positions = tuple(position for position, _ in grouped.snapshots)
    separators = _boundary_bytes(config, directory_positions)
    selections = product(*(indices for _, indices in grouped.snapshots))
    prompts = tuple(
        (tuple(indices), _compose_prompt(inputs, indices, separators))
        for indices in selections
    )
    return ComposedContexts(boundary_bytes=separators, prompts=prompts)


def _compose_prompt(
    inputs: FrozenInputs, indices: tuple[int, ...], separators: tuple[bytes, ...]
) -> bytes:
    """Join one selected source from each group with its exact boundary bytes.

    Returns:
        The composed prompt bytes.
    """
    parts: list[bytes] = []
    for index, source_index in enumerate(indices):
        parts.append(inputs.sources[source_index].content)
        if index < len(separators):
            parts.append(separators[index])
    return b"".join(parts)


def _boundary_bytes(
    config: HarnessConfig, directory_positions: tuple[int, ...]
) -> tuple[bytes, ...]:
    """Decode explicit boundary separators, defaulting omitted ones to LF LF.

    Returns:
        One separator byte string for each neighboring directory pair.
    """
    return tuple(
        next(
            (
                _decode_separator(option.value)
                for option in config.ordered_options
                if isinstance(option, SeparatorOption)
                and left < option.position < right
            ),
            b"\n\n",
        )
        for left, right in pairwise(directory_positions)
    )


def _decode_separator(value: str) -> bytes:
    """Decode the four validated separator escapes without altering Unicode.

    Returns:
        UTF-8 bytes for the decoded separator.
    """
    escapes = {"n": "\n", "r": "\r", "t": "\t", "\\": "\\"}
    decoded: list[str] = []
    index = 0
    while index < len(value):
        character = value[index]
        if character != "\\":
            decoded.append(character)
            index += 1
            continue
        decoded.append(escapes[value[index + 1]])
        index += 2
    return "".join(decoded).encode("utf-8")


def _schedule_calls(
    composed: ComposedContexts, config: HarnessConfig, /
) -> tuple[PlannedCall, ...]:
    """Expand contexts, models, and efforts in stable argument order.

    Returns:
        Calls with stable zero-based positions and exact prompt digests.
    """
    calls: list[PlannedCall] = []
    for context_indices, prompt in composed.prompts:
        prompt_sha256 = sha256(prompt).hexdigest()
        for model in config.models:
            for effort in config.efforts:
                calls.append(
                    PlannedCall(
                        position=len(calls),
                        context_indices=context_indices,
                        model=model,
                        effort=effort,
                        prompt_sha256=prompt_sha256,
                        prompt=prompt,
                    )
                )
    return tuple(calls)
