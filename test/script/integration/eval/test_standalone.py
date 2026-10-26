# SPDX-License-Identifier: Apache-2.0
"""Intent placeholder for unattended external invocation."""

import pytest


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason=(
        "not implemented: AC-8 standalone entry point has explicit unattended "
        "prerequisites and exit meanings"
    ),
)
def test_module_entry_point_runs_without_conversation_or_approval_prompts() -> None:
    """Exercise the documented command in a controlled subprocess environment."""
    # Given
    # A prepared environment, unattended CLI authentication/configuration, and
    # an explicit output destination, plus cases with missing prerequisites.

    # When
    # The documented `python -m script.eval` invocation runs in a subprocess.

    # Then
    # It needs no agent conversation or interactive approval, reports complete
    # success, failure, cancellation, and incomplete evidence distinctly, and
    # missing prerequisites fail explicitly without broadening permissions.
    pass
