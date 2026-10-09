# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Verify compute closes real CSV-backed provider resources."""

from dataclasses import dataclass, field
from io import TextIOBase
from pathlib import Path

import pytest

from ataraxia.bar import Bar
from ataraxia.compute import Sink
from ataraxia.compute.loop import compute
from ataraxia.provider import BarProvider
from ataraxia.source import SourceNode
from test.ataraxia.compute_source_inputs import two_bar_csv_source

FIRST_BAR = Bar(timestamp=1, open=100, high=102, low=99, close=101, volume=10)
SECOND_BAR = Bar(timestamp=2, open=104, high=108, low=103, close=106, volume=20)


@dataclass(frozen=True)
class CloseRunner:
    """Return each actual input bar's close through compute."""

    def __call__(self, item: Bar) -> int:
        return item.close


@dataclass(frozen=True)
class CloseSink(Sink[[Bar], int]):
    """Consume a real CSV source and expose each bar's close."""

    source: SourceNode[Bar]

    def deps(self) -> dict[str, SourceNode[Bar]]:
        return {"item": self.source}

    def factory(self) -> CloseRunner:
        return CloseRunner()

    def sources(self) -> tuple[SourceNode[Bar], ...]:
        return (self.source,)

    def consumer(self) -> None:
        return None


@dataclass
class FailureObservation:
    """Record the bar delivered to the runner before it raises."""

    item: Bar | None = None
    opened_file: TextIOBase | None = None
    was_open: bool | None = None


@dataclass(frozen=True)
class FailingRunner:
    """Record one real input bar and raise the configured error object."""

    error: RuntimeError
    observation: FailureObservation
    provider: BarProvider

    def __call__(self, item: Bar) -> int:
        self.observation.item = item
        opened_file = self.provider.fd
        self.observation.opened_file = opened_file
        if opened_file is not None:
            self.observation.was_open = not opened_file.closed
        raise self.error


@dataclass(frozen=True)
class FailingSink(Sink[[Bar], int]):
    """Raise from a sink after the real provider has yielded a bar."""

    source: SourceNode[Bar]
    runner: FailingRunner = field(compare=False, hash=False)

    def deps(self) -> dict[str, SourceNode[Bar]]:
        return {"item": self.source}

    def factory(self) -> FailingRunner:
        return self.runner

    def sources(self) -> tuple[SourceNode[Bar], ...]:
        return (self.source,)

    def consumer(self) -> None:
        return None


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/compute/resources/README.md",
    ac="AC-1",
)
def test_compute_closes_csv_provider_after_exhaustion(tmp_path: Path) -> None:
    """Exhaust real CSV computation and verify both complete steps and file closure."""
    # Given
    source, provider = two_bar_csv_source(tmp_path / "bars.csv")
    sink = CloseSink(source)
    expected = [
        {source: FIRST_BAR, sink: 101},
        {source: SECOND_BAR, sink: 106},
    ]
    computed = compute(sink)

    # When
    first = next(computed)
    opened_file: TextIOBase | None = provider.fd
    assert opened_file is not None
    assert not opened_file.closed
    actual = [first, *computed]

    # Then
    assert actual == expected
    assert opened_file.closed


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/compute/resources/README.md",
    ac="AC-1",
)
def test_compute_closes_csv_provider_after_runner_error(tmp_path: Path) -> None:
    """Propagate the exact sink error and close the real file after a bar arrives."""
    # Given
    source, provider = two_bar_csv_source(tmp_path / "bars.csv")
    failure = RuntimeError("CSV sink runner failed")
    observation = FailureObservation()
    sink = FailingSink(source, FailingRunner(failure, observation, provider))

    # When
    with pytest.raises(RuntimeError) as error:
        next(compute(sink))

    # Then
    opened_file = observation.opened_file
    assert error.value is failure
    assert str(error.value) == "CSV sink runner failed"
    assert observation.item == FIRST_BAR
    assert opened_file is not None
    assert opened_file is provider.fd
    assert observation.was_open is True
    assert opened_file.closed


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/compute/resources/README.md",
    ac="AC-1",
)
def test_compute_close_closes_csv_provider_with_row_unread(tmp_path: Path) -> None:
    """Close compute after the first of two real bars and verify provider closure."""
    # Given
    source, provider = two_bar_csv_source(tmp_path / "bars.csv")
    sink = CloseSink(source)
    computed = compute(sink)

    # When
    first = next(computed)
    opened_file: TextIOBase | None = provider.fd
    assert opened_file is not None
    assert not opened_file.closed
    computed.close()

    # Then
    assert first == {source: FIRST_BAR, sink: 101}
    assert list(computed) == []
    assert opened_file.closed
