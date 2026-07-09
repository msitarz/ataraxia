# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Dependency injection module."""

from typing import Any

from ataraxia.compute import ComputableSpec

type DependencyTreeNode = ComputableSpec[..., Any, Any] | type
type DependencyTree = dict[DependencyTreeNode, tuple[DependencyTreeNode, ...]]


def compute_dependency_tree(
    spec: DependencyTreeNode, tree: DependencyTree | None = None
) -> DependencyTree:
    """Return dependency tree of `entry_spec`."""
    if tree:
        if spec in tree:
            return tree

        if isinstance(spec, type):
            tree[spec] = ()
        else:
            tree[spec] = spec.dependencies()
    else:
        tree = {spec: ()} if isinstance(spec, type) else {spec: spec.dependencies()}

    if not isinstance(spec, type):
        for dep in spec.dependencies():
            compute_dependency_tree(dep, tree)

    return tree
