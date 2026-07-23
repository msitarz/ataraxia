# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Computable source nodes."""

from dataclasses import dataclass, field

from ataraxia.compute import Provider
from ataraxia.compute.protocol import DependencyMapping


class SourceRunner[T]:
    """Return stored item.

    Source runner is simply passing through the item that was fetched by the provider.
    Source node will set the item attribute via its send method.
    """

    item: T

    def __call__(self):
        """Return stored item."""
        return self.item


@dataclass(frozen=True)
class SourceNode[T]:
    """Generic source node for the computable graph.

    It simply passes through values from the provider to its dependents.
    """

    provider: Provider[T]
    runner: SourceRunner[T] = field(default_factory=SourceRunner)

    def deps(self) -> DependencyMapping:
        """Return no dependencies."""
        return {}

    def factory(self):
        """Return instance of the runner."""
        return self.runner

    def send(self, item: T):
        """Set item in the runner to be set for the compute graph."""
        self.runner.item = item

    def __iter__(self):
        return self.provider
