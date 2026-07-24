# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

from unittest.mock import MagicMock, patch

import pytest

from ataraxia.backtest import backtest_dir, backtest_shard
from ataraxia.errors import ModuleError


def test_backtest_shard_raise_on_invalid_module():
    """Should raise when provided invalid module."""
    mock = MagicMock(return_value="not a valid module")

    with pytest.raises(ModuleError), patch("ataraxia.util.import_file", mock):
        backtest_shard("i do not exist", "i do not exist")


def test_backtest_dir_raise_on_wrong_param():
    with pytest.raises(FileNotFoundError):
        backtest_dir("hello", "i do not exist")
