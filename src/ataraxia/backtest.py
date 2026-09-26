# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Backtest module.

Integrate external strategy to form a computable graph and process a single shard.
"""

from pathlib import Path
from typing import TypedDict

from ataraxia.broker import BrokerReturn
from ataraxia.compute import compute
from ataraxia.errors import ModuleError
from ataraxia.provider import BarProvider
from ataraxia.source import SourceNode
from ataraxia.util import import_file, is_sink, is_type


class BacktestShardReturn(BrokerReturn, TypedDict):
    """Define dict to return from backtest_shard."""

    shard_path: str
    strategy_path: str


def backtest_shard(
    strategy_path: str | Path, shard_path: str | Path
) -> BacktestShardReturn:
    """Return results from running strategy on shard.

    The selected sink or consumer must return a BrokerReturn, which is enriched
    with shard and strategy paths.

    Args:
        strategy_path: Absolute path to Python module containing strategy.
            The module must export a Sink class as __sink__, which is constructed
            with the source. Sink will usually be the strategy.

        shard_path: Absolute path to the CSV shard to be consumed by BarProvider.

    Raises:
        ModuleError: When the module does not export a Sink class as __sink__.
    """
    strategy_path = Path(strategy_path)
    shard_path = Path(shard_path)

    module = import_file(strategy_path)

    export_error = (
        f"Strategy module {strategy_path} must export a Sink class as __sink__"
    )
    try:
        sink = module.__sink__
    except AttributeError as exc:
        raise ModuleError(export_error) from exc

    if not is_sink(sink) or not is_type(sink):
        raise ModuleError(export_error)

    provider = BarProvider(shard_path)
    source = SourceNode(provider)
    sink_node = sink(source)
    compute_steps = tuple(compute(sink_node))
    final_step = compute_steps[-1]

    result = final_step[sink_node.consumer() or sink_node]

    if isinstance(result, dict):
        result["shard_path"] = str(shard_path.resolve())
        result["strategy_path"] = str(strategy_path.resolve())

    return result


def backtest_dir(
    strategy_path: str | Path, dir_path: str | Path
) -> tuple[BacktestShardReturn, ...]:
    """Return broker results for every shard in a directory."""
    dir_path = Path(dir_path)

    backtest_results: list[BacktestShardReturn] = []
    for file in dir_path.iterdir():
        backtest = backtest_shard(strategy_path, file)

        backtest_results.append(backtest)

    return tuple(backtest_results)
