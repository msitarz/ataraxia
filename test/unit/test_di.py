# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
from dataclasses import dataclass
from graphlib import CycleError
from typing import ClassVar

import pytest

from ataraxia.di import compute_dependency_tree, sort_dependency_tree


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
