# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Typed paths, copied fixtures, and independent expected backtest results."""

from dataclasses import dataclass
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from shutil import copyfile
import sys
from typing import Literal

import pytest

from ataraxia.backtest import BacktestShardReturn
from ataraxia.bar import Bar
from ataraxia.broker import Position

type StrategyFixture = Literal["broker_strategy.py", "sink_result_strategy.py"]
type InvalidExportFixture = Literal[
    "missing_export.py",
    "export_none.py",
    "export_number.py",
    "export_object.py",
    "export_instance.py",
    "module_error.py",
    "construction_error.py",
]
type InvalidResultFixture = Literal[
    "result_number.py",
    "result_non_position.py",
]
type InvalidStrategyFixture = InvalidExportFixture | InvalidResultFixture
type StrategyBasename = Literal[
    "broker_strategy.py",
    "sink_result_strategy.py",
    "missing_export.py",
    "export_none.py",
    "export_number.py",
    "export_object.py",
    "export_instance.py",
    "module_error.py",
    "construction_error.py",
    "result_number.py",
    "result_non_position.py",
    "somefile.py",
]
type ShardBasename = Literal["shard.csv", "somedir"]

BACKTEST_SHARD = "timestamp,open,high,low,close,volume\n1,100,200,50,150,1\n"


@dataclass(frozen=True)
class BacktestPaths:
    """Identify the copied strategy and its CSV shard."""

    strategy_path: Path
    shard_path: Path


@dataclass(frozen=True)
class AccountObservation:
    """Complete account values captured from a backtest result."""

    pnl: int
    unrealized_pnl: int


@dataclass(frozen=True)
class PositionObservation:
    """Complete position values captured independently of position processing."""

    side: Literal["buy", "sell"]
    stop_loss: int
    take_profit: int
    entry_bar: Bar
    entry_level: int
    closing_bar: Bar | None
    closing_level: int | None
    closing_pnl: int | None


@dataclass(frozen=True)
class BacktestObservation:
    """Complete account, position and resolved-path values."""

    account: AccountObservation
    open_positions: tuple[PositionObservation, ...]
    closed_positions: tuple[PositionObservation, ...]
    shard_path: str
    strategy_path: str


def arrange_backtest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    strategy_fixture: StrategyFixture | InvalidStrategyFixture,
    *,
    strategy_basename: StrategyBasename | None = None,
    shard_basename: ShardBasename = "shard.csv",
) -> BacktestPaths:
    """Copy a named strategy arrangement and shard into a temporary import root."""
    fixture_root = Path(__file__).parent / "fixtures" / "backtest"
    strategy_root = tmp_path / "strategy"
    strategy_root.mkdir(parents=True)

    copyfile(fixture_root / "strategy_base.py", strategy_root / "strategy_base.py")
    strategy_path = strategy_root / (strategy_basename or strategy_fixture)
    copyfile(fixture_root / strategy_fixture, strategy_path)
    monkeypatch.syspath_prepend(str(strategy_root))

    base_path = strategy_root / "strategy_base.py"
    spec = spec_from_file_location("strategy_base", base_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load copied strategy base: {base_path}")
    base_module = module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "strategy_base", base_module)
    spec.loader.exec_module(base_module)

    shard_path = tmp_path / shard_basename
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
) -> BacktestObservation:
    """Return the complete literal result for the retained buy-signal strategy."""
    return BacktestObservation(
        account=AccountObservation(pnl=0, unrealized_pnl=0),
        open_positions=(
            PositionObservation(
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
                entry_level=150,
                closing_bar=None,
                closing_level=None,
                closing_pnl=None,
            ),
        ),
        closed_positions=(),
        shard_path=str(shard_path.resolve()),
        strategy_path=str(strategy_path.resolve()),
    )


def expected_sink_result_strategy_result(
    shard_path: Path, strategy_path: Path
) -> BacktestObservation:
    """Return the complete literal result for a direct sink result."""
    return BacktestObservation(
        account=AccountObservation(pnl=0, unrealized_pnl=0),
        open_positions=(),
        closed_positions=(),
        shard_path=str(shard_path.resolve()),
        strategy_path=str(strategy_path.resolve()),
    )


def observe_position(position: Position) -> PositionObservation:
    """Copy every public position value into a typed test observation."""
    return PositionObservation(
        side=position.side,
        stop_loss=position.stop_loss,
        take_profit=position.take_profit,
        entry_bar=position.entry_bar,
        entry_level=position.entry_level,
        closing_bar=position.closing_bar,
        closing_level=position.closing_level,
        closing_pnl=position.closing_pnl,
    )


def observe_backtest_result(result: BacktestShardReturn) -> BacktestObservation:
    """Copy a backtest result into complete typed account and position values."""
    return BacktestObservation(
        account=AccountObservation(
            pnl=result["account"].pnl,
            unrealized_pnl=result["account"].unrealized_pnl,
        ),
        open_positions=tuple(observe_position(p) for p in result["open_positions"]),
        closed_positions=tuple(observe_position(p) for p in result["closed_positions"]),
        shard_path=result["shard_path"],
        strategy_path=result["strategy_path"],
    )
