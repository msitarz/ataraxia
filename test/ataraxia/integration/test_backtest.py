# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, override

import pytest

from ataraxia import backtest
from ataraxia.backtest import backtest_shard
from ataraxia.compute import Computable, Sink, compute
from ataraxia.compute.loop import ComputedMapping
from test.ataraxia.backtest_support import (
    BacktestObservation,
    arrange_backtest,
    expected_broker_strategy_result,
    observe_backtest_result,
)


class ConsumerBeforeSinkMapping(ComputedMapping):
    """Expose real computed results with the consumer before the sink."""

    def __init__(
        self,
        step: ComputedMapping,
        sink: Sink[..., Any],
        consumer: Computable[..., Any],
    ) -> None:
        self._step = step
        self._sink = sink
        self._consumer = consumer

    @override
    def __getitem__[**P, R](self, node: Computable[P, R]) -> R:
        return self._step[node]

    @override
    def __iter__(self) -> Iterator[Computable[..., Any]]:
        ordered: list[Computable[..., Any]] = [self._consumer]
        ordered.extend(
            node for node in self._step if node != self._consumer and node != self._sink
        )
        ordered.append(self._sink)
        return iter(ordered)

    @override
    def __len__(self) -> int:
        return len(self._step)


class ConsumerBeforeSinkCompute:
    """Adapt real compute steps and record their exposed key order."""

    def __init__(self) -> None:
        self.sink_node: Sink[..., Any] | None = None
        self.consumer_node: Computable[..., Any] | None = None
        self.orders: list[tuple[Computable[..., Any], ...]] = []

    def __call__(self, sink: Sink[..., Any]) -> Generator[ComputedMapping]:
        self.sink_node = sink
        consumer = sink.consumer()
        if consumer is None:
            raise AssertionError("the retained strategy must expose its broker")
        self.consumer_node = consumer

        for step in compute(sink):
            reordered = ConsumerBeforeSinkMapping(step, sink, consumer)
            self.orders.append(tuple(reordered))
            yield reordered


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/backtest/ordering/README.md",
    ac="AC-1",
)
def test_backtest_shard_uses_broker_result_from_compute_step(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Covers AC-1: select the broker result when it iterates before the sink."""
    # Given
    paths = arrange_backtest(tmp_path, monkeypatch, "broker_strategy.py")
    adapter = ConsumerBeforeSinkCompute()
    # backtest.py imports compute directly. This scoped adapter keeps the real
    # compute lifecycle and values while exposing their keys in a different order.
    monkeypatch.setattr(backtest, "compute", adapter)

    # When
    result = backtest_shard(paths.strategy_path, paths.shard_path)

    # Then
    assert adapter.sink_node is not None
    assert adapter.consumer_node is not None
    assert len(adapter.orders) == 1
    order = adapter.orders[0]
    assert order[0] == adapter.consumer_node
    assert order[-1] == adapter.sink_node
    observed: BacktestObservation = observe_backtest_result(result)
    assert observed == expected_broker_strategy_result(
        paths.shard_path, paths.strategy_path
    )
