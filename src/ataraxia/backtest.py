# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Backtest module.

Integrate external strategy to form a computable graph and process a single shard.
"""

from pathlib import Path
import traceback

from ataraxia.broker import BrokerReturn
from ataraxia.compute import compute
from ataraxia.errors import BacktestError, ModuleError
from ataraxia.provider import BarProvider
from ataraxia.shard_pool import run_shards
from ataraxia.shard_types import (
    BacktestShardReturn,
    ExceptionDiagnostic,
    ShardFailure,
    ShardInput,
    ShardSuccess,
    is_broker_return,
)
from ataraxia.source import SourceNode
from ataraxia.util import import_file, is_sink, is_type


def exception_diagnostic(exc: Exception) -> ExceptionDiagnostic:
    """Return chained diagnostics, falling back if user formatting fails."""
    exception_type = f"{type(exc).__module__}.{type(exc).__qualname__}"
    try:
        message = str(exc)
    except Exception:
        message = "Exception message unavailable: __str__ failed"
    try:
        stack = "".join(traceback.format_exception(exc))
    except Exception:
        stack = f"{exception_type}: {message}\nTraceback formatting failed"
    return {
        "kind": "exception",
        "type": exception_type,
        "message": message,
        "traceback": stack,
    }


def _compute_shard(strategy_path: str | Path, shard_path: str | Path) -> BrokerReturn:
    """Return results from running strategy on shard.

    The selected sink or consumer must return a BrokerReturn.

    Args:
        strategy_path: Absolute path to Python module containing strategy.
            The module must export a Sink class as __sink__, which is constructed
            with the source. Sink will usually be the strategy.

        shard_path: Absolute path to the CSV shard to be consumed by BarProvider.

    Raises:
        BacktestError: When the shard contains no bars or the selected sink or
            consumer does not return a broker result.
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
    if not compute_steps:
        raise BacktestError(f"Shard {shard_path} contains no bars")
    final_step = compute_steps[-1]

    result = final_step[sink_node.consumer() or sink_node]

    if not is_broker_return(result):
        raise BacktestError(
            f"Strategy {strategy_path} returned an invalid broker result for shard "
            f"{shard_path}"
        )

    return {
        "account": result["account"],
        "open_positions": result["open_positions"],
        "closed_positions": result["closed_positions"],
    }


def backtest_shard(
    strategy_path: str | Path, shard_path: str | Path
) -> BacktestShardReturn:
    """Return one shard outcome, retaining ordinary failures as diagnostics."""
    request: ShardInput = {
        "strategy_path": str(Path(strategy_path).resolve()),
        "shard_path": str(Path(shard_path).resolve()),
    }
    try:
        result = _compute_shard(request["strategy_path"], request["shard_path"])
    except Exception as exc:
        failure: ShardFailure = {
            "strategy_path": request["strategy_path"],
            "shard_path": request["shard_path"],
            "status": "error",
            "error": exception_diagnostic(exc),
        }
        return failure
    success: ShardSuccess = {
        "strategy_path": request["strategy_path"],
        "shard_path": request["shard_path"],
        "status": "success",
        "result": result,
    }
    return success


def backtest_dir(
    strategy_path: str | Path,
    dir_path: str | Path,
    *,
    parallel: int | None = None,
    shard_timeout: float = 5.0,
) -> tuple[BacktestShardReturn, ...]:
    """Return shard outcomes in discovery order or parallel arrival order."""
    dir_path = Path(dir_path)

    requests: tuple[ShardInput, ...] = tuple(
        {
            "strategy_path": str(Path(strategy_path).resolve()),
            "shard_path": str(file.resolve()),
        }
        for file in dir_path.iterdir()
    )
    if parallel is not None:
        return run_shards(requests, parallel, shard_timeout, backtest_shard)
    backtest_results: list[BacktestShardReturn] = []
    for request in requests:
        backtest = backtest_shard(request["strategy_path"], request["shard_path"])

        backtest_results.append(backtest)

    return tuple(backtest_results)
