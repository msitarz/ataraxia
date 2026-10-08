# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
import textwrap
from unittest.mock import mock_open, patch

import pytest

from ataraxia.errors import ProviderError
from ataraxia.provider import BarProvider


@pytest.fixture
def no_header():
    txt = """1,2,3,4,5,6
    1,25.0,55.5,23.25,43.25,10
    """

    return textwrap.dedent(txt)


@pytest.fixture
def wrong_header():
    txt = """timing,open,high,low,close,volume
    1,25.0,55.5,23.25,43.25,10
    """

    return textwrap.dedent(txt)


def test_bar_provider_no_header(no_header):
    """Should raise when file doesn't have a header."""
    m = mock_open(read_data=no_header)
    with (
        patch("builtins.open", m),
        BarProvider("stub_file_name") as f,
        pytest.raises(ProviderError),
    ):
        next(f)


def test_bar_provider_wrong_header(wrong_header):
    """Should raise when file have a wrong header."""
    m = mock_open(read_data=wrong_header)
    with (
        patch("builtins.open", m),
        BarProvider("stub_file_name") as f,
        pytest.raises(ProviderError),
    ):
        next(f)


def test_bar_provider_no_context_manager():
    """Should raise when used outside of context manager."""
    with pytest.raises(ProviderError):
        next(BarProvider("stub_file_name"))


@pytest.mark.parametrize(
    "row",
    ["1,100", "1,100,200,50,150,1,extra", "1,bad,200,50,150,1", "1,,200,50,150,1"],
    ids=["missing-columns", "extra-columns", "non-numeric", "empty-value"],
)
def test_bar_provider_rejects_malformed_rows_and_closes(tmp_path, row):
    shard = tmp_path / "invalid.csv"
    shard.write_text(f"timestamp,open,high,low,close,volume\n{row}\n")
    provider = BarProvider(shard)

    with pytest.raises(ProviderError, match="Invalid bar") as error, provider:
        next(provider)

    assert str(shard) in str(error.value)
    assert isinstance(error.value.__cause__, ValueError)
    assert provider.fd.closed


def test_bar_provider_rejects_unterminated_quote(tmp_path):
    import csv

    shard = tmp_path / "invalid.csv"
    shard.write_text('timestamp,open,high,low,close,volume\n1,"100,200,50,150,1\n')
    provider = BarProvider(shard)

    with pytest.raises(ProviderError, match="Invalid bar") as error, provider:
        next(provider)

    assert isinstance(error.value.__cause__, csv.Error)
    assert str(shard) in str(error.value)
    assert provider.fd.closed
