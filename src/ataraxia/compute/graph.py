# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Dependency graph module."""

from collections.abc import MutableMapping
import graphlib
from typing import Any

from ataraxia.errors import CycleError

from .protocols import Dependency

type Graph = MutableMapping[Dependency[..., Any], tuple[Dependency[..., Any], ...]]


def dependency_graph(computable: Dependency[..., Any], _graph: Graph | None = None):
    """Return dependency graph for `computable`."""
    if not _graph:
        _graph = {}

    if computable in _graph:
        return _graph

    _graph[computable] = tuple(computable.deps().values())

    for dep in computable.deps().values():
        dependency_graph(dep, _graph)

    return _graph


def sort_graph(graph: Graph) -> tuple[Dependency[..., Any], ...]:
    """Return sorted graph.

    Raises:
        CycleError: When dependencies depend on each other.
    """
    ts = graphlib.TopologicalSorter(graph)

    try:
        return tuple(ts.static_order())
    except graphlib.CycleError as e:
        raise CycleError("Cyclical dependency graph") from e
