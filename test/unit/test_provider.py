# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
from unittest.mock import mock_open, patch

import pytest

from ataraxia.bar import Bar
from ataraxia.provider import BarProvider


@pytest.fixture
def file_contents():
    return """timestamp,open,high,low,close,volume
    1,25.0,55.5,23.25,43.25,10
    """


def test_bar_provider_single_bar(file_contents):
    """Should return a single bar."""
    m = mock_open(read_data=file_contents)
    with patch("builtins.open", m), BarProvider("stub_file_name") as f:
        bar = next(f)

        assert isinstance(bar, Bar)
        assert bar.timestamp == 1
