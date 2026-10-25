# SPDX-License-Identifier: Apache-2.0
"""Intent placeholder for caller-owned manual subset reruns."""

import pytest


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason="not implemented: AC-5 new subset runs preserve caller experiment ownership",
)
def test_manual_subset_uses_new_evidence_without_prior_run_scanning() -> None:
    """Keep subset selection and cross-run budget policy with the caller."""
    # Given
    # Prior run artifacts and a caller-selected subset for a fresh invocation.

    # When
    # The caller starts that subset in a new output directory.

    # Then
    # Original artifacts remain unchanged; the runner does not scan or infer prior
    # attempts. The caller continues applying any budget policy outside this runner.
    pass
