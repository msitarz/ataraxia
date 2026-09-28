# SPDX-License-Identifier: Apache-2.0
"""Shard boundary contracts and runtime validation."""

from collections.abc import Sequence
from typing import Literal, TypedDict, TypeIs

from ataraxia.broker import Account, BrokerReturn, Position


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


def is_shard_error(value: object) -> TypeIs[ShardError]:
    """Return whether a diagnostic satisfies its discriminated contract."""
    if not isinstance(value, dict):
        return False
    if not isinstance(value.get("type"), str) or not isinstance(
        value.get("message"), str
    ):
        return False
    common = {"kind", "type", "message", "traceback"}
    match value.get("kind"):
        case "exception":
            return set(value) == common and isinstance(value.get("traceback"), str)
        case "timeout":
            return (
                set(value) == common | {"timeout_seconds", "elapsed_seconds"}
                and value.get("traceback") is None
                and isinstance(value.get("timeout_seconds"), float)
                and isinstance(value.get("elapsed_seconds"), float)
            )
        case "worker_failure":
            return (
                set(value) == common | {"exit_code"}
                and value.get("traceback") is None
                and (
                    value.get("exit_code") is None
                    or type(value.get("exit_code")) is int
                )
            )
        case _:
            return False


def is_shard_outcome(value: object) -> TypeIs[BacktestShardReturn]:
    """Return whether a received outcome has exactly one valid variant."""
    if not isinstance(value, dict):
        return False
    if not isinstance(value.get("strategy_path"), str) or not isinstance(
        value.get("shard_path"), str
    ):
        return False
    common = {"strategy_path", "shard_path", "status"}
    if value.get("status") == "success":
        return set(value) == common | {"result"} and is_broker_return(
            value.get("result")
        )
    return (
        value.get("status") == "error"
        and set(value) == common | {"error"}
        and is_shard_error(value.get("error"))
    )
