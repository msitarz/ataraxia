# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

from pathlib import Path

import pytest

from ataraxia.backtest import backtest_shard
from ataraxia.errors import BacktestError
from test.ataraxia.backtest_support import (
    InvalidResultFixture,
    arrange_backtest,
)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/backtest/refusals/README.md",
    ac="AC-1",
)
@pytest.mark.parametrize(
    "strategy_fixture",
    ["result_number.py", "result_non_position.py"],
    ids=["non-dict", "non-position"],
)
def test_backtest_shard_requires_broker_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    strategy_fixture: InvalidResultFixture,
) -> None:
    """Covers AC-1: real invalid results raise the contextual refusal unchanged."""
    # Given
    paths = arrange_backtest(tmp_path, monkeypatch, strategy_fixture)
    assert paths.strategy_path.name == strategy_fixture
    strategy_before = paths.strategy_path.read_bytes()
    shard_before = paths.shard_path.read_bytes()

    # When
    with pytest.raises(BacktestError) as error:
        backtest_shard(paths.strategy_path, paths.shard_path)

    # Then
    assert str(error.value) == (
        f"Strategy {paths.strategy_path} returned an invalid broker result "
        f"for shard {paths.shard_path}"
    )
    assert error.value.__cause__ is None
    assert paths.strategy_path.read_bytes() == strategy_before
    assert paths.shard_path.read_bytes() == shard_before


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/backtest/refusals/README.md",
    ac="AC-1",
)
def test_backtest_header_only_shard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Covers AC-1: a header-only shard raises its exact contextual refusal."""
    # Given
    paths = arrange_backtest(tmp_path, monkeypatch, "broker_strategy.py")
    paths.shard_path.write_text(
        "timestamp,open,high,low,close,volume\n", encoding="utf-8"
    )
    strategy_before = paths.strategy_path.read_bytes()
    shard_before = paths.shard_path.read_bytes()

    # When
    with pytest.raises(BacktestError) as error:
        backtest_shard(paths.strategy_path, paths.shard_path)

    # Then
    assert str(error.value) == f"Shard {paths.shard_path} contains no bars"
    assert error.value.__cause__ is None
    assert paths.strategy_path.read_bytes() == strategy_before
    assert paths.shard_path.read_bytes() == shard_before
