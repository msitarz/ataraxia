# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Typed paths, copied fixtures, and independent expected backtest results."""

from dataclasses import dataclass
from pathlib import Path
from shutil import copyfile
from typing import Literal

import pytest

from ataraxia.backtest import BacktestShardReturn
from ataraxia.bar import Bar
from ataraxia.broker import Account, Position

type StrategyFixture = Literal["broker_strategy.py", "sink_result_strategy.py"]

BACKTEST_SHARD = "timestamp,open,high,low,close,volume\n1,100,200,50,150,1\n"


@dataclass(frozen=True)
class BacktestPaths:
    """Identify the copied strategy and its CSV shard."""

    strategy_path: Path
    shard_path: Path


def arrange_backtest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    strategy_fixture: StrategyFixture,
) -> BacktestPaths:
    """Copy a named strategy bundle and shard into a temporary import root."""
    fixture_root = Path(__file__).parent / "fixtures" / "backtest"
    strategy_root = tmp_path / "strategy"
    strategy_root.mkdir(parents=True)

    copyfile(fixture_root / "strategy_base.py", strategy_root / "strategy_base.py")
    strategy_path = strategy_root / strategy_fixture
    copyfile(fixture_root / strategy_fixture, strategy_path)
    monkeypatch.syspath_prepend(str(strategy_root))

    shard_path = tmp_path / "shard.csv"
    shard_path.write_text(BACKTEST_SHARD, encoding="utf-8")
    return BacktestPaths(strategy_path=strategy_path, shard_path=shard_path)


def copy_import_bar(tmp_path: Path) -> Path:
    """Copy the named standalone Bar loader fixture into a temporary path."""
    fixture_path = Path(__file__).parent / "fixtures" / "backtest" / "import_bar.py"
    destination = tmp_path / "import_bar.py"
    copyfile(fixture_path, destination)
    return destination


def expected_broker_strategy_result(
    shard_path: Path, strategy_path: Path
) -> BacktestShardReturn:
    """Return the complete literal result for the retained buy-signal strategy."""
    return {
        "account": Account(pnl=0, unrealized_pnl=0),
        "open_positions": [
            Position(
                side="buy",
                stop_loss=100,
                take_profit=200,
                entry_bar=Bar(
                    timestamp=1,
                    open=100,
                    high=200,
                    low=50,
                    close=150,
                    volume=1,
                ),
            )
        ],
        "closed_positions": [],
        "shard_path": str(shard_path.resolve()),
        "strategy_path": str(strategy_path.resolve()),
    }


def expected_sink_result_strategy_result(
    shard_path: Path, strategy_path: Path
) -> BacktestShardReturn:
    """Return the complete literal result for a direct sink result."""
    return {
        "account": Account(pnl=0, unrealized_pnl=0),
        "open_positions": [],
        "closed_positions": [],
        "shard_path": str(shard_path.resolve()),
        "strategy_path": str(strategy_path.resolve()),
    }
