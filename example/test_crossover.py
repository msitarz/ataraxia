# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Tests for example crossover strategy."""

import pytest

from ataraxia.bar import Bar
from ataraxia.broker import Signal

from .crossover import CrossoverRunner


@pytest.fixture
def bar() -> Bar:
    """Return bar fixture."""
    return Bar(timestamp=1, open=10, high=10, low=10, close=10, volume=10)


def test_crossover_on_cold_sma(bar: Bar) -> None:
    """Should not send signal when sma not warmed-up."""
    # Given
    # The bar fixture supplies the input and the runner starts fresh.
    runner = CrossoverRunner()

    # When
    result = runner(
        bar=bar,
        fast_sma=[10, 12],
        slow_sma=[12, None],
    )

    # Then
    assert result is None


def test_crossover_on_warm_sma_no_cross(bar: Bar) -> None:
    """Should not send signal if sma did not cross."""
    # Given
    # The bar fixture supplies the input and the runner starts fresh.
    runner = CrossoverRunner()

    # When
    result = runner(bar=bar, fast_sma=[11, 10], slow_sma=[13, 12])

    # Then
    assert result is None


def test_crossover_signal_on_sma_cross(bar: Bar) -> None:
    """Should not send signal if sma did not cross."""
    # Given
    # The bar fixture supplies the input and the runner starts fresh.
    runner = CrossoverRunner()

    # When
    signal = runner(bar=bar, fast_sma=[14, 10], slow_sma=[13, 12])

    # Then
    assert isinstance(signal, Signal)
