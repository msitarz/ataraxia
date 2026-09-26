# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

from pathlib import Path
from unittest.mock import patch

import pytest

from ataraxia.backtest import backtest_dir, backtest_shard
from ataraxia.cli import main
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


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("item.close", 150),
        ("None", None),
        (
            "{'close': item.close, 'shard_path': 'old', 'strategy_path': 'old'}",
            {"close": 150},
        ),
    ],
)
def test_backtest_shard(strategy_and_shard_path, expression, expected):
    """Return arbitrary sink values, enriching only dictionaries with input paths."""
    shard = strategy_and_shard_path["shard"]
    strategy = strategy_and_shard_path["strategy"]
    strategy.write_text(strategy.read_text().replace("item.close", expression))

    result = backtest_shard(strategy, shard)

    if isinstance(expected, dict):
        expected = {
            **expected,
            "shard_path": str(shard.resolve()),
            "strategy_path": str(strategy.resolve()),
        }
    assert result == expected


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


def test_backtest_dir(strategy_and_shard_path, tmp_path: Path):
    """Preserve non-broker values when running a real strategy across shards."""
    shards = tmp_path / "shards"
    shards.mkdir()
    data = strategy_and_shard_path["shard"].read_text()
    (shards / "first.csv").write_text(data)
    (shards / "second.csv").write_text(data)

    results = backtest_dir(strategy_and_shard_path["strategy"], shards)

    assert results == (150, 150)


@pytest.mark.parametrize("expression", ["item.close", "{'close': item.close}"])
def test_cli_rejects_non_broker_strategy_results(
    strategy_and_shard_path, tmp_path: Path, capsys, expression
):
    """Unsupported CLI results leave an existing output file intact."""
    strategy = strategy_and_shard_path["strategy"]
    strategy.write_text(strategy.read_text().replace("item.close", expression))
    shards = tmp_path / "shards"
    shards.mkdir()
    strategy_and_shard_path["shard"].rename(shards / "shard.csv")
    output = tmp_path / "results.json"
    output.write_text("previous results")
    argv = [
        "ataraxia",
        "--sink",
        str(strategy),
        "--shards-dir",
        str(shards),
        "--output",
        str(output),
    ]

    with patch("ataraxia.cli.sys.argv", argv), pytest.raises(SystemExit) as error:
        main()

    assert error.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "CLI requires broker results" in captured.err
    assert "Python backtest API" in captured.err
    assert output.read_text() == "previous results"
