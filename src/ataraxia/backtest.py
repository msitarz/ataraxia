# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Backtest module.

Integrate external strategy to form a computable graph and process a single shard.
"""

from pathlib import Path

from ataraxia.broker import BrokerReturn
from ataraxia.compute import compute
from ataraxia.errors import BacktestError, ModuleError
from ataraxia.provider import BarProvider
from ataraxia.source import SourceNode
from ataraxia.util import import_file, is_sink, is_type


def backtest_shard(strategy_path: str | Path, shard_path: str | Path):
    """Return results from running strategy on shard.

    Args:
        strategy_path: Absolute path to Python module containing strategy.
            The module must have special __strategy__ attribute that will be used
            as the sink in the computable graph.

        shard_path: Absolute path to the CSV shard to be consumed by BarProvider.

    Raises:
        ModuleError: When the module does not expose strategy.
    """
    strategy_path = Path(strategy_path)
    shard_path = Path(shard_path)

    module = import_file(strategy_path)

    strategy = module.__strategy__

    if not is_sink(strategy) or not is_type(strategy):
        raise ModuleError(
            "Module must provide Sink computable in __strategy__ attribute."
        )

    with BarProvider(shard_path) as provider:
        source = SourceNode(provider)
        all_compute_steps = tuple(compute(strategy(source)))
        broker_result = tuple(all_compute_steps[-1].values())[-1]

        return broker_result


def backtest_dir(strategy_path: str | Path, dir_path: str | Path):
    """Return backtest results from directory containing shards.

    Raises:
        BacktestError: When dir_path argument is not a directory+
    """
    dir_path = Path(dir_path)

    if not dir_path.is_dir():
        raise BacktestError("dir_path argument must be a directory")

    backtest_results: list[BrokerReturn] = []
    for file in dir_path.iterdir():
        backtest = backtest_shard(strategy_path, file)

        backtest_results.append(backtest)

    return tuple(backtest_results)
