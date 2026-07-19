# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Compute loop module."""

from collections.abc import Mapping, MutableMapping
from typing import Any

from .graph import dependency_graph, sort_graph
from .protocols import Computable, Runner, Sink

type ComputableMapping = Mapping[Computable[..., Any], Runner[..., Any]]
type ComputedMapping = MutableMapping[Computable[..., Any], Any]


def prime_catalog(
    computables: tuple[Computable[..., Any], ...],
) -> ComputableMapping:
    """Return catalog of instantiated runners of computables."""
    return {c: c.factory() for c in computables}


def computed_node_deps(node: Computable[..., Any], computed: ComputedMapping):
    """Return node computed parameters as kwargs."""
    return {k: computed[dep] for k, dep in node.deps().items()}


def compute_step(
    nodes: tuple[Computable[..., Any], ...],
    catalog: ComputableMapping,
):
    """Perform a single computation step over the computable graph.

    This function moves the computation graph by one step within the loop.

    Args:
        nodes: Sorted computable graph nodes.
        catalog: Mapping of specifications to instantiated compute nodes.

    Returns:
        Computation results for each computable node.
    """
    computed: ComputedMapping = {}

    for node in nodes:
        runner = catalog[node]
        deps = computed_node_deps(node, computed)

        # Keep empty tuple unpacking as pyrefly otherwise reports [invalid-param-spec]
        computed[node] = runner(*(), **deps)

    return computed


def compute(sink: Sink[..., Any]):
    """Yield each compute step for the sink in the computable graph."""
    sources = sink.sources()

    if len(sources) != 1:
        raise NotImplementedError("Multi-source computable graph not implemented")

    source = sources[0]

    graph = dependency_graph(sink)
    nodes = sort_graph(graph)
    catalog = prime_catalog(nodes)

    for item in source:
        source.send(item)
        yield compute_step(nodes, catalog)
