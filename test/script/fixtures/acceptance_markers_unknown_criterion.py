# SPDX-License-Identifier: Apache-2.0
"""Marker declaration referencing an undeclared Work criterion."""

import pytest


@pytest.mark.covers(work="doc/example/README.md", ac="AC-9")
def test_declares_unknown_criterion_marker() -> None:
    pass
