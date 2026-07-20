# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
from dataclasses import dataclass
from operator import itemgetter

import pytest

from ataraxia.compute.graph import dependency_graph, sort_graph
from ataraxia.errors import CycleError


@pytest.fixture
def single_dep():
    class BRunner:
        def __call__(self):
            return 1

    @dataclass(frozen=True)
    class B:
        def deps(self):
            return {}

        def factory(self):
            return BRunner()

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


def test_dependency_graph_good_path(single_dep):
    A, B = itemgetter("A", "B")(single_dep)

    a = A()
    graph = dependency_graph(a)

    assert graph == {a: (B(),), B(): ()}


def test_sort_graph(single_dep):
    A, B = itemgetter("A", "B")(single_dep)

    graph = {A(): (B(),), B(): ()}

    assert sort_graph(graph) == (B(), A())


def test_sort_graph_cycle_error(single_dep):
    A, B = itemgetter("A", "B")(single_dep)

    graph = {A(): (B(),), B(): (A(),)}

    with pytest.raises(CycleError):
        sort_graph(graph)
