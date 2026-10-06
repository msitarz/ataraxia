# SPDX-License-Identifier: Apache-2.0
"""Named nested-pytest witnesses copied into the disposable example root."""

import pytest


@pytest.mark.covers(work="test/selection/README.md", ac="AC-1")
def test_work_first_criterion_example_root() -> None:
    """Supply the first criterion's successful example-root witness."""
    # Given: this named fixture case belongs to the selected Work/criterion.

    # When: nested pytest executes the selected case.

    # Then: execution completes without failure.
    pass


@pytest.mark.covers(work="test/selection/README.md", ac="AC-2")
def test_work_second_criterion_example_root() -> None:
    """Supply the second criterion's successful example-root witness."""
    # Given: this named fixture case belongs to the selected Work/criterion.

    # When: nested pytest executes the selected case.

    # Then: execution completes without failure.
    pass
