# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
from dataclasses import dataclass
from typing import NamedTuple, Protocol, runtime_checkable

import pytest

from ataraxia.compute_old import (
    Computable,
    Runner,
    _ComputeMeta,
    _is_dataclass_frozen,
)


def test_is_dataclass_frozen():
    @dataclass(frozen=True)
    class FrozenDataclass:
        pass

    assert _is_dataclass_frozen(FrozenDataclass)

    @dataclass
    class Dataclass:
        pass

    assert not _is_dataclass_frozen(Dataclass)

    class SimpleClass:
        pass

    assert not _is_dataclass_frozen(SimpleClass)


def test_compute_meta():
    @runtime_checkable
    class Prot(Protocol, metaclass=_ComputeMeta):
        attr: int

        def meth(self): ...

    class NotDataclass:
        attr: int

        def meth(self):
            return 1

    with pytest.raises(TypeError):
        isinstance(NotDataclass(1), Prot)

    @dataclass(frozen=True)
    class Dataclass:
        attr: int

        def meth(self):
            return 2

    assert isinstance(Dataclass(1), Prot)

    @dataclass(frozen=True)
    class InvalidImpl:
        attr: int

        def wrong_meth(self):
            return 3

    assert not isinstance(InvalidImpl(1), Prot)

    @dataclass
    class InvalidImplNotFrozen:
        attr: int

        def wrong_meth(self):
            return 4

    assert not isinstance(InvalidImplNotFrozen(1), Prot)


@pytest.fixture
def valid_compute_classes():
    class FeatureParams(NamedTuple):
        period: int

    @dataclass(frozen=True)
    class Feature:
        period: int

        def __call__(self, bar: float):
            return bar + self.period

    @dataclass(frozen=True)
    class FeatureSpec:
        init_params: FeatureParams
        compute_node: Runner = Feature

        def dependencies(self):
            return ()

        def factory(self):
            return Feature(*self.init_params)

    return (FeatureParams, Feature, FeatureSpec)


def test_isinstance_of_computable(valid_compute_classes):
    FeatureParams, Feature, FeatureSpec = valid_compute_classes

    feature_spec = FeatureSpec(FeatureParams(12))

    assert isinstance(feature_spec, Computable)

    class NotDataclass:
        init_params: FeatureParams
        compute_node: Runner = Feature

        def __init__(self, init_params, compute_node):
            self.init_params = init_params
            self.compute_node = compute_node

        def dependencies(self):
            return ()

        def factory(self):
            return Feature(*self.init_params)

    not_dataclass_spec = NotDataclass(FeatureParams(12), Feature)

    with pytest.raises(TypeError):
        isinstance(not_dataclass_spec, Computable)
