# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz


from dataclasses import dataclass
from typing import ClassVar

from ataraxia.di import compute_dependency_tree


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
