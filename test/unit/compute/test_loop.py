# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
from dataclasses import dataclass
from operator import itemgetter

import pytest

from ataraxia.compute.loop import kickstart_runners


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


def test_kickstart_instances(single_dep):
    A, B, ARunner, BRunner = itemgetter("A", "B", "ARunner", "BRunner")(single_dep)

    sorted_graph = (B(), A())

    assert kickstart_runners(sorted_graph) == {B(): BRunner(), A(): ARunner()}
