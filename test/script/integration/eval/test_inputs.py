# SPDX-License-Identifier: Apache-2.0
"""Intent placeholders for repository-backed input freezing."""

import pytest


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason="not implemented: AC-2 commit-checked context and instruction snapshots",
)
def test_context_and_instruction_snapshots_match_one_clean_commit() -> None:
    """Observe provenance at the read-only Git and filesystem boundary."""
    # Given
    # A clean disposable repository with tracked context and optional -i files.

    # When
    # The input freezer captures bytes, paths, blob IDs, and content digests.

    # Then
    # Every frozen byte sequence is attributed to the same repository HEAD.
    pass


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason=(
        "not implemented: AC-1/AC-2 refuse dirty, external, untracked, ignored, "
        "or raced inputs"
    ),
)
def test_input_freezing_refuses_invalid_membership_or_changed_bytes() -> None:
    """Refuse unsafe source selection before planning or model dispatch."""
    # Given
    # A dirty checkout or an external, ignored, untracked, or changed input path.

    # When
    # Context or configured instruction inputs are frozen for one invocation.

    # Then
    # The refusal identifies the invalid input and launches no CLI process.
    pass
