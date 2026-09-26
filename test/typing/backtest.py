# SPDX-License-Identifier: Apache-2.0
"""Static regression checks for the public backtest result contract."""

from collections.abc import Sequence
from pathlib import Path
from typing import assert_type

from ataraxia.backtest import BacktestShardReturn, backtest_dir, backtest_shard
from ataraxia.broker import Account, Position
from ataraxia.cli import display_results, save_results


def backtest_contract(strategy: Path, shard: Path, directory: Path) -> None:
    """Keep full result types available to callers without narrowing or casts."""
    result = backtest_shard(strategy, shard)
    assert_type(result, BacktestShardReturn)
    assert_type(result["account"], Account)
    assert_type(result["open_positions"], Sequence[Position])
    assert_type(result["closed_positions"], Sequence[Position])
    assert_type(result["shard_path"], str)
    assert_type(result["strategy_path"], str)
    results = backtest_dir(strategy, directory)
    assert_type(results, tuple[BacktestShardReturn, ...])
    display_results(results)
    save_results(results, Path("results.json"))

    result["account"] = 1  # E: is not assignable to TypedDict key
