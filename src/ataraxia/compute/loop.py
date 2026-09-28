# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Compute loop module."""

from annotationlib import Format
from collections.abc import Generator, Iterator, Mapping
from inspect import signature
from typing import Any, cast

from ataraxia.errors import DependencyError

from .graph import dependency_graph, sort_graph
from .protocol import Computable, Runner, Sink

type ComputableMapping = Mapping[Computable[..., Any], Runner[..., Any]]


class ComputedMapping(Mapping[Computable[..., Any], object]):
    """Read-only step results with node-specific lookup types.

    Heterogeneous storage is private: only execution can insert a result. Iteration
    and bulk Mapping operations cannot preserve individual node/value relationships.
    """

    def __init__(self) -> None:
        self._values: dict[Computable[..., Any], object] = {}

    def __getitem__[**P, R](self, node: Computable[P, R]) -> R:
        # Each entry is produced by that node's runner in _compute. Python cannot
        # express the existential node/result pairs in the heterogeneous dict.
        return cast(R, self._values[node])

    def __iter__(self) -> Iterator[Computable[..., Any]]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def _compute[R](self, node: Computable[..., R], runner: Runner[..., R]) -> None:
        deps = computed_node_deps(node, self)
        self._values[node] = runner(*(), **deps)


def prime_catalog(
    computables: tuple[Computable[..., Any], ...],
) -> ComputableMapping:
    """Return instantiated runners after validating keyword dependency wiring.

    Raises:
        DependencyError: When a runner cannot accept its dependency names or its
            signature cannot be inspected.
    """
    catalog = {}
    for node in computables:
        runner = node.factory()
        try:
            signature(runner, annotation_format=Format.STRING).bind(
                **dict.fromkeys(node.deps())
            )
        except (TypeError, ValueError) as exc:
            raise DependencyError(f"Invalid dependencies for {node!r}: {exc}") from exc
        catalog[node] = runner
    return catalog


def computed_node_deps(
    node: Computable[..., Any], computed: Mapping[Computable[..., Any], object]
) -> dict[str, object]:
    """Return node computed parameters as kwargs."""
    return {k: computed[dep] for k, dep in node.deps().items()}


def compute_step(
    nodes: tuple[Computable[..., Any], ...],
    catalog: ComputableMapping,
) -> ComputedMapping:
    """Perform a single computation step over the computable graph.

    This function moves the computation graph by one step within the loop.

    Args:
        nodes: Sorted computable graph nodes.
        catalog: Runners returned by prime_catalog for these nodes. Hand-built
            catalogs must preserve each node/factory relationship; the heterogeneous
            catalog type cannot enforce it.

    Returns:
        Computation results for each computable node.
    """
    computed = ComputedMapping()

    for node in nodes:
        computed._compute(node, catalog[node])

    return computed


def compute(sink: Sink[..., Any]) -> Generator[ComputedMapping]:
    """Yield each compute step for the sink in the computable graph.

    Preparation propagates DependencyError for invalid runner dependency wiring.
    """
    sources = sink.sources()

    if len(sources) != 1:
        raise NotImplementedError("Multi-source computable graph not implemented")

    source = sources[0]

    graph = dependency_graph(sink.consumer() or sink)
    nodes = sort_graph(graph)
    catalog = prime_catalog(nodes)

    with source:
        for item in source:
            source.send(item)
            yield compute_step(nodes, catalog)
