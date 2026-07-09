# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
from dataclasses import dataclass
from graphlib import CycleError
from typing import ClassVar, NamedTuple

import pytest

from ataraxia.bar import Bar
from ataraxia.di import (
    compute_dependency_tree,
    inject_dependencies,
    instantiate_compute_nodes,
    sort_dependency_tree,
)


def test_compute_dependency_tree_good_path():
    @dataclass(frozen=True)
    class ASpec:
        init_params: ClassVar = None
        compute_node: ClassVar = None

        def dependencies(self):
            return (int,)

        def factory(self):
            return None

    @dataclass(frozen=True)
    class EntrySpec:
        init_params: ClassVar = None
        compute_node: ClassVar = None

        def dependencies(self):
            return (ASpec(),)

        def factory(self):
            return None

    entry_spec = EntrySpec()

    deps = compute_dependency_tree(entry_spec)

    assert deps == {EntrySpec(): (ASpec(),), ASpec(): (int,), int: ()}


def test_compute_dependency_tree_type_as_entry():
    """Tests compute_dependency_tree when entry spec is a type."""
    deps = compute_dependency_tree(int)

    assert deps == {int: ()}


def test_compute_dependency_tree_error_not_computable_spec():
    # Error when spec is not a ComputableSpec
    class ASpec:
        pass

    with pytest.raises(TypeError):
        compute_dependency_tree(ASpec())


def test_compute_dependency_tree_error_not_a_class():
    # Error when spec is not a class
    with pytest.raises(TypeError):
        compute_dependency_tree(0)


def test_compute_dependency_tree_error_no_deps():
    # Error when spec doesn't have any dependencies
    @dataclass(frozen=True)
    class BSpec:
        init_params: ClassVar = None
        compute_node: ClassVar = None

        def dependencies(self):
            return ()

        def factory(self):
            return None

    with pytest.raises(TypeError):
        compute_dependency_tree(BSpec())


def test_compute_dependency_tree_error_deps_not_tuple():
    # Error when spec dependencies are not a tuple
    @dataclass(frozen=True)
    class CSpec:
        init_params: ClassVar = None
        compute_node: ClassVar = None

        def dependencies(self):
            return [int]

        def factory(self):
            return None

    with pytest.raises(TypeError):
        compute_dependency_tree(CSpec())


def test_sort_dependency_tree_good_path():
    @dataclass(frozen=True)
    class CSpec:
        init_params: ClassVar = None
        compute_node: ClassVar = None

        def dependencies(self):
            return (int,)

        def factory(self):
            return None

    @dataclass(frozen=True)
    class BSpec:
        init_params: ClassVar = None
        compute_node: ClassVar = None

        def dependencies(self):
            return (CSpec(),)

        def factory(self):
            return None

    @dataclass(frozen=True)
    class ASpec:
        init_params: ClassVar = None
        compute_node: ClassVar = None

        def dependencies(self):
            return (BSpec(), CSpec())

        def factory(self):
            return None

    tree = {
        ASpec(): ASpec().dependencies(),
        BSpec(): BSpec().dependencies(),
        CSpec(): CSpec().dependencies(),
        int: (),
    }

    deps = sort_dependency_tree(tree)

    assert deps == (int, CSpec(), BSpec(), ASpec())


def test_sort_dependency_tree_cycle_error():
    @dataclass(frozen=True)
    class BSpec:
        init_params: ClassVar = None
        compute_node: ClassVar = None

        def dependencies(self):
            return (ASpec(),)

        def factory(self):
            return None

    @dataclass(frozen=True)
    class ASpec:
        init_params: ClassVar = None
        compute_node: ClassVar = None

        def dependencies(self):
            return (BSpec(),)

        def factory(self):
            return None

    tree = {
        ASpec(): ASpec().dependencies(),
        BSpec(): BSpec().dependencies(),
    }

    with pytest.raises(CycleError):
        sort_dependency_tree(tree)


@pytest.fixture
def b_node():
    class BNodeParams(NamedTuple):
        x: float

    @dataclass(frozen=True)
    class BNode:
        x: float

        def __call__(self, bar):
            return bar.close + self.x

    @dataclass(frozen=True)
    class BSpec:
        init_params: BNodeParams
        compute_node: ClassVar = BNode

        def dependencies(self):
            return (Bar,)

        def factory(self):
            return self.compute_node(*self.init_params)

    return BNodeParams, BNode, BSpec


def test_instantiate_compute_nodes(b_node):
    BNodeParams, BNode, BSpec = b_node

    bspec8 = BSpec(BNodeParams(8))
    bspec9 = BSpec(BNodeParams(9))

    deps = (Bar, bspec8, bspec9)

    catalog = instantiate_compute_nodes(deps)

    assert isinstance(catalog, dict)

    assert catalog.get(Bar) is None

    assert isinstance(catalog.get(bspec8), BNode)
    assert catalog[bspec8].x == 8

    assert isinstance(catalog.get(bspec9), BNode)
    assert catalog[bspec9].x == 9


def test_instantiate_compute_nodes_error(b_node):
    class NotSpec:
        x: int

    with pytest.raises(TypeError):
        instantiate_compute_nodes((NotSpec(),))


def test_inject_dependencies(b_node):
    BNodeParams, _BNode, BSpec = b_node

    class ANode:
        def __call__(self, param1: float, param2: float):
            return param1 + param2

    @dataclass(frozen=True)
    class ASpec:
        init_params: ClassVar = None
        compute_node: ClassVar = ANode

        def dependencies(self):
            return (BSpec(BNodeParams(2)), BSpec(BNodeParams(6)))

        def factory(self):
            return self.compute_node()

    bar = Bar(3, 6)

    aspec = ASpec()
    bspec02 = BSpec(BNodeParams(2))
    bspec06 = BSpec(BNodeParams(6))

    tree = {
        aspec: aspec.dependencies(),
        bspec02: bspec02.dependencies(),
        bspec06: bspec06.dependencies(),
        Bar: (),
    }

    deps = (Bar, bspec02, bspec06, aspec)

    catalog = {
        Bar: None,
        aspec: aspec.factory(),
        bspec02: bspec02.factory(),
        bspec06: bspec06.factory(),
    }

    computed = inject_dependencies(bar, catalog, deps, tree)

    assert computed == {
        Bar: bar,
        bspec06: bar.close + 6,
        bspec02: bar.close + 2,
        aspec: bar.close + 2 + bar.close + 6,
    }
