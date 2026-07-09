# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Dependency injection module."""

from typing import Any

from ataraxia.compute import ComputableSpec

type DependencyTreeNode = ComputableSpec[..., Any, Any] | type
type DependencyTree = dict[DependencyTreeNode, tuple[DependencyTreeNode, ...]]


def compute_dependency_tree(
    spec: DependencyTreeNode, _tree: DependencyTree | None = None
) -> DependencyTree:
    """Calculate dependency tree for `spec`.

    Args:
        spec: Root of the return dependency tree.x
        _tree: Leave out if calculating the tree from the root node.

    Returns:
        Dependency tree for `spec` root node.

    Raises:
        TypeError: if spec is neither ComputableSpec or type.
    """
    if not isinstance(spec, type) and not isinstance(spec, ComputableSpec):
        raise TypeError("Spec must implement ComputableSpec protocol or be a class")

    if isinstance(spec, ComputableSpec):
        deps = spec.dependencies()
        if not deps:
            raise TypeError("Spec dependencies cannot be empty")
    else:
        deps = ()

    if not isinstance(deps, tuple):
        raise TypeError("Dependencies must be a tuple")

    if not _tree:
        _tree = {}

    if spec in _tree:
        return _tree

    _tree[spec] = deps

    for dep in deps:
        compute_dependency_tree(dep, _tree)

    return _tree
