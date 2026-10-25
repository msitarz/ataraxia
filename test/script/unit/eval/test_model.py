# SPDX-License-Identifier: Apache-2.0
"""Intent placeholder for strict harness configuration boundaries."""

import pytest


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason="not implemented: AC-2 strict immutable configuration validation",
)
def test_configuration_rejects_coercion_extras_and_invalid_limits() -> None:
    """Keep strict constraints, including booleans, finite limits, and zero cap."""
    # Given
    # Configurations include extra fields, bool-as-int values, and boundary limits.

    # When
    # Strict configuration records are validated and serialized.

    # Then
    # Invalid values fail while a zero output allowance remains valid.
    pass
