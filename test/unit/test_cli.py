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
    backtest_dir.assert_called_once_with(Path("showcase.py"), Path("samples"))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("account", {"pnl": 0, "unrealized_pnl": 0}),
        ("open_positions", None),
        ("closed_positions", None),
        ("open_positions", ""),
        ("closed_positions", b""),
        ("open_positions", bytearray()),
        ("open_positions", [object()]),
        ("closed_positions", ({"side": "buy"},)),
    ],
)
def test_main_rejects_malformed_broker_results(
    broker_returns, tmp_path: Path, capsys: CaptureFixture, field, value
):
    """Validate every result before displaying totals or creating output."""
    output = tmp_path / "results.json"
    malformed = {**broker_returns[1], field: value}
    with (
        patch(
            "ataraxia.cli.sys.argv",
            ["ataraxia", "-s", "strategy.py", "-d", "shards", "-o", str(output)],
        ),
        patch("ataraxia.cli.backtest_dir", return_value=(broker_returns[0], malformed)),
        pytest.raises(SystemExit) as error,
    ):
        main()

    assert error.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "CLI requires broker results" in captured.err
    assert not output.exists()


def test_main_accepts_position_sequences(broker_returns, tmp_path: Path, capsys):
    """BrokerReturn permits tuple position sequences as well as lists."""
    output = tmp_path / "results.json"
    results = tuple(
        {
            **result,
            "open_positions": tuple(result["open_positions"]),
            "closed_positions": tuple(result["closed_positions"]),
        }
        for result in broker_returns
    )
    with (
        patch(
            "ataraxia.cli.sys.argv",
            ["ataraxia", "-s", "strategy.py", "-d", "shards", "-o", str(output)],
        ),
        patch("ataraxia.cli.backtest_dir", return_value=results),
    ):
        main()

    captured = capsys.readouterr()
    assert captured.err == ""
    assert "Realized PnL   = 80" in captured.out
    saved = json.loads(output.read_text())
    assert saved[0]["account"] == {"pnl": 30, "unrealized_pnl": -40}
    assert len(saved[0]["open_positions"]) == 1
    assert saved[1]["open_positions"] == []


def test_save_results(broker_returns, tmp_path: Path):
    output = tmp_path / "out.json"

    save_results(broker_returns, output)

    assert json.loads(output.read_text()) == [
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
