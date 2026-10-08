# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest

from ataraxia.backtest import backtest_dir, backtest_shard
from ataraxia.broker import Account
from ataraxia.errors import BacktestError


@pytest.mark.parametrize(
    "result",
    [
        42,
        {"account": Account(), "open_positions": [], "closed_positions": [object()]},
    ],
    ids=["non-dict", "non-position"],
)
def test_backtest_shard_requires_broker_result(result: object):
    """Should reject a selected sink or consumer result outside the broker contract."""
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
        patch(
            "ataraxia.backtest.compute",
            return_value=({sink: result},),
        ),
        patch("ataraxia.backtest.import_file", return_value=module_mock),
        patch("ataraxia.backtest.is_sink", return_value=True),
        patch("ataraxia.backtest.is_type", return_value=True),
        pytest.raises(BacktestError, match="invalid broker result") as error,
    ):
        backtest_shard("strategy.py", "shard.csv")

    assert "strategy.py" in str(error.value)
    assert "shard.csv" in str(error.value)


def test_backtest_dir_raise_on_wrong_param():
    with pytest.raises(FileNotFoundError):
        backtest_dir("hello", "i do not exist")
