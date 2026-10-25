# SPDX-License-Identifier: Apache-2.0
"""Intent placeholders for pure matrix composition and planning."""

import pytest


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason="not implemented: AC-1 deterministic Cartesian matrix composition",
)
def test_plan_orders_context_model_and_effort_products_deterministically() -> None:
    """Check default separators, explicit bytes, and repeated positions."""
    # Given
    # Ordered contexts with default and explicit separators plus repeated flags.

    # When
    # The pure planner composes every context, model, and effort combination.

    # Then
    # The full product has last-context-fastest order before model and effort
    # order; exact separator bytes and duplicate scheduled positions are retained.
    pass


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason="not implemented: AC-1 invalid separator values and placement",
)
def test_plan_refuses_unknown_or_dangling_separator_escapes() -> None:
    """Reject unsupported escapes rather than silently changing input bytes."""
    # Given
    # A separator contains an unknown escape or a dangling backslash.

    # When
    # The plan validates boundary bytes before building calls.

    # Then
    # Planning fails before any dispatch can begin.
    pass
