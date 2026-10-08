# SPDX-License-Identifier: Apache-2.0
"""Unchanged source fixture for a static Work marker declaration."""

import pytest


@pytest.mark.covers(work="doc/other/README.md", ac="AC-1")
def test_output_remains_stable() -> None:
    """Represent one collected declaration for the temporary Work."""
