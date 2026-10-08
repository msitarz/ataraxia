# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

from pathlib import Path
from shutil import copyfile

import pytest

from ataraxia.backtest import backtest_dir, backtest_shard
from test.ataraxia.backtest_support import (
    BacktestObservation,
    arrange_backtest,
    expected_broker_strategy_result,
    expected_sink_result_strategy_result,
    observe_backtest_result,
)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/backtest/results/README.md",
    ac="AC-1",
)
def test_backtest_shard(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Compare the complete real broker result for the retained one-bar shard."""
    # Given
    paths = arrange_backtest(tmp_path, monkeypatch, "broker_strategy.py")

    # When
    result = backtest_shard(paths.strategy_path, paths.shard_path)

    # Then
    observed: BacktestObservation = observe_backtest_result(result)
    assert observed == expected_broker_strategy_result(
        paths.shard_path, paths.strategy_path
    )


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/backtest/results/README.md",
    ac="AC-1",
)
def test_backtest_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Compare results by resolved shard path without relying on directory order."""
    # Given
    paths = arrange_backtest(tmp_path, monkeypatch, "broker_strategy.py")
    shards_dir = tmp_path / "shards"
    shards_dir.mkdir()
    first_shard = shards_dir / "first_shard.csv"
    second_shard = shards_dir / "second_shard.csv"
    copyfile(paths.shard_path, first_shard)
    copyfile(paths.shard_path, second_shard)

    # When
    results = backtest_dir(paths.strategy_path, shards_dir)

    # Then
    expected: dict[str, BacktestObservation] = {
        str(first_shard.resolve()): expected_broker_strategy_result(
            first_shard, paths.strategy_path
        ),
        str(second_shard.resolve()): expected_broker_strategy_result(
            second_shard, paths.strategy_path
        ),
    }
    observed = {
        result["shard_path"]: observe_backtest_result(result) for result in results
    }
    assert len(results) == 2
    assert observed == expected


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/backtest/results/README.md",
    ac="AC-1",
)
def test_backtest_shard_include_shard_path_strategy_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Retain path basenames while checking a complete direct-sink result."""
    # Given
    paths = arrange_backtest(
        tmp_path,
        monkeypatch,
        "sink_result_strategy.py",
        strategy_basename="somefile.py",
        shard_basename="somedir",
    )

    # When
    result = backtest_shard(paths.strategy_path, paths.shard_path)

    # Then
    assert paths.strategy_path.name == "somefile.py"
    assert paths.shard_path.name == "somedir"
    observed: BacktestObservation = observe_backtest_result(result)
    assert observed == expected_sink_result_strategy_result(
        paths.shard_path, paths.strategy_path
    )
