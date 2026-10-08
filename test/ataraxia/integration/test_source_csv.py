# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Real provider resources across source context lifetimes."""

from io import TextIOBase
from pathlib import Path

import pytest

from ataraxia.bar import Bar
from ataraxia.provider import BarProvider
from ataraxia.source import SourceNode


@pytest.fixture
def two_bar_shard(tmp_path: Path) -> Path:
    shard = tmp_path / "bars.csv"
    shard.write_text(
        "timestamp,open,high,low,close,volume\n"
        "1,25.0,55.5,23.25,43.25,10\n"
        "2,30,40,10,35,20\n",
        encoding="utf-8",
    )
    return shard


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/input/contexts/README.md", ac="AC-1"
)
def test_source_csv_context_closes_after_exhaustion(two_bar_shard: Path) -> None:
    """Exhaustion forwards both complete Bars and closes the real file."""
    # Given
    provider = BarProvider(two_bar_shard)
    source = SourceNode[Bar](provider)
    runner = source.factory()
    expected = [
        Bar(timestamp=1, open=100, high=222, low=93, close=173, volume=10),
        Bar(timestamp=2, open=30, high=40, low=10, close=35, volume=20),
    ]
    actual: list[Bar] = []
    opened_file: TextIOBase | None = None

    # When
    with source:
        opened_file = provider.fd
        assert opened_file is not None
        assert iter(source) is provider
        assert source.factory() is runner
        for bar in source:
            source.send(bar)
            actual.append(runner())

    # Then
    assert actual == expected
    assert opened_file is not None
    assert opened_file.closed


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/input/contexts/README.md", ac="AC-1"
)
def test_source_csv_context_closes_after_body_error(two_bar_shard: Path) -> None:
    """A body error propagates by identity after the real file closes."""
    # Given
    provider = BarProvider(two_bar_shard)
    source = SourceNode[Bar](provider)
    runner = source.factory()
    expected = Bar(timestamp=1, open=100, high=222, low=93, close=173, volume=10)
    body_error = RuntimeError("stop source body")
    opened_file: TextIOBase | None = None

    # When
    with pytest.raises(RuntimeError) as error, source:
        opened_file = provider.fd
        assert opened_file is not None
        first = next(iter(source))
        source.send(first)
        assert runner() == expected
        raise body_error

    # Then
    assert error.value is body_error
    assert opened_file is not None
    assert opened_file.closed


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/input/contexts/README.md", ac="AC-1"
)
def test_source_csv_context_closes_on_early_exit(two_bar_shard: Path) -> None:
    """Early scope exit sends the first Bar and closes with another row unread."""
    # Given
    provider = BarProvider(two_bar_shard)
    source = SourceNode[Bar](provider)
    runner = source.factory()
    expected = Bar(timestamp=1, open=100, high=222, low=93, close=173, volume=10)
    opened_file: TextIOBase | None = None

    # When
    with source:
        opened_file = provider.fd
        assert opened_file is not None
        first = next(iter(source))
        source.send(first)
        actual = runner()

    # Then
    assert actual == expected
    assert opened_file is not None
    assert opened_file.closed
