# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
import textwrap
from unittest.mock import mock_open, patch

import pytest

from ataraxia.bar import Bar
from ataraxia.errors import ProviderError
from ataraxia.provider import BarProvider


@pytest.fixture
def file_contents():
    txt = """timestamp,open,high,low,close,volume
    1,25.0,55.5,23.25,43.25,10
    """

    return textwrap.dedent(txt)


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


def test_bar_provider_single_bar(file_contents):
    """Should return a single bar."""
    m = mock_open(read_data=file_contents)
    with patch("builtins.open", m), BarProvider("stub_file_name") as f:
        bar = next(f)

        assert isinstance(bar, Bar)
        assert bar.timestamp == 1


def test_bar_provider_stop_iteration(file_contents):
    """Should raise StopIteration when no more data."""
    m = mock_open(read_data=file_contents)
    with (
        patch("builtins.open", m),
        BarProvider("stub_file_name") as f,
        pytest.raises(StopIteration),
    ):
        next(f)
        next(f)


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


def test_provider_no_context_manager():
    """Should raise when used outside of context manager."""
    with pytest.raises(ProviderError):
        next(BarProvider("stub_file_name"))
