# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

import pytest

from ataraxia.bar import Bar
from ataraxia.broker import Position, PositionOnBarReturn, Signal


@pytest.fixture
def long_signal() -> Signal:
    return Signal(side="buy", stop_loss=10, take_profit=30)


@pytest.fixture
def short_signal() -> Signal:
    return Signal(side="sell", stop_loss=29, take_profit=11)


@pytest.fixture
def entry_bar() -> Bar:
    return Bar(timestamp=1, open=20, high=30, low=15, close=25, volume=1)


@pytest.fixture
def long_position(long_signal: Signal, entry_bar: Bar) -> Position:
    return Position(
        entry_bar=entry_bar,
        side=long_signal.side,
        stop_loss=long_signal.stop_loss,
        take_profit=long_signal.take_profit,
    )


@pytest.fixture
def short_position(short_signal: Signal, entry_bar: Bar) -> Position:
    return Position(
        entry_bar=entry_bar,
        side=short_signal.side,
        stop_loss=short_signal.stop_loss,
        take_profit=short_signal.take_profit,
    )


def _assert_closing_state(position: Position, bar: Bar, level: int, pnl: int) -> None:
    assert position.closing_bar is bar
    assert position.closing_level == level
    assert position.closing_pnl == pnl


def _assert_open_state(position: Position) -> None:
    assert position.closing_bar is None
    assert position.closing_level is None
    assert position.closing_pnl is None


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/positions/README.md", ac="AC-1"
)
def test_position_init(long_position: Position) -> None:
    """Use the entry bar close as the long position's entry level."""
    # Given
    # The local signal and entry-bar fixtures construct a long position.

    # When
    position_values = (
        long_position.side,
        long_position.stop_loss,
        long_position.take_profit,
        long_position.entry_level,
    )

    # Then
    assert position_values == ("buy", 10, 30, 25)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/positions/README.md", ac="AC-1"
)
def test_position_on_bar_no_order_hit(long_position: Position) -> None:
    """Keep a long position open and report its close-price unrealized PnL."""
    # Given
    bar = Bar(timestamp=2, open=25, high=29, low=20, close=28, volume=2)

    # When
    result = long_position.on_bar(bar)

    # Then
    assert result == {"closed": False, "pnl": 3}
    _assert_open_state(long_position)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/positions/README.md", ac="AC-1"
)
@pytest.mark.parametrize(
    "bar",
    [
        Bar(timestamp=2, open=25, high=28, low=5, close=28, volume=2),
        Bar(timestamp=2, open=25, high=28, low=10, close=28, volume=2),
    ],
    ids=["inside-stop-range", "at-stop-boundary"],
)
def test_position_on_bar_stop_loss_hit(long_position: Position, bar: Bar) -> None:
    """Close a long position at its stop when the bar touches the stop level."""
    # Given
    # The table covers an interior stop price and equality at the lower edge.

    # When
    result = long_position.on_bar(bar)

    # Then
    assert result == {"closed": True, "pnl": -15}
    _assert_closing_state(long_position, bar, level=10, pnl=-15)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/positions/README.md", ac="AC-1"
)
def test_position_on_bar_stop_loss_hit_with_gap(long_position: Position) -> None:
    """Close a gapped long position at the bar open below its stop."""
    # Given
    bar = Bar(timestamp=2, open=5, high=5, low=1, close=2, volume=2)

    # When
    result = long_position.on_bar(bar)

    # Then
    assert result == {"closed": True, "pnl": -20}
    _assert_closing_state(long_position, bar, level=5, pnl=-20)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/positions/README.md", ac="AC-1"
)
def test_position_on_bar_take_profit_hit(long_position: Position) -> None:
    """Close a long position at its target when the bar touches that level."""
    # Given
    bar = Bar(timestamp=2, open=25, high=30, low=11, close=28, volume=2)

    # When
    result = long_position.on_bar(bar)

    # Then
    assert result == {"closed": True, "pnl": 5}
    _assert_closing_state(long_position, bar, level=30, pnl=5)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/positions/README.md", ac="AC-1"
)
def test_position_on_bar_take_profit_hit_with_gap(long_position: Position) -> None:
    """Close a gapped long position at the bar open above its target."""
    # Given
    bar = Bar(timestamp=2, open=35, high=40, low=33, close=38, volume=2)

    # When
    result = long_position.on_bar(bar)

    # Then
    assert result == {"closed": True, "pnl": 10}
    _assert_closing_state(long_position, bar, level=35, pnl=10)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/positions/README.md", ac="AC-1"
)
def test_position_on_bar_both_orders_hit(long_position: Position) -> None:
    """Give a touched long stop priority when the same bar reaches both orders."""
    # Given
    bar = Bar(timestamp=2, open=25, high=30, low=10, close=28, volume=2)

    # When
    result = long_position.on_bar(bar)

    # Then
    assert result == {"closed": True, "pnl": -15}
    _assert_closing_state(long_position, bar, level=10, pnl=-15)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/positions/README.md", ac="AC-1"
)
def test_position_on_bar_when_already_finished(long_position: Position) -> None:
    """Return the first close outcome and preserve its closing bar and fields."""
    # Given
    first_bar = Bar(timestamp=2, open=25, high=28, low=5, close=28, volume=2)
    long_position.on_bar(first_bar)
    later_bar = Bar(timestamp=3, open=25, high=35, low=20, close=28, volume=2)

    # When
    result = long_position.on_bar(later_bar)

    # Then
    assert result == {"closed": True, "pnl": -15}
    _assert_closing_state(long_position, first_bar, level=10, pnl=-15)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/positions/README.md", ac="AC-1"
)
def test_position_short_on_bar_take_profit_hit(short_position: Position) -> None:
    """Close a short position at its target when the bar touches that level."""
    # Given
    bar = Bar(timestamp=2, open=25, high=28, low=11, close=28, volume=2)

    # When
    result = short_position.on_bar(bar)

    # Then
    assert result == {"closed": True, "pnl": 14}
    _assert_closing_state(short_position, bar, level=11, pnl=14)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/positions/README.md", ac="AC-1"
)
def test_position_short_on_bar_take_profit_hit_with_gap(
    short_position: Position,
) -> None:
    """Close a gapped short position at the bar open below its target."""
    # Given
    bar = Bar(timestamp=2, open=5, high=6, low=1, close=4, volume=2)

    # When
    result = short_position.on_bar(bar)

    # Then
    assert result == {"closed": True, "pnl": 20}
    _assert_closing_state(short_position, bar, level=5, pnl=20)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/positions/README.md", ac="AC-1"
)
def test_position_short_on_bar_stop_loss_hit(short_position: Position) -> None:
    """Close a short position at its stop when the bar touches the stop level."""
    # Given
    bar = Bar(timestamp=2, open=25, high=29, low=11, close=28, volume=2)

    # When
    result = short_position.on_bar(bar)

    # Then
    assert result == {"closed": True, "pnl": -4}
    _assert_closing_state(short_position, bar, level=29, pnl=-4)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/positions/README.md", ac="AC-1"
)
def test_position_short_on_bar_stop_loss_hit_with_gap(
    short_position: Position,
) -> None:
    """Close a gapped short position at the bar open above its stop."""
    # Given
    bar = Bar(timestamp=2, open=35, high=40, low=30, close=38, volume=2)

    # When
    result = short_position.on_bar(bar)

    # Then
    assert result == {"closed": True, "pnl": -10}
    _assert_closing_state(short_position, bar, level=35, pnl=-10)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/positions/README.md", ac="AC-1"
)
def test_position_short_on_bar_closing_pnl(short_position: Position) -> None:
    """Retain the short stop's realized closing PnL and complete outcome."""
    # Given
    bar = Bar(timestamp=2, open=25, high=29, low=11, close=28, volume=2)

    # When
    result = short_position.on_bar(bar)

    # Then
    assert result == {"closed": True, "pnl": -4}
    _assert_closing_state(short_position, bar, level=29, pnl=-4)


@pytest.mark.parametrize(
    ("position", "bar", "expected_pnl"),
    [
        (
            Position(
                entry_bar=Bar(
                    timestamp=1, open=20, high=30, low=15, close=25, volume=1
                ),
                side="buy",
                stop_loss=10,
                take_profit=30,
            ),
            Bar(timestamp=2, open=25, high=29, low=11, close=28, volume=2),
            3,
        ),
        (
            Position(
                entry_bar=Bar(
                    timestamp=1, open=20, high=30, low=15, close=25, volume=1
                ),
                side="sell",
                stop_loss=29,
                take_profit=11,
            ),
            Bar(timestamp=2, open=25, high=28, low=12, close=27, volume=2),
            -2,
        ),
    ],
    ids=["long-inside-neighbor-prices", "short-inside-neighbor-prices"],
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/values/positions/README.md", ac="AC-1"
)
def test_position_stays_open_between_neighboring_order_prices(
    position: Position, bar: Bar, expected_pnl: int
) -> None:
    """Keep both sides open at the one-point neighbors inside their orders."""
    # Given
    # Each arrangement places both stop and target one point beyond the bar.

    # When
    result: PositionOnBarReturn = position.on_bar(bar)

    # Then
    assert result == {"closed": False, "pnl": expected_pnl}
    _assert_open_state(position)
