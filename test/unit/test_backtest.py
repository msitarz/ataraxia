# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ataraxia.backtest import backtest_dir, backtest_shard
from ataraxia.broker import Account, BrokerReturn


def test_backtest_shard_include_shard_path_strategy_path(tmp_path: Path):
    """Should include the shard and strategy paths in a broker result."""
    module_mock = MagicMock()

    @dataclass(frozen=True)
    class S:
        def __init__(self, _source):
            return None

        def consumer(self):
            return None

    sink = S(0)
    module_mock.configure_mock(__sink__=S)
    broker_result: BrokerReturn = {
        "account": Account(),
        "open_positions": [],
        "closed_positions": [],
    }

    with (
        patch(
            "ataraxia.backtest.compute",
            return_value=({sink: broker_result},),
        ),
        patch("ataraxia.backtest.import_file", return_value=module_mock),
        patch("ataraxia.backtest.is_sink", return_value=True),
        patch("ataraxia.backtest.is_type", return_value=True),
    ):
        result = backtest_shard("somefile.py", "somedir")

        assert result.get("shard_path")
        assert result.get("strategy_path")


@pytest.mark.parametrize(
    "result",
    [
        42,
        {"account": Account(), "open_positions": [], "closed_positions": [object()]},
    ],
    ids=["non-dict", "non-position"],
)
def test_backtest_shard_requires_broker_result(result: object):
    """Should reject a selected sink or consumer result outside the broker contract."""
    module_mock = MagicMock()

    @dataclass(frozen=True)
    class S:
        def __init__(self, _source):
            return None

        def consumer(self):
            return None

    sink = S(0)
    module_mock.configure_mock(__sink__=S)

    with (
        patch(
            "ataraxia.backtest.compute",
            return_value=({sink: result},),
        ),
        patch("ataraxia.backtest.import_file", return_value=module_mock),
        patch("ataraxia.backtest.is_sink", return_value=True),
        patch("ataraxia.backtest.is_type", return_value=True),
    ):
        outcome = backtest_shard("strategy.py", "shard.csv")

    assert outcome["status"] == "error"
    assert "invalid broker result" in outcome["error"]["message"]
    assert "strategy.py" in outcome["error"]["message"]
    assert "shard.csv" in outcome["error"]["message"]


def test_backtest_dir_raise_on_wrong_param():
    with pytest.raises(FileNotFoundError):
        backtest_dir("hello", "i do not exist")


def test_exception_diagnostics_preserve_chains_notes_groups_and_unpicklable_state():
    from ataraxia.backtest import exception_diagnostic

    try:
        try:
            raise ValueError("original")
        except ValueError as cause:
            error = ExceptionGroup("group", [RuntimeError("nested")])
            error.add_note("useful note")
            error.unpicklable = lambda: None
            raise error from cause
    except Exception as error:
        diagnostic = exception_diagnostic(error)
    assert diagnostic["type"] == "builtins.ExceptionGroup"
    for text in ("original", "direct cause", "nested", "useful note"):
        assert text in diagnostic["traceback"]


def test_exception_diagnostic_formatting_fallback():
    from ataraxia.backtest import exception_diagnostic

    class Broken(Exception):
        def __str__(self):
            raise RuntimeError("format failed")

    with patch(
        "ataraxia.backtest.traceback.TracebackException.from_exception",
        side_effect=ValueError,
    ):
        diagnostic = exception_diagnostic(Broken())
    assert "unavailable" in diagnostic["message"]
    assert "formatting failed" in diagnostic["traceback"]


@pytest.mark.parametrize("error", [KeyboardInterrupt(), SystemExit(3)])
def test_main_process_base_exceptions_propagate(error):
    with (
        patch("ataraxia.backtest.import_file", side_effect=error),
        pytest.raises(type(error)),
    ):
        backtest_shard("strategy.py", "shard.csv")


@pytest.mark.parametrize(("width", "depth"), [(20, 1), (1, 12), (20, 12)])
def test_exception_diagnostic_preserves_entire_group(width, depth):
    from ataraxia.backtest import exception_diagnostic

    children = []
    for index in range(width):
        try:
            raise ValueError(f"leaf-{index:02d}")
        except ValueError as child:
            child.add_note(f"note-{index:02d}")
            children.append(child)
    group = ExceptionGroup("level-0", children)
    for level in range(1, depth):
        group = ExceptionGroup(f"level-{level}", [group])
    try:
        try:
            raise RuntimeError("explicit cause")
        except RuntimeError as cause:
            raise group from cause
    except Exception as error:
        diagnostic = exception_diagnostic(error)
    stack = diagnostic["traceback"]
    for index in range(width):
        assert f"leaf-{index:02d}" in stack
        assert f"note-{index:02d}" in stack
    for level in range(depth):
        assert f"level-{level}" in stack
    assert stack.count("in test_exception_diagnostic_preserves_entire_group") >= width
    assert "explicit cause" in stack
    assert "direct cause" in stack
    assert "max_group_depth" not in stack
    assert "and 5 more exceptions" not in stack


def test_group_diagnostic_respects_suppressed_context():
    from ataraxia.backtest import exception_diagnostic

    try:
        try:
            raise ValueError("hidden context")
        except ValueError:
            raise ExceptionGroup(
                "visible group", [RuntimeError("visible child")]
            ) from None
    except Exception as error:
        diagnostic = exception_diagnostic(error)
    assert "hidden context" not in diagnostic["traceback"]
    assert "visible group" in diagnostic["traceback"]
    assert "visible child" in diagnostic["traceback"]
