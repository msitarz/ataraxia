# SPDX-License-Identifier: Apache-2.0
"""Historical reviewed design sketch; runtime contract lives in script/eval/plan.py."""

from typing import Protocol

from .model import FrozenInputs, FrozenPlan, HarnessConfig

class PlanBuilder(Protocol):
    """Pure composer and matrix planner; performs no I/O."""

    def plan(self, inputs: FrozenInputs, config: HarnessConfig, /) -> FrozenPlan:
        """Compose exact snapshot bytes and return the complete ordered plan."""
        ...
