# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Backtest module.

Integrate external strategy to form a computable graph and process a single shard.
"""

from pathlib import Path

from ataraxia.broker import BrokerReturn
from ataraxia.compute import compute
from ataraxia.errors import ModuleError
from ataraxia.provider import BarProvider
from ataraxia.source import SourceNode
from ataraxia.util import import_file, is_sink, is_type


def backtest_shard(strategy_path: str | Path, shard_path: str | Path):
    """Return results from running strategy on shard.

    Args:
        strategy_path: Absolute path to Python module containing strategy.
            The module must have special __sink__ attribute that will be used
            as the sink in the computable graph.  Sink will usually be the strategy.

        shard_path: Absolute path to the CSV shard to be consumed by BarProvider.

    Raises:
        ModuleError: When the module does not expose strategy.
    """
    strategy_path = Path(strategy_path)
    shard_path = Path(shard_path)

    module = import_file(strategy_path)

    sink = module.__sink__

    if not is_sink(sink) or not is_type(sink):
        raise ModuleError("Module must provide Sink computable in __sink__ attribute")

    with BarProvider(shard_path) as provider:
        source = SourceNode(provider)
        sink_node = sink(source)
        compute_steps = tuple(compute(sink_node))
        final_step = compute_steps[-1]

        return final_step[sink_node.consumer() or sink_node]


def backtest_dir(strategy_path: str | Path, dir_path: str | Path):
    """Return backtest results from directory containing shards."""
    dir_path = Path(dir_path)

    backtest_results: list[BrokerReturn] = []
    for file in dir_path.iterdir():
        backtest = backtest_shard(strategy_path, file)

        backtest_results.append(backtest)

    return tuple(backtest_results)
