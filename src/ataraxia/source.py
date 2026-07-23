# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Computable source nodes."""


class SourceRunner[T]:
    """Return stored item.

    Source runner is simply passing through the item that was fetched by the provider.
    Source node will set the item attribute via its send method.
    """

    item: T

    def __call__(self):
        """Return stored item."""
        return self.item
