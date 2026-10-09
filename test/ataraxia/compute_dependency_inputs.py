# SPDX-License-Identifier: Apache-2.0
"""Typed dependency nodes and runners for the small A/B graph."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class BRunner:
    """Produce the literal value consumed by A."""

    def __call__(self) -> int:
        return 1


@dataclass(frozen=True)
class B:
    """Leaf node whose runner produces one."""

    def deps(self) -> Mapping[str, B]:
        return {}

    def factory(self) -> BRunner:
        return BRunner()


@dataclass(frozen=True)
class ARunner:
    """Add three to the dependency value supplied as b."""

    def __call__(self, b: int) -> int:
        return b + 3


@dataclass(frozen=True)
class A:
    """Node that depends on B through the runner parameter named b."""

    b: B

    def deps(self) -> Mapping[str, B]:
        return {"b": self.b}

    def factory(self) -> ARunner:
        return ARunner()


def single_dependency() -> tuple[A, B]:
    """Return concrete A and B nodes linked by A's b dependency."""
    b = B()
    return A(b), b
