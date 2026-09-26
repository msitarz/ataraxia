# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Backtest module.

Integrate external strategy to form a computable graph and process a single shard.
"""

from collections.abc import Sequence
from pathlib import Path
from typing import Literal, TypedDict

from ataraxia.broker import Account, BrokerReturn, Position
from ataraxia.compute import compute
from ataraxia.errors import BacktestResultError, ModuleError
from ataraxia.provider import BarProvider
from ataraxia.source import SourceNode
from ataraxia.util import import_file, is_sink, is_type


class BacktestShardReturn(BrokerReturn, TypedDict):
    """Describe a broker result enriched with its backtest input paths."""

    shard_path: str
    strategy_path: str


def _positions(
    value: object, field: Literal["open_positions", "closed_positions"]
) -> tuple[Position, ...]:
    """Return validated positions from dynamically loaded strategy code.

    Raises:
        BacktestResultError: When the value is not a sequence of Position objects.
    """
    message = f"{field} must be a sequence of Position objects"
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise BacktestResultError(message)
    positions: list[Position] = []
    for position in value:
        if not isinstance(position, Position):
            raise BacktestResultError(message)
        positions.append(position)
    return tuple(positions)


def _broker_result(value: object) -> BrokerReturn:
    """Return a validated broker record from dynamically loaded strategy code.

    Raises:
        BacktestResultError: When the value lacks valid broker result fields.
    """
    if not isinstance(value, dict):
        raise BacktestResultError("Final value must be a broker result dictionary")
    account = value.get("account")
    if not isinstance(account, Account):
        raise BacktestResultError("account must be an Account")
    return {
        "account": account,
        "open_positions": _positions(value.get("open_positions"), "open_positions"),
        "closed_positions": _positions(
            value.get("closed_positions"), "closed_positions"
        ),
    }


def backtest_shard(
    strategy_path: str | Path, shard_path: str | Path
) -> BacktestShardReturn:
    """Return results from running strategy on shard.

    Args:
        strategy_path: Absolute path to Python module containing strategy.
            The module must export a Sink class as __sink__, which is constructed
            with the source. Sink will usually be the strategy.

        shard_path: Absolute path to the CSV shard to be consumed by BarProvider.

    Returns:
        Account and position sequences from the final consumer value, or sink
        value when there is no consumer, with absolute shard and strategy paths.
        Position sequences are copied to tuples. Additional strategy fields are
        not part of the returned record.

    Raises:
        ModuleError: When the module does not export a Sink class as __sink__.
        BacktestResultError: When the final value lacks valid broker result fields.
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

    try:
        result = _broker_result(final_step[sink_node.consumer() or sink_node])
    except BacktestResultError as exc:
        raise BacktestResultError(
            f"Invalid result from {strategy_path} for shard {shard_path}: {exc}"
        ) from exc
    return {
        **result,
        "shard_path": str(shard_path.resolve()),
        "strategy_path": str(strategy_path.resolve()),
    }


def backtest_dir(
    strategy_path: str | Path, dir_path: str | Path
) -> tuple[BacktestShardReturn, ...]:
    """Return complete backtest results using backtest_shard's validation."""
    dir_path = Path(dir_path)

    backtest_results: list[BacktestShardReturn] = []
    for file in dir_path.iterdir():
        backtest = backtest_shard(strategy_path, file)

        backtest_results.append(backtest)

    return tuple(backtest_results)
