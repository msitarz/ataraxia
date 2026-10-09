# SPDX-License-Identifier: Apache-2.0
"""Typed, retained result inputs and independent CLI JSON expectations."""

import json
from pathlib import Path
from typing import Literal, TypedDict, TypeIs

from ataraxia.bar import Bar
from ataraxia.broker import Account, BrokerReturn, Position


class BarJSON(TypedDict):
    """Serialized Bar fields."""

    timestamp: int
    open: int
    high: int
    low: int
    close: int
    volume: int


class PositionJSON(TypedDict):
    """Complete serialized Position fields."""

    side: Literal["buy", "sell"]
    stop_loss: int
    take_profit: int
    entry_bar: BarJSON
    entry_level: int
    closing_bar: BarJSON | None
    closing_level: int | None
    closing_pnl: int | None


class AccountJSON(TypedDict):
    """Serialized Account fields."""

    pnl: int
    unrealized_pnl: int


class BrokerReturnJSON(TypedDict):
    """Complete serialized broker result fields."""

    account: AccountJSON
    closed_positions: list[PositionJSON]
    open_positions: list[PositionJSON]


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


def load_reporting_expected() -> list[BrokerReturnJSON]:
    """Load and validate the complete expected JSON at its file boundary."""
    path = Path(__file__).parent / "fixtures" / "cli" / "reporting_expected.json"
    raw: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("reporting expectation must be a JSON array")
    valid = [item for item in raw if _is_broker_return(item)]
    if len(valid) != len(raw):
        raise ValueError("reporting expectation does not match its complete schema")
    return valid


def _is_object(value: object, fields: set[str]) -> TypeIs[dict[str, object]]:
    return (
        isinstance(value, dict)
        and value.keys() == fields
        and all(isinstance(key, str) for key in value)
    )


def _is_integer(value: object) -> bool:
    return type(value) is int


def _is_bar(value: object) -> TypeIs[BarJSON]:
    return _is_object(
        value, {"timestamp", "open", "high", "low", "close", "volume"}
    ) and all(_is_integer(value[key]) for key in value)


def _is_account(value: object) -> TypeIs[AccountJSON]:
    return _is_object(value, {"pnl", "unrealized_pnl"}) and all(
        _is_integer(item) for item in value.values()
    )


def _is_position(value: object) -> TypeIs[PositionJSON]:
    fields = {
        "side",
        "stop_loss",
        "take_profit",
        "entry_bar",
        "entry_level",
        "closing_bar",
        "closing_level",
        "closing_pnl",
    }
    if not _is_object(value, fields):
        return False
    return (
        value["side"] in ("buy", "sell")
        and _is_integer(value["stop_loss"])
        and _is_integer(value["take_profit"])
        and _is_bar(value["entry_bar"])
        and _is_integer(value["entry_level"])
        and (value["closing_bar"] is None or _is_bar(value["closing_bar"]))
        and (value["closing_level"] is None or _is_integer(value["closing_level"]))
        and (value["closing_pnl"] is None or _is_integer(value["closing_pnl"]))
    )


def _is_position_list(value: object) -> TypeIs[list[PositionJSON]]:
    return isinstance(value, list) and all(_is_position(item) for item in value)


def _is_broker_return(value: object) -> TypeIs[BrokerReturnJSON]:
    return (
        _is_object(value, {"account", "closed_positions", "open_positions"})
        and _is_account(value["account"])
        and _is_position_list(value["closed_positions"])
        and _is_position_list(value["open_positions"])
    )
