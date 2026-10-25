# SPDX-License-Identifier: Apache-2.0
"""Historical reviewed port; implemented by ``script.eval.inputs``."""

from typing import Protocol

from .model import FrozenInputs, HarnessConfig

class RepositoryReader(Protocol):
    """Read-only Git and source boundary; it does not compose or plan calls."""

    def freeze(self, config: HarnessConfig, /) -> FrozenInputs:
        """Validate repository inputs and return commit-checked snapshots."""
        ...
