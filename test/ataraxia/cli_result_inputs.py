# SPDX-License-Identifier: Apache-2.0
"""Typed, retained result inputs and independent CLI JSON expectations."""

import json
from pathlib import Path

from ataraxia.bar import Bar
from ataraxia.broker import Account, BrokerReturn, Position


def broker_returns() -> tuple[BrokerReturn, BrokerReturn]:
    """Return the retained closed/open positions and their two accounts."""
    first_entry = Bar(timestamp=1, open=100, high=150, low=50, close=75, volume=2)
    first_close = Bar(timestamp=2, open=80, high=130, low=20, close=45, volume=2)
    first_position = Position(
        side="sell", stop_loss=150, take_profit=45, entry_bar=first_entry
    )
    first_position.close(first_close, level=45, pnl=30)

    second_entry = Bar(timestamp=3, open=100, high=200, low=50, close=150, volume=10)
    second_position = Position(
        side="buy", stop_loss=90, take_profit=500, entry_bar=second_entry
    )

    third_entry = Bar(timestamp=4, open=200, high=300, low=100, close=250, volume=10)
    third_close = Bar(timestamp=5, open=250, high=400, low=150, close=175, volume=10)
    third_position = Position(
        side="buy", stop_loss=100, take_profit=300, entry_bar=third_entry
    )
    third_position.close(third_close, level=300, pnl=50)

    return (
        {
            "account": Account(pnl=30, unrealized_pnl=-40),
            "closed_positions": [first_position],
            "open_positions": [second_position],
        },
        {
            "account": Account(pnl=50, unrealized_pnl=0),
            "closed_positions": [third_position],
            "open_positions": [],
        },
    )


def load_reporting_expected() -> object:
    """Load the reviewed JSON as an opaque whole-value expectation."""
    path = Path(__file__).parent / "fixtures" / "cli" / "reporting_expected.json"
    return json.loads(path.read_text(encoding="utf-8"))
