# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Invalid strategy module exporting a Strategy(None) instance."""

from dataclasses import dataclass

from ataraxia.bar import Bar
from ataraxia.compute.protocol import DependencyMapping, Source


class UnreachableRunner:
    """Describe the typed runner shape, which the invalid export never reaches."""

    def __call__(self, item: Bar) -> None:
        raise NotImplementedError("the invalid sink instance must be rejected")


@dataclass(frozen=True)
class Strategy:
    """Fixture-local sink shape with the retained invalid None source."""

    source: None

    def deps(self) -> DependencyMapping:
        raise NotImplementedError("the invalid sink instance must be rejected")

    def factory(self) -> UnreachableRunner:
        raise NotImplementedError("the invalid sink instance must be rejected")

    def sources(self) -> tuple[Source[Bar, ..., Bar], ...]:
        raise NotImplementedError("the invalid sink instance must be rejected")

    def consumer(self) -> None:
        raise NotImplementedError("the invalid sink instance must be rejected")


__sink__: Strategy = Strategy(None)
