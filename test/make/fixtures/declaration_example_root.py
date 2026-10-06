# SPDX-License-Identifier: Apache-2.0
"""Static example-root marker witness for declaration checking."""

import pytest


@pytest.mark.covers(work="test/declarations/README.md", ac="AC-1")
def test_output_remains_stable_in_example() -> None:
    """Provide a second selected marker from the example root."""
    # Given: this literal marker belongs to the selected Work.

    # When: declaration checking inspects this source.

    # Then: its marker contributes to the neutral declaration summary.
    pass
