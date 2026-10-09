# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Tests for source closure and propagated compute errors."""

from dataclasses import dataclass
from types import TracebackType

import pytest

from ataraxia.compute import Sink
from ataraxia.compute.loop import compute
from test.ataraxia.compute_source_inputs import IntegerSource, integer_source_sink


@dataclass(frozen=True)
class FailingRunner:
    """Raise the exact configured error after receiving a source item."""

    error: RuntimeError

    def __call__(self, item: int) -> int:
        raise self.error


@dataclass(frozen=True)
class FailingSink(Sink[[int], int]):
    """Run a failing runner through one injected source."""

    source: IntegerSource
    error: RuntimeError

    def deps(self) -> dict[str, IntegerSource]:
        return {"item": self.source}

    def factory(self) -> FailingRunner:
        return FailingRunner(self.error)

    def sources(self) -> tuple[IntegerSource, ...]:
        return (self.source,)

    def consumer(self) -> None:
        return None


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/compute/lifecycle/README.md",
    ac="AC-1",
)
def test_compute_closes_source_on_exhaustion() -> None:
    """Exhaust compute and verify both complete steps and source closure."""
    # Given
    sink, source = integer_source_sink()

    # When
    actual = list(compute(sink))

    # Then
    assert actual == [
        {source: 1, sink: 8},
        {source: 3, sink: 10},
    ]
    assert source.context.is_closed
    assert not source.context.is_open
    assert source.context.exit_args == (None, None, None)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/compute/lifecycle/README.md",
    ac="AC-1",
)
def test_compute_closes_source_when_runner_raises() -> None:
    """Propagate the exact sink error and close the source with its traceback."""
    # Given
    source = IntegerSource()
    failure = RuntimeError("sink runner failed")
    sink = FailingSink(source, failure)

    # When
    with pytest.raises(RuntimeError) as error:
        next(compute(sink))

    # Then
    assert error.value is failure
    assert str(error.value) == "sink runner failed"
    assert source.context.is_closed
    assert not source.context.is_open
    exit_args = source.context.exit_args
    assert exit_args is not None
    exc_type, exc_value, traceback = exit_args
    assert exc_type is RuntimeError
    assert exc_value is failure
    assert type(exc_value) is RuntimeError
    assert isinstance(traceback, TracebackType)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/compute/lifecycle/README.md",
    ac="AC-1",
)
def test_compute_closes_source_when_generator_is_closed() -> None:
    """Close compute after one result and verify GeneratorExit reaches source."""
    # Given
    sink, source = integer_source_sink()
    computed = compute(sink)

    # When
    first = next(computed)
    computed.close()

    # Then
    assert first == {source: 1, sink: 8}
    assert source.context.is_closed
    assert not source.context.is_open
    exit_args = source.context.exit_args
    assert exit_args is not None
    exc_type, exc_value, traceback = exit_args
    assert exc_type is GeneratorExit
    assert type(exc_value) is GeneratorExit
    assert isinstance(traceback, TracebackType)
