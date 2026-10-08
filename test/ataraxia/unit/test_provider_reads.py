# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Real-file tests for BarProvider reads and exhaustion."""

from pathlib import Path
import textwrap

import pytest

from ataraxia.bar import Bar
from ataraxia.provider import BarProvider


@pytest.fixture
def file_contents() -> str:
    txt = """timestamp,open,high,low,close,volume
    1,25.0,55.5,23.25,43.25,10
    """

    return textwrap.dedent(txt)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/input/reads/README.md", ac="AC-1"
)
def test_bar_provider_single_bar(tmp_path: Path, file_contents: str) -> None:
    """Covers AC-1: decimal CSV prices normalize into a complete literal Bar."""
    # Given
    shard = tmp_path / "single.csv"
    shard.write_text(file_contents, encoding="utf-8")
    provider = BarProvider(shard)
    expected = Bar(timestamp=1, open=100, high=222, low=93, close=173, volume=10)

    # When
    with provider:
        actual = next(provider)

    # Then
    assert actual == expected
    assert provider.fd is not None
    assert provider.fd.closed


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/input/reads/README.md", ac="AC-1"
)
def test_bar_provider_stop_iteration(tmp_path: Path, file_contents: str) -> None:
    """Covers AC-1: the single retained row is followed by exact exhaustion."""
    # Given
    shard = tmp_path / "single.csv"
    shard.write_text(file_contents, encoding="utf-8")
    provider = BarProvider(shard)
    expected = Bar(timestamp=1, open=100, high=222, low=93, close=173, volume=10)

    # When
    with provider:
        first_bar = next(provider)

        # Then
        assert first_bar == expected

        # When
        with pytest.raises(StopIteration):
            next(provider)

    # Then
    assert provider.fd is not None
    assert provider.fd.closed


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/input/reads/README.md", ac="AC-1"
)
def test_bar_provider_header_only_exhausts_and_closes(tmp_path: Path) -> None:
    """Covers AC-1: a header-only CSV yields no rows and closes after exit."""
    # Given
    shard = tmp_path / "empty.csv"
    shard.write_text("timestamp,open,high,low,close,volume\n", encoding="utf-8")
    provider = BarProvider(shard)

    # When
    with provider:
        actual = list(provider)

    # Then
    assert actual == []
    assert provider.fd is not None
    assert provider.fd.closed


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/input/reads/README.md", ac="AC-1"
)
def test_bar_provider_skips_blank_rows(tmp_path: Path) -> None:
    """Covers AC-1: blank lines are skipped while integer CSV prices stay intact."""
    # Given
    shard = tmp_path / "bars.csv"
    shard.write_text(
        "timestamp,open,high,low,close,volume\n\n"
        "1,100,200,50,150,1\n\n2,100,200,50,150,1\n\n",
        encoding="utf-8",
    )
    provider = BarProvider(shard)
    expected = [
        Bar(timestamp=1, open=100, high=200, low=50, close=150, volume=1),
        Bar(timestamp=2, open=100, high=200, low=50, close=150, volume=1),
    ]

    # When
    with provider:
        actual = list(provider)

    # Then
    assert actual == expected
    assert provider.fd is not None
    assert provider.fd.closed


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/input/reads/README.md", ac="AC-1"
)
def test_bar_provider_hashable_by_filepath() -> None:
    """Covers AC-1: providers with equal filepaths have equal hashes."""
    # Given
    first = BarProvider("dummy_file_name")
    second = BarProvider("dummy_file_name")

    # When
    first_hash = hash(first)
    second_hash = hash(second)

    # Then
    assert first_hash == second_hash
