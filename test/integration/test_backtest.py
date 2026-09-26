# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

from pathlib import Path
from unittest.mock import patch

import pytest

from ataraxia.backtest import backtest_dir, backtest_shard
from ataraxia.errors import ModuleError


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


def test_backtest_shard_requires_sink_export(strategy_and_shard_path):
    """A loadable strategy without __sink__ should raise a contextual domain error."""
    strategy = strategy_and_shard_path["strategy"]
    strategy.write_text(strategy.read_text().replace("__sink__ = Strategy", ""))

    with pytest.raises(ModuleError, match="__sink__") as error:
        backtest_shard(strategy, strategy_and_shard_path["shard"])

    assert str(strategy) in str(error.value)
    assert isinstance(error.value.__cause__, AttributeError)


@pytest.mark.parametrize("export", ["None", "42", "object", "Strategy(None)"])
def test_backtest_shard_requires_sink_class(strategy_and_shard_path, export):
    """The export must be a Sink class, not an arbitrary value, class, or instance."""
    strategy = strategy_and_shard_path["strategy"]
    strategy.write_text(
        strategy.read_text().replace("__sink__ = Strategy", f"__sink__ = {export}")
    )

    with pytest.raises(ModuleError, match="Sink class") as error:
        backtest_shard(strategy, strategy_and_shard_path["shard"])

    assert str(strategy) in str(error.value)


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

    with pytest.raises(AttributeError, match=r"^strategy bug$"):
        backtest_shard(strategy, strategy_and_shard_path["shard"])


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
