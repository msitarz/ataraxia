# SPDX-License-Identifier: Apache-2.0
"""Consumer-owned local token-estimation port."""

from typing import Protocol

from .model import EstimateBasis, TokenEstimate

class TokenEstimator(Protocol):
    """Local estimator port; it cannot dispatch model calls."""

    def estimate(
        self, content: bytes, model: str, basis: EstimateBasis, /
    ) -> TokenEstimate:
        """Return an estimate or explicit unknown for the supplied bytes."""
        ...
