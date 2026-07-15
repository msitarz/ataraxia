# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Dependency injection module."""

from collections.abc import Generator, Iterable
from graphlib import CycleError, TopologicalSorter
from typing import Any

from ataraxia.bar import Bar
from ataraxia.compute import Computable, Runner

type DependencyGraphNode = Computable[..., Any] | type
type DependencyGraphNodeTuple = tuple[DependencyGraphNode, ...]
type DependencyGraph = dict[DependencyGraphNode, DependencyGraphNodeTuple]


def compute_dependency_graph(
    spec: DependencyGraphNode, _graph: DependencyGraph | None = None
) -> DependencyGraph:
    """Calculate dependency graph for `spec`.

    Args:
        spec: Root of the return dependency graph.x
        _graph: Leave out if calculating the graph from the root node.

    Returns:
        Dependency graph for `spec` root node.

    Raises:
        TypeError: if spec is neither Computable or type.
    """
    if not isinstance(spec, type) and not isinstance(spec, Computable):
        raise TypeError("Spec must implement Computable protocol or be a class")

    if isinstance(spec, Computable):
        deps = spec.dependencies()
        if not deps:
            raise TypeError("Spec dependencies cannot be empty")
    else:
        deps = ()

    if not isinstance(deps, tuple):
        raise TypeError("Dependencies must be a tuple")

    if not _graph:
        _graph = {}

    if spec in _graph:
        return _graph

    _graph[spec] = deps

    for dep in deps:
        compute_dependency_graph(dep, _graph)

    return _graph


def sort_dependency_graph(graph: DependencyGraph) -> DependencyGraphNodeTuple:
    """Sort dependency `graph`.

    Takes the graph computed via `compute_dependency_graph`, sorts it checking for
    CycleError and returns a flat tuple of nodes.  This tuple will be processed.

    Arg:
        graph: Dependency graph returned from `compute_dependency_graph`.

    Returns:
        Tuple of sorted dependency nodes.

    Raises:
        CycleError: When dependencies form a cyclic graph.
    """
    ts = TopologicalSorter(graph)
    try:
        return tuple(ts.static_order())
    except CycleError as e:
        e.add_note("Compute specifications cannot reference each other")
        raise


type ComputeCatalog = dict[DependencyGraphNode, Runner[..., object] | None]


def instantiate_compute_nodes(dependencies: DependencyGraphNodeTuple):
    """Return a mapping of specification to instantiated compute node.

    Raises:
        TypeError: When one of dependencies is neither Computable or type.
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


type ComputationGraph = dict[DependencyGraphNode, object]


def compute_step(
    bar: Bar,
    catalog: ComputeCatalog,
    dependencies: DependencyGraphNodeTuple,
    graph: DependencyGraph,
):
    """Inject dependencies starting with variables in the loop.

    This function moves the computation graph by one step within the loop.  Currently
    supports looping over bar values of a single instrument only.

    Args:
        bar: Current Bar instance in the computation loop.
        catalog: Mapping of specifications to instantiated compute nodes.
        dependencies: sorted tuple of specifications.
        graph: Mapping of specifications to their dependencies.

    Returns:
        Computation graph results of each dependency.

    Raises:
        TypeError: When type dependency is not of Bar class or .
    """
    computations: ComputationGraph = {}

    for dep in dependencies:
        if isinstance(dep, type):
            if type(bar) is not dep:
                raise TypeError("Dependency not supported", dep)
            computations[dep] = bar
            continue

        node = catalog[dep]
        send = tuple(computations[d] for d in graph[dep])

        if isinstance(node, Runner):
            computations[dep] = node(*send)
        else:
            raise TypeError("Specification factory must be return a ComputableNode")

    return computations


def compute(
    spec: Computable[..., Any], shard: Iterable[Bar]
) -> Generator[ComputationGraph]:
    """Compute `shard` with `spec`.

    Args:
        spec: Root node in `DependencyGraph`.
        shard: Data to process.  Currently only iterable that returns `Bar` is
            supported.

    Yields:
        `ComputationGraph` of each iteration over `shard`.
    """
    graph = compute_dependency_graph(spec)
    deps = sort_dependency_graph(graph)
    catalog = instantiate_compute_nodes(deps)
    for bar in shard:
        yield compute_step(bar, catalog, deps, graph)
