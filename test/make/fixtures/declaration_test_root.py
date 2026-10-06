# SPDX-License-Identifier: Apache-2.0
"""Static marker witnesses whose execution must never occur during ac-check."""

import pytest


@pytest.mark.covers(work="test/declarations/README.md", ac="AC-1")
def test_output_remains_stable() -> None:
    """Fail visibly if declaration checking executes this fixture test."""
    # Given: this literal marker is input to static declaration checking.

    # When: a defect causes execution instead of static inspection.

    # Then: fail so the enclosing Make boundary test detects execution.
    raise AssertionError("ac-check executed a test")


@pytest.mark.covers(work="other/README.md", ac="AC-9")
def test_other_work_is_historical_or_unrelated() -> None:
    """Provide an unrelated literal marker for exclusion."""
    # Given: this marker belongs to an unrelated Work.

    # When: declaration checking inspects this source.

    # Then: the unrelated marker does not affect the selected Work's summary.
    pass
