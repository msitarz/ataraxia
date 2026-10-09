# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

from pathlib import Path

import pytest

from ataraxia.backtest import backtest_dir


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/backtest/refusals/README.md",
    ac="AC-1",
)
def test_backtest_dir_raise_on_wrong_param(tmp_path: Path) -> None:
    """Covers AC-1: a missing shard directory reports its offending path."""
    # Given
    missing_directory = tmp_path / "i do not exist"

    # When
    with pytest.raises(FileNotFoundError) as error:
        backtest_dir("hello", missing_directory)

    # Then
    assert error.value.filename == str(missing_directory)
