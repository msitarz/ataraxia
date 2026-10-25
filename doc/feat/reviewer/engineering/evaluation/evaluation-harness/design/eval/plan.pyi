# SPDX-License-Identifier: Apache-2.0
"""Pure prompt composition and ordered matrix planning boundary."""

from typing import Protocol

from .model import FrozenInputs, FrozenPlan, HarnessConfig

class PlanBuilder(Protocol):
    """Pure composer and matrix planner; performs no I/O."""

    def plan(self, inputs: FrozenInputs, config: HarnessConfig, /) -> FrozenPlan:
        """Compose exact snapshot bytes and return the complete ordered plan."""
        ...
