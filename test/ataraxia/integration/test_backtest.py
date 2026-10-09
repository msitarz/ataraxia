# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

from pathlib import Path
from unittest.mock import patch

import pytest

from ataraxia.backtest import BacktestShardReturn, backtest_shard
from ataraxia.broker import Account, BrokerReturn, Signal


@pytest.fixture
def strategy_and_shard_path(tmp_path: Path):
    shard = tmp_path / "shard.csv"
    strategy = tmp_path / "strategy.py"

    shard.write_text("timestamp,open,high,low,close,volume\n1,100,200,50,150,1\n")

    strategy.write_text(
        "\n".join([
            "from dataclasses import dataclass",
            "from ataraxia.broker import Broker, Signal",
            "from ataraxia.source import SourceNode",
            "",
            "class StrategyRunner:",
            "    def __call__(self, item):",
            "        return Signal(side='buy', stop_loss=100, take_profit=200)",
            "",
            "@dataclass(frozen=True)",
            "class Strategy:",
            "    source: SourceNode",
            "    def deps(self):",
            "        return {'item': self.source}",
            "    def factory(self):",
            "        return StrategyRunner()",
            "    def consumer(self):",
            "        return Broker(self.source, self)",
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


@pytest.fixture
def broker_result() -> BrokerReturn:
    return {
        "account": Account(),
        "open_positions": [],
        "closed_positions": [],
    }


def test_backtest_shard_uses_broker_result_from_compute_step(
    strategy_and_shard_path, broker_result
):
    """Should select the consumer result instead of the final mapping entry."""
    shard = strategy_and_shard_path["shard"]
    strategy = strategy_and_shard_path["strategy"]

    expected: BacktestShardReturn = {
        **broker_result,
        "shard_path": str(shard.resolve()),
        "strategy_path": str(strategy.resolve()),
    }

    def fake_compute(sink):
        yield {
            sink.consumer(): broker_result,
            sink: Signal(side="buy", stop_loss=100, take_profit=200),
        }

    with patch("ataraxia.backtest.compute", fake_compute):
        result = backtest_shard(strategy, shard)

        assert result == expected
