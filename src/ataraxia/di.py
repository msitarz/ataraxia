# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Dependency injection module."""

from collections.abc import Generator, Iterable
from graphlib import CycleError, TopologicalSorter
from typing import Any

from ataraxia.bar import Bar
from ataraxia.compute import Computable, Runner

type DependencyTreeNode = Computable[..., Any] | type
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
    if not isinstance(spec, type) and not isinstance(spec, Computable):
        raise TypeError("Spec must implement ComputableSpec protocol or be a class")

    if isinstance(spec, Computable):
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


type ComputeCatalog = dict[DependencyTreeNode, Runner[..., object] | None]


def instantiate_compute_nodes(dependencies: DependencyTreeNodeTuple):
    """Return a mapping of specification to instantiated compute node.

    Raises:
        TypeError: When one of dependencies is neither ComputableSpec or type.
    """
    catalog: ComputeCatalog = {}

    for dep in dependencies:
        if isinstance(dep, type):
            catalog[dep] = None
        elif isinstance(dep, Computable):
            catalog[dep] = dep.factory()
        else:
            raise TypeError("Dependency must be a class or a specification instance")

    return catalog


type ComputationTree = dict[DependencyTreeNode, object]


def compute_step(
    bar: Bar,
    catalog: ComputeCatalog,
    dependencies: DependencyTreeNodeTuple,
    tree: DependencyTree,
):
    """Inject dependencies starting with variables in the loop.

    This function moves the computation tree by one step within the loop.  Currently
    supports looping over bar values of a single instrument only.

    Args:
        bar: Current Bar instance in the computation loop.
        catalog: Mapping of specifications to instantiated compute nodes.
        dependencies: sorted tuple of specifications.
        tree: Mapping of specifications to their dependencies.

    Returns:
        Computation tree results of each dependency.

    Raises:
        TypeError: When type dependency is not of Bar class or .
    """
    computations: ComputationTree = {}

    for dep in dependencies:
        if isinstance(dep, type):
            if type(bar) is not dep:
                raise TypeError("Dependency not supported", dep)
            computations[dep] = bar
            continue

        node = catalog[dep]
        send = tuple(computations[d] for d in tree[dep])

        if isinstance(node, Runner):
            computations[dep] = node(*send)
        else:
            raise TypeError("Specification factory must be return a ComputableNode")

    return computations


def compute(
    spec: Computable[..., Any], shard: Iterable[Bar]
) -> Generator[ComputationTree]:
    """Compute `shard` with `spec`.

    Args:
        spec: Root node in `DependencyTree`.
        shard: Data to process.  Currently only iterable that returns `Bar` is
            supported.

    Yields:
        `ComputationTree` of each iteration over `shard`.
    """
    tree = compute_dependency_tree(spec)
    deps = sort_dependency_tree(tree)
    catalog = instantiate_compute_nodes(deps)
    for bar in shard:
        yield compute_step(bar, catalog, deps, tree)
