# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

from pathlib import Path
from unittest.mock import patch

import pytest

from ataraxia.backtest import backtest_dir, backtest_shard


@pytest.fixture
def strategy_and_shard_path(tmp_path: Path):
    shard = tmp_path / "shard.csv"
    strategy = tmp_path / "strategy.py"

    shard.write_text("timestamp,open,high,low,close,volume\n1,100,200,50,150,1\n")

    strategy.write_text(
        "\n".join([
            "from dataclasses import dataclass",
            "from ataraxia.source import SourceNode",
            "",
            "class StrategyRunner:",
            "    def __call__(self, item):",
            "        return item.close",
            "",
            "@dataclass(frozen=True)",
            "class Strategy:",
            "    source: SourceNode",
            "    def deps(self):",
            "        return {'item': self.source}",
            "    def factory(self):",
            "        return StrategyRunner()",
            "    def consumer(self):",
            "        return None",
            "    def sources(self):",
            "        return (self.source,)",
            "",
            "__sink__ = Strategy",
        ])
    )

    return {
        "shard": shard,
        "strategy": strategy,
    }


def test_backtest_shard(strategy_and_shard_path):
    """Should process provided strategy via provided shard."""
    shard = strategy_and_shard_path["shard"]
    strategy = strategy_and_shard_path["strategy"]

    result = backtest_shard(strategy, shard)

    assert result == 150


def test_backtest_shard_reordered_compute_results_dict(strategy_and_shard_path):
    """Should return sink values if compute results dict is not in order."""
    shard = strategy_and_shard_path["shard"]
    strategy = strategy_and_shard_path["strategy"]

    def fake_compute(sink):
        yield {sink: 150, "last_key_in_order": "wrong value"}

    with patch("ataraxia.backtest.compute", fake_compute):
        result = backtest_shard(strategy, shard)

        assert result == 150


def test_backtest_dir(tmp_path: Path):
    """Should process all files in the dir and return values."""

    file_1 = tmp_path / "file_1.py"
    file_2 = tmp_path / "file_2.py"

    file_1.write_text("")
    file_2.write_text("")

    with patch("ataraxia.backtest.backtest_shard", return_value=3):
        results = backtest_dir("i do not exist", tmp_path)

        assert results == (3, 3)
