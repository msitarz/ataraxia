# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

from pathlib import Path

import pytest

from ataraxia.backtest import backtest_shard
from ataraxia.errors import ModuleError
from ataraxia.util import import_file, is_sink, is_type
from test.ataraxia.backtest_support import (
    InvalidExportFixture,
    arrange_backtest,
)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/backtest/exports/README.md",
    ac="AC-1",
)
def test_backtest_shard_requires_sink_export(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reject the missing export with its exact path and AttributeError cause."""
    # Given
    paths = arrange_backtest(tmp_path, monkeypatch, "missing_export.py")

    # When
    with pytest.raises(ModuleError) as error:
        backtest_shard(paths.strategy_path, paths.shard_path)

    # Then
    assert str(error.value) == (
        f"Strategy module {paths.strategy_path} must export a Sink class as __sink__"
    )
    assert isinstance(error.value.__cause__, AttributeError)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/backtest/exports/README.md",
    ac="AC-1",
)
@pytest.mark.parametrize(
    ("strategy_fixture", "sink_guard", "type_guard"),
    [
        ("export_none.py", False, False),
        ("export_number.py", False, False),
        ("export_object.py", False, True),
        ("export_instance.py", True, False),
    ],
    ids=["none", "integer", "class-not-sink", "sink-instance"],
)
def test_backtest_shard_requires_sink_class(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    strategy_fixture: InvalidExportFixture,
    sink_guard: bool,
    type_guard: bool,
) -> None:
    """Preserve the non-Sink and non-class export guards and contextual error."""
    # Given
    paths = arrange_backtest(tmp_path, monkeypatch, strategy_fixture)

    # When
    with pytest.raises(ModuleError) as error:
        backtest_shard(paths.strategy_path, paths.shard_path)
    module = import_file(paths.strategy_path)
    exported: object | None = getattr(module, "__sink__", None)

    # Then
    assert is_sink(exported) is sink_guard
    assert is_type(exported) is type_guard
    assert str(error.value) == (
        f"Strategy module {paths.strategy_path} must export a Sink class as __sink__"
    )
    assert error.value.__cause__ is None


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/backtest/exports/README.md",
    ac="AC-1",
)
@pytest.mark.parametrize(
    "strategy_fixture",
    ["module_error.py", "construction_error.py"],
    ids=["module-execution", "sink-construction"],
)
def test_backtest_shard_preserves_strategy_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    strategy_fixture: InvalidExportFixture,
) -> None:
    """Preserve the module-execution and sink-construction AttributeErrors."""
    # Given
    paths = arrange_backtest(tmp_path, monkeypatch, strategy_fixture)

    # When
    with pytest.raises(AttributeError) as error:
        backtest_shard(paths.strategy_path, paths.shard_path)

    # Then
    assert str(error.value) == "strategy bug"
    assert error.value.__cause__ is None
