# SPDX-License-Identifier: Apache-2.0
from typing import assert_type

from ataraxia.bar import Bar
from ataraxia.compute import Computable, Runner, Sink
from ataraxia.compute.loop import ComputedMapping, compute, compute_step, prime_catalog
from ataraxia.feature import RollingWindow, Sma, sma
from ataraxia.source import SourceNode


def contracts(
    integer: Computable[[], int],
    text: Computable[[], str],
    source: SourceNode[Bar],
    sink: Sink[..., int],
    runner: Runner[[int], str],
) -> None:
    results = compute_step((integer, text), prime_catalog((integer, text)))
    assert_type(results, ComputedMapping)
    assert_type(results[integer], int)
    assert_type(results[text], str)
    assert_type(next(compute(sink))[sink], int)
    window = RollingWindow(integer, 3)
    assert_type(window, RollingWindow[int])
    assert_type(results[window], tuple[int, ...])
    assert_type(results[RollingWindow[int](integer, 3)], tuple[int, ...])
    assert_type(results[Sma(source, 3)], float | None)
    assert_type(sma((2, 3, None), 3), float | None)
    assert_type(sma((2.0, 3.0), 2), float | None)
    sma(("wrong",), 1)  # E: is not assignable
    assert_type(source.factory()(), Bar)
    assert_type(runner(1), str)
    wrong: str = results[integer]  # E: is not assignable
    runner("wrong")  # E: is not assignable
    Sma(integer, 3)  # E: is not assignable
    source.send("wrong")  # E: is not assignable
    results[integer] = 1  # E: Cannot set item
    results["wrong"]  # E: is not assignable
    assert wrong
