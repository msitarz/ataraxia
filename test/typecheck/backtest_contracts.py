# SPDX-License-Identifier: Apache-2.0
from typing import assert_type

from ataraxia.broker import BrokerReturn
from ataraxia.shard_types import (
    BacktestShardReturn,
    ShardError,
    ShardFailure,
    ShardSuccess,
)


def narrow(outcome: BacktestShardReturn) -> None:
    if outcome["status"] == "success":
        assert_type(outcome["result"], BrokerReturn)
        outcome["error"]  # E: does not have key
    else:
        assert_type(outcome["error"], ShardError)
        outcome["result"]  # E: does not have key


def invalid(result: BrokerReturn, error: ShardError) -> None:
    _success: ShardSuccess = {
        "strategy_path": "/s",
        "shard_path": "/d",
        "status": "success",
        "result": result,
        "error": error,  # E: is not defined
    }
    _failure: ShardFailure = {
        "strategy_path": "/s",
        "shard_path": "/d",
        "status": "error",
        "error": error,
        "result": result,  # E: is not defined
    }
