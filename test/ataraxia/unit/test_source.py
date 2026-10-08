# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Tests for source runner and provider forwarding."""

from collections.abc import Iterator
from types import TracebackType

import pytest

from ataraxia.provider import Provider
from ataraxia.source import SourceNode, SourceRunner


class IntegerProvider(Provider[int]):
    """Provide a typed integer iterator and record context exit arguments."""

    def __init__(self, values: Iterator[int], exit_result: bool | None = False) -> None:
        self._values = values
        self.exit_result = exit_result
        self.entered = 0
        self.exit_args: (
            tuple[
                type[BaseException] | None,
                BaseException | None,
                TracebackType | None,
            ]
            | None
        ) = None

    def __enter__(self) -> IntegerProvider:
        self.entered += 1
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        self.exit_args = (exc_type, exc_value, traceback)
        return self.exit_result

    def __iter__(self) -> IntegerProvider:
        return self

    def __next__(self) -> int:
        return next(self._values)

    def __hash__(self) -> int:
        return object.__hash__(self)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/input/forwarding/README.md", ac="AC-1"
)
def test_source_runner() -> None:
    """Return the item stored by the source node."""
    # Given
    runner = SourceRunner[int]()
    runner.item = 1

    # When
    actual = runner()

    # Then
    assert actual == 1


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/input/forwarding/README.md", ac="AC-1"
)
def test_source_node() -> None:
    """Forward integer items while retaining its provider and runner."""
    # Given
    provider = IntegerProvider(iter((3, 4)))
    source = SourceNode[int](provider)
    runner = source.factory()

    # When
    actual_provider = iter(source)
    source.send(next(actual_provider))
    first = runner()
    source.send(next(actual_provider))
    second = runner()

    # Then
    with pytest.raises(StopIteration):
        next(actual_provider)

    assert actual_provider is provider
    assert source.provider is provider
    assert source.deps() == {}
    assert source.factory() is runner
    assert (first, second) == (3, 4)


@pytest.mark.parametrize(
    "exit_result", [False, True, None], ids=["false", "true", "none"]
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/input/forwarding/README.md", ac="AC-1"
)
def test_source_node_delegates_provider_lifecycle(exit_result: bool | None) -> None:
    """Forward context entry, exact errors, traceback, and exit outcomes."""
    # Given
    provider = IntegerProvider(iter(()), exit_result=exit_result)
    source = SourceNode[int](provider)
    error = RuntimeError("compute failed")

    # When
    entered = source.__enter__()
    none_traceback_result = source.__exit__(RuntimeError, error, None)
    source.__enter__()
    try:
        raise error
    except RuntimeError as caught:
        traceback = caught.__traceback__
        actual_result = source.__exit__(RuntimeError, caught, traceback)

    # Then
    assert entered is source
    assert provider.entered == 2
    assert none_traceback_result is exit_result
    assert actual_result is exit_result
    assert traceback is not None
    assert provider.exit_args == (RuntimeError, error, traceback)
