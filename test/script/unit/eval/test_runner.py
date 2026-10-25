# SPDX-License-Identifier: Apache-2.0
"""Intent placeholder for effective-call identity semantics."""

import pytest


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason="not implemented: AC-2 effective identity stability and input sensitivity",
)
def test_effective_identity_tracks_effective_inputs_not_caching() -> None:
    """Separate stable effective identity from scheduled-position accounting."""
    # Given
    # Identical calls and variants that change context, instruction bytes,
    # separators, model, effort, CLI binding, or another invocation setting.

    # When
    # Effective-call identities are built for one run and for duplicate positions.

    # Then
    # Identical effective inputs keep identity; changed inputs change it. Run and
    # position association preserves duplicates; no cache reuse is implied.
    pass
