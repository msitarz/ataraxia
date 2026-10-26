# SPDX-License-Identifier: Apache-2.0
"""Historical reviewed port sketch; runtime wiring is in script/eval/tokens.py."""

from typing import Protocol

from .model import EstimateBasis, TokenEstimate

class TokenEstimator(Protocol):
    """Local estimator port; it cannot dispatch model calls."""

    def estimate(
        self, content: bytes, model: str, basis: EstimateBasis, /
    ) -> TokenEstimate:
        """Return an estimate or explicit unknown for the supplied bytes."""
        ...
