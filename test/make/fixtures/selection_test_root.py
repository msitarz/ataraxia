# SPDX-License-Identifier: Apache-2.0
"""Named nested-pytest witnesses copied into the disposable test root."""

import pytest


@pytest.mark.covers(work="test/selection/README.md", ac="AC-1")
def test_work_first_criterion_test_root() -> None:
    """Supply one successful selection witness in the test root."""
    # Given: this named fixture case belongs to the selected Work/criterion.

    # When: nested pytest executes the selected case.

    # Then: execution completes without failure.
    pass


@pytest.mark.covers(work="other/README.md", ac="AC-1")
def test_other_work_is_excluded() -> None:
    """Fail if an unrelated Work is ever executed."""
    # Given: this named fixture case belongs to an unrelated Work.

    # When: nested pytest incorrectly executes the case.

    # Then: fail visibly because the selection included an unrelated Work.
    raise AssertionError("a different Work was selected")
