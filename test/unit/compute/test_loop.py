# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
from dataclasses import dataclass, field
from operator import itemgetter

import pytest

from ataraxia.compute import Runner, Source
from ataraxia.compute.loop import (
    compute,
    compute_step,
    computed_node_deps,
    prime_catalog,
)


@pytest.fixture
def single_dep():
    # Runners are also frozen dataclasses for easy assert

    @dataclass(frozen=True)
    class BRunner:
        def __call__(self):
            return 1

    @dataclass(frozen=True)
    class B:
        def deps(self):
            return {}

        def factory(self):
            return BRunner()

    @dataclass(frozen=True)
    class ARunner:
        def __call__(self, b: int):
            return b + 3

    @dataclass(frozen=True)
    class A:
        def deps(self):
            return {"b": B()}

        def factory(self):
            return ARunner()

    return {"BRunner": BRunner, "B": B, "ARunner": ARunner, "A": A}


def test_prime_catalog(single_dep):
    A, B, ARunner, BRunner = itemgetter("A", "B", "ARunner", "BRunner")(single_dep)

    sorted_graph = (B(), A())

    assert prime_catalog(sorted_graph) == {B(): BRunner(), A(): ARunner()}


def test_computed_node_deps(single_dep):
    A, B = itemgetter("A", "B")(single_dep)

    computed = {B(): B().factory()(), A(): ValueError("Shouldn't be here")}

    assert computed_node_deps(A(), computed) == {"b": 1}


def test_compute_step(single_dep):
    A, B = itemgetter("A", "B")(single_dep)

    nodes = (B(), A())
    catalog = {B(): B().factory(), A(): A().factory()}

    assert compute_step(nodes, catalog) == {B(): 1, A(): 4}


@pytest.fixture
def source_sink():
    class SrcRunner:
        def __call__(self):
            return self.next_item

    class TestProvider:
        def __enter__(self):
            return self

        def __exit__(self, _exc_type, _exc_value, _traceback):
            return False

        def __iter__(self):
            return (x for x in (1, 3))

    @dataclass(frozen=True)
    class Src:
        runner: Runner = field(default_factory=SrcRunner)

        def deps(self):
            return {}

        def factory(self):
            return self.runner

        def send(self, item):
            self.runner.next_item = item

        def provider(self):
            return TestProvider()

    @dataclass(frozen=True)
    class SnkRunner:
        def __call__(self, item: int):
            return item + 7

    @dataclass(frozen=True)
    class Snk:
        source: Source = field(default_factory=Src)

        def deps(self):
            return {"item": self.source}

        def factory(self):
            return SnkRunner()

        def sources(self):
            return (self.source,)

        def consumer(self):
            return None

    return {"Src": Src, "Snk": Snk}


def test_compute(source_sink):
    Snk = itemgetter("Snk")(source_sink)

    snk = Snk()

    computed = compute(snk)

    assert next(computed) == {snk.source: 1, snk: 8}
    assert next(computed) == {snk.source: 3, snk: 10}
