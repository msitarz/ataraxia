# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

from pathlib import Path
from unittest.mock import patch

import pytest

from ataraxia.backtest import BacktestShardReturn, backtest_dir, backtest_shard
from ataraxia.bar import Bar
from ataraxia.broker import Account, BrokerReturn, Position, Signal


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
    return {"account": Account(), "open_positions": [], "closed_positions": []}


def expected_backtest_result(shard: Path, strategy: Path) -> BacktestShardReturn:
    """Return the complete broker result expected from the fixture strategy."""
    return {
        "status": "success",
        "result": {
            "account": Account(),
            "open_positions": [
                Position(
                    side="buy",
                    stop_loss=100,
                    take_profit=200,
                    entry_bar=Bar(
                        timestamp=1,
                        open=100,
                        high=200,
                        low=50,
                        close=150,
                        volume=1,
                    ),
                )
            ],
            "closed_positions": [],
        },
        "shard_path": str(shard.resolve()),
        "strategy_path": str(strategy.resolve()),
    }


def test_backtest_shard(strategy_and_shard_path):
    """Should process provided strategy via provided shard."""
    shard = strategy_and_shard_path["shard"]
    strategy = strategy_and_shard_path["strategy"]

    result = backtest_shard(strategy, shard)

    assert result == expected_backtest_result(shard, strategy)


def test_backtest_header_only_shard(strategy_and_shard_path):
    shard = strategy_and_shard_path["shard"]
    shard.write_text("timestamp,open,high,low,close,volume\n")

    outcome = backtest_shard(strategy_and_shard_path["strategy"], shard)
    assert outcome["status"] == "error"
    assert "contains no bars" in outcome["error"]["message"]
    assert str(shard) in outcome["error"]["message"]


def test_backtest_shard_requires_sink_export(strategy_and_shard_path):
    """A loadable strategy without __sink__ should raise a contextual domain error."""
    strategy = strategy_and_shard_path["strategy"]
    strategy.write_text(strategy.read_text().replace("__sink__ = Strategy", ""))

    outcome = backtest_shard(strategy, strategy_and_shard_path["shard"])
    assert outcome["status"] == "error"
    assert "__sink__" in outcome["error"]["message"]
    assert str(strategy) in outcome["error"]["message"]
    assert "AttributeError" in outcome["error"]["traceback"]


@pytest.mark.parametrize("export", ["None", "42", "object", "Strategy(None)"])
def test_backtest_shard_requires_sink_class(strategy_and_shard_path, export):
    """The export must be a Sink class, not an arbitrary value, class, or instance."""
    strategy = strategy_and_shard_path["strategy"]
    strategy.write_text(
        strategy.read_text().replace("__sink__ = Strategy", f"__sink__ = {export}")
    )

    outcome = backtest_shard(strategy, strategy_and_shard_path["shard"])
    assert outcome["status"] == "error"
    assert "Sink class" in outcome["error"]["message"]
    assert str(strategy) in outcome["error"]["message"]


@pytest.mark.parametrize(
    "failure",
    [
        "raise AttributeError('strategy bug')",
        "\n".join([
            "class BrokenStrategy(Strategy):",
            "    def __init__(self, source):",
            "        raise AttributeError('strategy bug')",
            "__sink__ = BrokenStrategy",
        ]),
    ],
    ids=["module-execution", "sink-construction"],
)
def test_backtest_shard_preserves_strategy_errors(strategy_and_shard_path, failure):
    """Strategy execution errors should not be mistaken for a missing export."""
    strategy = strategy_and_shard_path["strategy"]
    strategy.write_text(f"{strategy.read_text()}\n{failure}\n")

    outcome = backtest_shard(strategy, strategy_and_shard_path["shard"])
    assert outcome["status"] == "error"
    assert outcome["error"]["type"] == "builtins.AttributeError"
    assert outcome["error"]["message"] == "strategy bug"


def test_backtest_shard_uses_broker_result_from_compute_step(
    strategy_and_shard_path, broker_result
):
    """Should select the consumer result instead of the final mapping entry."""
    shard = strategy_and_shard_path["shard"]
    strategy = strategy_and_shard_path["strategy"]

    expected: BacktestShardReturn = {
        "status": "success",
        "result": broker_result,
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


def test_backtest_dir(strategy_and_shard_path):
    """Should process all shards and return broker results."""

    shard = strategy_and_shard_path["shard"]
    strategy = strategy_and_shard_path["strategy"]
    shards_dir = shard.parent / "shards"
    shards_dir.mkdir()
    first_shard = shards_dir / "first_shard.csv"
    first_shard.write_text(shard.read_text())
    second_shard = shards_dir / "second_shard.csv"
    second_shard.write_text(shard.read_text())

    results = backtest_dir(strategy, shards_dir)

    expected_results = {
        str(first_shard.resolve()): expected_backtest_result(first_shard, strategy),
        str(second_shard.resolve()): expected_backtest_result(second_shard, strategy),
    }

    assert len(results) == 2
    assert {result["shard_path"]: result for result in results} == expected_results
