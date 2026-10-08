# SPDX-License-Identifier: Apache-2.0
"""Marker declaration whose selected criterion is not a literal."""

import pytest

criterion = "AC-1"


@pytest.mark.covers(work="doc/example/README.md", ac=criterion)
def test_declares_dynamic_criterion_marker() -> None:
    pass
