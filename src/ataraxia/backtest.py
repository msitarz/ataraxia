# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Backtest module.

Integrate external strategy to form a computable graph and process a single shard.
"""

from collections.abc import Sequence
from pathlib import Path
import traceback
from typing import Literal, TypedDict, TypeIs

from ataraxia.broker import Account, BrokerReturn, Position
from ataraxia.compute import compute
from ataraxia.errors import BacktestError, ModuleError
from ataraxia.provider import BarProvider
from ataraxia.source import SourceNode
from ataraxia.util import import_file, is_sink, is_type


class ShardInput(TypedDict):
    """Identify a strategy and shard by absolute paths."""

    strategy_path: str
    shard_path: str


class ExceptionDiagnostic(TypedDict):
    """Store an exception without live exception or traceback objects."""

    kind: Literal["exception"]
    type: str
    message: str
    traceback: str


class TimeoutDiagnostic(TypedDict):
    """Describe an expired assignment."""

    kind: Literal["timeout"]
    type: str
    message: str
    timeout_seconds: float
    elapsed_seconds: float
    traceback: None


class WorkerFailureDiagnostic(TypedDict):
    """Describe a worker that failed to deliver an outcome."""

    kind: Literal["worker_failure"]
    type: str
    message: str
    exit_code: int | None
    traceback: None


type ShardError = ExceptionDiagnostic | TimeoutDiagnostic | WorkerFailureDiagnostic


class ShardSuccess(ShardInput):
    """Contain a validated broker result."""

    status: Literal["success"]
    result: BrokerReturn


class ShardFailure(ShardInput):
    """Contain a serializable diagnostic, without a broker result."""

    status: Literal["error"]
    error: ShardError


type BacktestShardReturn = ShardSuccess | ShardFailure


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


def is_position_sequence(value: object) -> TypeIs[Sequence[Position]]:
    """Return whether a value is a sequence of positions."""
    return (
        isinstance(value, Sequence)
        and not isinstance(value, (str, bytes, bytearray))
        and all(isinstance(position, Position) for position in value)
    )


def is_broker_return(value: object) -> TypeIs[BrokerReturn]:
    """Return whether a value has the broker result contract."""
    if not isinstance(value, dict):
        return False

    return (
        isinstance(value.get("account"), Account)
        and is_position_sequence(value.get("open_positions"))
        and is_position_sequence(value.get("closed_positions"))
    )


def _compute_shard(strategy_path: str | Path, shard_path: str | Path) -> BrokerReturn:
    """Return results from running strategy on shard.

    The selected sink or consumer must return a BrokerReturn, which is enriched
    with shard and strategy paths.

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

    return result


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
    strategy_path: str | Path, dir_path: str | Path
) -> tuple[BacktestShardReturn, ...]:
    """Return broker results for every shard in a directory."""
    dir_path = Path(dir_path)

    backtest_results: list[BacktestShardReturn] = []
    for file in dir_path.iterdir():
        backtest = backtest_shard(strategy_path, file)

        backtest_results.append(backtest)

    return tuple(backtest_results)
