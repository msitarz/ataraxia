# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Test precise runtime dependency binding and preparation behavior."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, override

import pytest

from ataraxia.compute import Computable, Runner
from ataraxia.compute.loop import compute, compute_step, prime_catalog
from test.ataraxia.compute_dependency_inputs import B
from test.ataraxia.compute_source_inputs import (
    IntegerSink,
    IntegerSource,
    integer_source_sink,
)

if TYPE_CHECKING:
    from ataraxia.bar import Bar


@dataclass(frozen=True)
class RequiredItemRunner:
    """Accept one required keyword named item."""

    def __call__(self, item: int) -> int:
        return item


@dataclass(frozen=True)
class PositionalOnlyItemRunner:
    """Accept item positionally but reject it as a dependency keyword."""

    def __call__(self, item: int, /) -> int:
        return item


@dataclass(frozen=True)
class KeywordOnlyItemRunner:
    """Accept item as a required keyword-only dependency."""

    def __call__(self, *, item: int) -> int:
        return item


@dataclass(frozen=True)
class DefaultItemRunner:
    """Accept item as an optional keyword dependency."""

    def __call__(self, item: int = 1) -> int:
        return item


@dataclass(frozen=True)
class ArbitraryKeywordRunner:
    """Accept the named arbitrary dependency supplied by its node."""

    def __call__(self, **kwargs: int) -> int:
        return kwargs["arbitrary"]


@dataclass(frozen=True)
class PositionalArgsRunner:
    """Accept an empty dependency mapping through variadic positional args."""

    def __call__(self, *args: int) -> int:
        return len(args)


@dataclass(frozen=True)
class SignatureNode[R: Runner[..., int]]:
    """Pair a signature-specific runner with its precise dependency mapping."""

    runner: R
    dependencies: dict[str, Computable[..., int]] = field(compare=False, hash=False)

    def deps(self) -> dict[str, Computable[..., int]]:
        return self.dependencies

    def factory(self) -> R:
        return self.runner


@dataclass(frozen=True)
class MisspelledWiringSink(IntegerSink):
    """Expose a bad dependency key for pre-entry preparation coverage."""

    @override
    def deps(self) -> dict[str, IntegerSource]:
        return {"itme": self.source}


@dataclass(frozen=True)
class UninspectableRunnerNode:
    """Return builtin int, whose callable signature cannot be inspected."""

    def deps(self) -> dict[str, Computable[..., int]]:
        return {}

    def factory(self) -> type[int]:
        return int


@dataclass(frozen=True)
class TypeOnlyAnnotationRunner:
    """Return a result without evaluating its TYPE_CHECKING-only Bar annotation."""

    def __call__(self, item: Bar | None = None) -> int:
        return 7


@dataclass(frozen=True)
class TypeOnlyAnnotationNode:
    """Expose the annotation-only runner through normal node preparation."""

    runner: TypeOnlyAnnotationRunner = field(default_factory=TypeOnlyAnnotationRunner)

    def deps(self) -> dict[str, Computable[..., int]]:
        return {}

    def factory(self) -> TypeOnlyAnnotationRunner:
        return self.runner


INVALID_SIGNATURE_CASES: tuple[
    tuple[
        SignatureNode[RequiredItemRunner] | SignatureNode[PositionalOnlyItemRunner],
        str,
    ],
    ...,
] = (
    (
        SignatureNode(RequiredItemRunner(), {"itme": B()}),
        "missing a required argument: 'item'",
    ),
    (SignatureNode(RequiredItemRunner(), {}), "missing a required argument: 'item'"),
    (
        SignatureNode(
            RequiredItemRunner(),
            {"item": B(), "extra": B()},
        ),
        "got an unexpected keyword argument 'extra'",
    ),
    (
        SignatureNode(PositionalOnlyItemRunner(), {"item": B()}),
        "missing a required positional-only argument: 'item'",
    ),
)

VALID_SIGNATURE_NODES: tuple[
    SignatureNode[KeywordOnlyItemRunner]
    | SignatureNode[DefaultItemRunner]
    | SignatureNode[ArbitraryKeywordRunner]
    | SignatureNode[PositionalArgsRunner],
    ...,
] = (
    SignatureNode(KeywordOnlyItemRunner(), {"item": B()}),
    SignatureNode(DefaultItemRunner(), {}),
    SignatureNode(ArbitraryKeywordRunner(), {"arbitrary": B()}),
    SignatureNode(PositionalArgsRunner(), {}),
)


@pytest.mark.parametrize(
    ("node", "cause_reason"),
    INVALID_SIGNATURE_CASES,
    ids=[
        "<lambda>-names0",
        "<lambda>-names1",
        "<lambda>-names2",
        "<lambda>-names3",
    ],
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/compute/binding/README.md",
    ac="AC-1",
)
def test_invalid_dependency_names_fail_preparation(
    node: SignatureNode[RequiredItemRunner] | SignatureNode[PositionalOnlyItemRunner],
    cause_reason: str,
) -> None:
    """Refuse malformed dependency names with their precise bind errors."""
    from ataraxia.errors import DependencyError

    # Given
    expected_reason = cause_reason

    # When
    with pytest.raises(DependencyError, match="Invalid dependencies") as error:
        prime_catalog((node,))

    # Then
    assert type(error.value.__cause__) is TypeError
    assert str(error.value.__cause__) == expected_reason


@pytest.mark.parametrize(
    "node",
    VALID_SIGNATURE_NODES,
    ids=[
        "<lambda>-names0",
        "<lambda>-names1",
        "<lambda>-names2",
        "<lambda>-names3",
    ],
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/compute/binding/README.md",
    ac="AC-1",
)
def test_valid_dependency_signatures(
    node: (
        SignatureNode[KeywordOnlyItemRunner]
        | SignatureNode[DefaultItemRunner]
        | SignatureNode[ArbitraryKeywordRunner]
        | SignatureNode[PositionalArgsRunner]
    ),
) -> None:
    """Accept keyword-only, defaulted, variadic keyword and positional runners."""
    # Given
    expected_runner = node.factory()

    # When
    catalog = prime_catalog((node,))

    # Then
    assert catalog[node] is expected_runner


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/compute/binding/README.md",
    ac="AC-1",
)
def test_wiring_failure_precedes_source_entry() -> None:
    """Reject bad wiring before entering the faithful integer source."""
    from ataraxia.errors import DependencyError

    # Given
    _, source = integer_source_sink()
    sink = MisspelledWiringSink(source)

    # When
    with pytest.raises(DependencyError, match="Invalid dependencies") as error:
        next(compute(sink))

    # Then
    assert type(error.value.__cause__) is TypeError
    assert str(error.value.__cause__) == "missing a required argument: 'item'"
    assert not source.context.is_open
    assert not source.context.is_closed
    assert source.context.exit_args is None


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/compute/binding/README.md",
    ac="AC-1",
)
def test_uninspectable_runner_fails_preparation() -> None:
    """Report the exact signature-inspection failure for builtin int."""
    from ataraxia.errors import DependencyError

    # Given
    node = UninspectableRunnerNode()

    # When
    with pytest.raises(DependencyError, match="Invalid dependencies") as error:
        prime_catalog((node,))

    # Then
    assert type(error.value.__cause__) is ValueError
    assert str(error.value.__cause__) == (
        "no signature found for builtin type <class 'int'>"
    )


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/compute/binding/README.md",
    ac="AC-1",
)
def test_preparation_does_not_evaluate_type_only_annotations() -> None:
    """Prepare a runner whose optional Bar annotation is type-only."""
    # Given
    node = TypeOnlyAnnotationNode()

    # When
    catalog = prime_catalog((node,))

    # Then
    assert compute_step((node,), catalog)[node] == 7
