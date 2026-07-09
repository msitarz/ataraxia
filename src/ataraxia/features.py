# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Features module.

Provide basic features for the computation model.
"""

from collections import deque
from dataclasses import dataclass
from typing import ClassVar, NamedTuple, override

from ataraxia.bar import Bar
from ataraxia.compute import ComputableNode, ComputableSpec

# ================
# Bar Compute Node
# ================


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


# ===========================
# Rolling Window Compute Node
# ===========================


class RollingWindowParams(NamedTuple):
    """Parameters for RollingWindow specification."""

    maxlen: int


class RollingWindowNode[T](ComputableNode[[T], tuple[T, ...]]):
    """Container node implementing rolling window."""

    queue: deque[T]

    def __init__(self, maxlen: int):
        self.queue = deque(maxlen=maxlen)

    def __call__(self, item: T):
        """Accumulate item.

        Returns:
            Accumulated items in a tuple.
        """
        self.queue.appendleft(item)
        return tuple(self.queue)
