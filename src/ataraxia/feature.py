# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Basic features as computable nodes."""

from collections import deque


class RollingWindowRunner[T]:
    """Accumulate items.

    It accumulates items in reverse chronological order, meaning the most recent item is
    at the start of returned tuple.
    """

    maxlen: int
    q: deque[T]

    def __init__(self, maxlen: int):
        self.maxlen = maxlen
        self.q = deque(maxlen=maxlen)

    def __call__(self, item: T) -> tuple[T, ...]:
        """Return accumulated items as a tuple."""
        self.q.appendleft(item)
        return tuple(self.q)
