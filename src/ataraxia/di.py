# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Dependency injection module."""

from graphlib import CycleError, TopologicalSorter
from typing import Any, NamedTuple

from ataraxia.bar import Bar
from ataraxia.compute import ComputableNode, ComputableSpec

type DependencyTreeNode = ComputableSpec[..., Any, NamedTuple | None] | type
type DependencyTreeNodeTuple = tuple[DependencyTreeNode, ...]
type DependencyTree = dict[DependencyTreeNode, DependencyTreeNodeTuple]


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


def sort_dependency_tree(tree: DependencyTree) -> DependencyTreeNodeTuple:
    """Sort dependency `tree`.

    Takes the tree computed via `compute_dependency_tree`, sorts it checking for
    CycleError and returns a flat tuple of nodes.  This tuple will be processed.

    Arg:
        tree: Dependency tree returned from `compute_dependency_tree`.

    Returns:
        Tuple of sorted dependency nodes.

    Raises:
        CycleError: When dependencies form a cyclic graph.
    """
    ts = TopologicalSorter(tree)
    try:
        return tuple(ts.static_order())
    except CycleError as e:
        e.add_note("Compute specifications cannot reference each other")
        raise


def instantiate_compute_nodes(dependencies: DependencyTreeNodeTuple):
    """Return a mapping of specification to instantiated compute node.

    Raises:
        TypeError: When one of dependencies is neither ComputableSpec or type.
    """
    catalog: dict[DependencyTreeNode, ComputableNode[..., Any] | None] = {}

    for dep in dependencies:
        if isinstance(dep, type):
            catalog[dep] = None
        elif isinstance(dep, ComputableSpec):
            catalog[dep] = dep.factory()
        else:
            raise TypeError("Dependency must be a class or a specification instance")

    return catalog


def inject_dependencies(bar: Bar):
    """Inject dependencies starting with variables in the loop.

    This function moves the computation tree by one step within the loop.  Currently
    supports looping over bar values of a single instrument only.

    Args:
        bar: Current Bar instance in the computation loop.

    Returns:
        Computation tree results of each dependency.

    Raises:
        ValueError: When dependency
    """
    pass
