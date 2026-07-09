# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Features module.

Provide basic features for the computation model.
"""

from dataclasses import dataclass
from typing import ClassVar, override

from ataraxia.bar import Bar
from ataraxia.compute import ComputableNode, ComputableSpec


@dataclass(frozen=True)
class BarNode(ComputableNode[[], Bar]):
    """Current bar processed in the computation loop."""

    def __call__(self, bar: Bar):
        """Bar entry point in the computation tree.

        Returns:
            bar: the received input.
        """
        return bar


@dataclass(frozen=True)
class BarSpec(ComputableSpec[[], Bar]):
    """Compute specification for the current bar in the loop."""

    compute_node: ClassVar[type[BarNode]] = BarNode

    @override
    def dependencies(self):
        """Dependencies for bar are simply.

        Returns:
            Tuple with type Bar dependency for DI.
        """
        return (Bar,)
