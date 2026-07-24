# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from ataraxia.backtest import backtest_dir, backtest_shard
from ataraxia.errors import ModuleError


def test_backtest_shard_include_shard_path_strategy_path(tmp_path: Path):
    """Should raise when provided invalid module."""
    module_mock = MagicMock()

    @dataclass(frozen=True)
    class S:
        def __init__(self, _source):
            return None

        def consumer(self):
            return None

    sink = S(0)
    module_mock.configure_mock(__sink__=S)

    with (
        patch("ataraxia.backtest.compute", return_value=({sink: {}},)),
        patch("ataraxia.backtest.import_file", return_value=module_mock),
        patch("ataraxia.backtest.is_sink", return_value=True),
        patch("ataraxia.backtest.is_type", return_value=True),
        patch("builtins.open", mock_open()),
    ):
        result = backtest_shard("somefile.py", "somedir")

        assert result.get("shard_path")
        assert result.get("strategy_path")


def test_backtest_shard_raise_on_invalid_module():
    """Should raise when provided invalid module."""
    mock = MagicMock(return_value="not a valid module")

    with pytest.raises(ModuleError), patch("ataraxia.util.import_file", mock):
        backtest_shard("i do not exist", "i do not exist")


def test_backtest_dir_raise_on_wrong_param():
    with pytest.raises(FileNotFoundError):
        backtest_dir("hello", "i do not exist")
