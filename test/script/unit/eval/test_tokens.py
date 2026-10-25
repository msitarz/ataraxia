# SPDX-License-Identifier: Apache-2.0
"""Intent placeholder for separate context and instruction estimates."""

import pytest


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason="not implemented: AC-1 explicit dry-run estimate bases",
)
def test_estimates_keep_configured_instructions_separate_from_context() -> None:
    """Never count unavailable Codex defaults as supplied context."""
    # Given
    # A plan with composed context and either a configured or omitted instruction.

    # When
    # The estimator builds one report entry for each scheduled call.

    # Then
    # Configured instructions have a separate estimate; default bytes are unknown.
    pass
