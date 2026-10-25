# SPDX-License-Identifier: Apache-2.0
"""Intent placeholder for caller-owned manual subset reruns."""

import pytest


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason="not implemented: AC-5 new subset runs preserve caller experiment ownership",
)
def test_manual_subset_uses_new_evidence_without_prior_run_scanning() -> None:
    """Do not infer resume state or own experiment budgets across invocations."""
    # Given
    # Prior run artifacts and caller-owned selection and budget inputs.

    # When
    # The caller starts a manual subset as a new invocation.

    # Then
    # A fresh destination is used without scanning old runs or changing caller budgets.
    pass
