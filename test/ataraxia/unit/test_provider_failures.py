# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Real-file tests for BarProvider's contextual failures."""

import csv
from pathlib import Path

import pytest

from ataraxia.errors import ProviderError
from ataraxia.provider import BarProvider


@pytest.fixture
def no_header() -> str:
    return """1,2,3,4,5,6
1,25.0,55.5,23.25,43.25,10
"""


@pytest.fixture
def wrong_header() -> str:
    return """timing,open,high,low,close,volume
1,25.0,55.5,23.25,43.25,10
"""


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/input/failures/README.md", ac="AC-1"
)
def test_bar_provider_no_header(tmp_path: Path, no_header: str) -> None:
    """Covers AC-1: a numeric first row is rejected as a missing header."""
    # Given
    shard = tmp_path / "no-header.csv"
    shard.write_text(no_header, encoding="utf-8")
    provider = BarProvider(shard)

    # When
    with provider, pytest.raises(ProviderError) as error:
        next(provider)

    # Then
    assert str(error.value) == f"CSV file must contain a header: {shard}"
    assert error.value.__cause__ is None
    assert provider.fd is not None
    assert provider.fd.closed


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/input/failures/README.md", ac="AC-1"
)
def test_bar_provider_wrong_header(tmp_path: Path, wrong_header: str) -> None:
    """Covers AC-1: a noncanonical header is rejected with its filepath."""
    # Given
    shard = tmp_path / "wrong-header.csv"
    shard.write_text(wrong_header, encoding="utf-8")
    provider = BarProvider(shard)

    # When
    with provider, pytest.raises(ProviderError) as error:
        next(provider)

    # Then
    assert str(error.value) == f"CSV file must contain a header: {shard}"
    assert error.value.__cause__ is None
    assert provider.fd is not None
    assert provider.fd.closed


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/input/failures/README.md", ac="AC-1"
)
def test_bar_provider_no_context_manager() -> None:
    """Covers AC-1: iteration outside a context raises without opening a file."""
    # Given
    provider = BarProvider("stub_file_name")

    # When
    with pytest.raises(ProviderError) as error:
        next(provider)

    # Then
    assert str(error.value) == "Use provider as context manager"
    assert error.value.__cause__ is None
    assert provider.fd is None


@pytest.mark.parametrize(
    ("row", "distinctive_reason"),
    [
        ("1,100", "shorter than"),
        ("1,100,200,50,150,1,extra", "longer than"),
        ("1,bad,200,50,150,1", "'bad'"),
        ("1,,200,50,150,1", "''"),
    ],
    ids=["missing-columns", "extra-columns", "non-numeric", "empty-value"],
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/input/failures/README.md", ac="AC-1"
)
def test_bar_provider_rejects_malformed_rows_and_closes(
    tmp_path: Path, row: str, distinctive_reason: str
) -> None:
    """Covers AC-1: malformed rows retain contextual reasons and causes."""
    # Given
    shard = tmp_path / "invalid.csv"
    shard.write_text(f"timestamp,open,high,low,close,volume\n{row}\n", encoding="utf-8")
    provider = BarProvider(shard)

    # When
    with provider, pytest.raises(ProviderError) as error:
        next(provider)

    # Then
    message_prefix = f"Invalid bar in shard {shard}: "
    assert str(error.value).startswith(message_prefix)
    assert distinctive_reason in str(error.value)
    assert isinstance(error.value.__cause__, ValueError)
    assert provider.fd is not None
    assert provider.fd.closed


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/input/failures/README.md", ac="AC-1"
)
def test_bar_provider_rejects_unterminated_quote(tmp_path: Path) -> None:
    """Covers AC-1: unterminated quoting preserves the parser cause and closure."""
    # Given
    shard = tmp_path / "invalid.csv"
    shard.write_text(
        'timestamp,open,high,low,close,volume\n1,"100,200,50,150,1\n',
        encoding="utf-8",
    )
    provider = BarProvider(shard)

    # When
    with provider, pytest.raises(ProviderError) as error:
        next(provider)

    # Then
    message_prefix = f"Invalid bar in shard {shard}: "
    assert str(error.value).startswith(message_prefix)
    assert "unexpected end of data" in str(error.value)
    assert isinstance(error.value.__cause__, csv.Error)
    assert provider.fd is not None
    assert provider.fd.closed
