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
    deps = () if isinstance(spec, type) else spec.dependencies()

    if not tree:
        tree = {}

    if spec in tree:
        return tree

    tree[spec] = deps

    for dep in deps:
        compute_dependency_tree(dep, tree)

    return tree
