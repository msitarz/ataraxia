# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

from pathlib import Path

import pytest

from ataraxia.bar import Bar
from ataraxia.util import import_file
from test.ataraxia.backtest_support import copy_import_bar


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/backtest/loading/README.md",
    ac="AC-1",
)
def test_import_file(tmp_path: Path) -> None:
    """Load and invoke the copied fixture's complete six-field Bar factory."""
    # Given
    mod_path = copy_import_bar(tmp_path)

    # When
    module = import_file(mod_path)
    factory = getattr(module, "new_bar", None)
    assert callable(factory)
    result = factory()
    assert isinstance(result, Bar)

    # Then
    assert result == Bar(timestamp=1, open=1, high=1, low=1, close=1, volume=1)
