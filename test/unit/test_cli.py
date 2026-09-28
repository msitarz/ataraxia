# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

from collections.abc import Sequence
import json
from pathlib import Path
from unittest.mock import patch

from _pytest.capture import CaptureFixture
import pytest

from ataraxia.bar import Bar
from ataraxia.broker import Account, BrokerReturn, Position
from ataraxia.cli import display_results, main, save_results


@pytest.fixture
def broker_returns() -> Sequence[BrokerReturn]:
    b1o = Bar(
        timestamp=1,
        open=100,
        high=150,
        low=50,
        close=75,
        volume=2,
    )
    b1c = Bar(
        timestamp=2,
        open=80,
        high=130,
        low=20,
        close=45,
        volume=2,
    )

    p1 = Position(
        side="sell",
        stop_loss=150,
        take_profit=45,
        entry_bar=b1o,
    )
    p1.on_bar(b1c)  # profit +30

    b2o = Bar(
        timestamp=3,
        open=100,
        high=200,
        low=50,
        close=150,
        volume=10,
    )
    b2c = Bar(
        timestamp=3,
        open=150,
        high=250,
        low=100,
        close=110,
        volume=10,
    )

    p2 = Position(
        side="buy",
        stop_loss=90,
        take_profit=500,
        entry_bar=b2o,
    )
    p2.on_bar(b2c)  # unrealized loss -40

    b3o = Bar(
        timestamp=4,
        open=200,
        high=300,
        low=100,
        close=250,
        volume=10,
    )
    b3c = Bar(
        timestamp=5,
        open=250,
        high=400,
        low=150,
        close=175,
        volume=10,
    )

    p3 = Position(
        side="buy",
        stop_loss=100,
        take_profit=300,
        entry_bar=b3o,
    )
    p3.on_bar(b3c)  # profit +50

    return (
        {
            "account": Account(pnl=30, unrealized_pnl=-40),
            "closed_positions": [p1],
            "open_positions": [p2],
        },
        {
            "account": Account(pnl=50, unrealized_pnl=0),
            "closed_positions": [p3],
            "open_positions": [],
        },
    )


def test_display_results(broker_returns: tuple[BrokerReturn], capsys: CaptureFixture):
    display_results(broker_returns)

    captured = capsys.readouterr()

    assert captured.err == ""
    assert captured.out == (
        """Aggregated backtest results:\n"""
        """Realized PnL   = 80\n"""
        """Unrealized PnL = -40\n"""
    )


def test_main_print_error_and_exit(capsys: CaptureFixture):
    """Should print error and exit with code 1 if no broker results."""
    with (
        patch(
            "ataraxia.cli.sys.argv",
            ["ataraxia", "--sink", "showcase.py", "--shards-dir", "samples"],
        ),
        patch("ataraxia.cli.backtest_dir", return_value=()) as backtest_dir,
        pytest.raises(SystemExit) as raised,
    ):
        main()

    captured = capsys.readouterr()

    assert raised.value.code == 1
    assert captured.err == "No backtest completed, check params and output file\n"
    backtest_dir.assert_called_once_with(
        Path("showcase.py"), Path("samples"), parallel=None, shard_timeout=5.0
    )


def test_save_results(broker_returns, tmp_path: Path):
    output = tmp_path / "out.json"

    outcomes = [
        {
            "strategy_path": "/strategy.py",
            "shard_path": "/shard.csv",
            "status": "success",
            "result": result,
        }
        for result in broker_returns
    ]
    save_results(outcomes, output)

    assert [item["result"] for item in json.loads(output.read_text())] == [
        {
            "account": {"pnl": 30, "unrealized_pnl": -40},
            "closed_positions": [
                {
                    "side": "sell",
                    "stop_loss": 150,
                    "take_profit": 45,
                    "entry_bar": {
                        "timestamp": 1,
                        "open": 100,
                        "high": 150,
                        "low": 50,
                        "close": 75,
                        "volume": 2,
                    },
                    "entry_level": 75,
                    "closing_bar": {
                        "timestamp": 2,
                        "open": 80,
                        "high": 130,
                        "low": 20,
                        "close": 45,
                        "volume": 2,
                    },
                    "closing_level": 45,
                    "closing_pnl": 30,
                }
            ],
            "open_positions": [
                {
                    "side": "buy",
                    "stop_loss": 90,
                    "take_profit": 500,
                    "entry_bar": {
                        "timestamp": 3,
                        "open": 100,
                        "high": 200,
                        "low": 50,
                        "close": 150,
                        "volume": 10,
                    },
                    "entry_level": 150,
                    "closing_bar": None,
                    "closing_level": None,
                    "closing_pnl": None,
                }
            ],
        },
        {
            "account": {"pnl": 50, "unrealized_pnl": 0},
            "closed_positions": [
                {
                    "side": "buy",
                    "stop_loss": 100,
                    "take_profit": 300,
                    "entry_bar": {
                        "timestamp": 4,
                        "open": 200,
                        "high": 300,
                        "low": 100,
                        "close": 250,
                        "volume": 10,
                    },
                    "entry_level": 250,
                    "closing_bar": {
                        "timestamp": 5,
                        "open": 250,
                        "high": 400,
                        "low": 150,
                        "close": 175,
                        "volume": 10,
                    },
                    "closing_level": 300,
                    "closing_pnl": 50,
                }
            ],
            "open_positions": [],
        },
    ]


@pytest.mark.parametrize(
    "options",
    [
        ["--parallel", "0"],
        ["--parallel", "-1"],
        ["--parallel", "wrong"],
        ["--parallel", "1", "--shard-timeout", "0"],
        ["--parallel", "1", "--shard-timeout", "-1"],
        ["--parallel", "1", "--shard-timeout", "nan"],
        ["--parallel", "1", "--shard-timeout", "inf"],
        ["--shard-timeout", "1"],
    ],
)
def test_invalid_parallel_arguments_do_not_execute(options, tmp_path):
    output = tmp_path / "out.json"
    output.write_text("previous")
    with (
        patch(
            "ataraxia.cli.sys.argv",
            ["ataraxia", "-s", "s.py", "-d", "shards", "-o", str(output), *options],
        ),
        patch("ataraxia.cli.backtest_dir") as backtest,
        pytest.raises(SystemExit) as error,
    ):
        main()
    assert error.value.code == 2
    backtest.assert_not_called()
    assert output.read_text() == "previous"


@pytest.mark.parametrize("cpu_count", [None, 3])
def test_bare_parallel_uses_available_processors(cpu_count):
    with (
        patch(
            "ataraxia.cli.sys.argv",
            ["ataraxia", "-s", "s.py", "-d", "shards", "--parallel"],
        ),
        patch("ataraxia.cli.os.process_cpu_count", return_value=cpu_count),
        patch("ataraxia.cli.backtest_dir", return_value=()) as backtest,
        pytest.raises(SystemExit),
    ):
        main()
    assert backtest.call_args.kwargs == {
        "parallel": cpu_count or 1,
        "shard_timeout": 5.0,
    }


def test_atomic_save_preserves_existing_file_on_serialization_failure(tmp_path):
    output = tmp_path / "out.json"
    output.write_text("previous")
    with pytest.raises(TypeError):
        save_results([object()], output)
    assert output.read_text() == "previous"
    assert list(tmp_path.iterdir()) == [output]


def test_atomic_save_preserves_existing_file_on_replace_failure(tmp_path):
    output = tmp_path / "out.json"
    output.write_text("previous")
    with (
        patch("ataraxia.cli.Path.replace", side_effect=OSError("replace failed")),
        pytest.raises(OSError),
    ):
        save_results([], output)
    assert output.read_text() == "previous"
    assert list(tmp_path.iterdir()) == [output]
