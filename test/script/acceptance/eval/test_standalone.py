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


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason=(
        "not implemented: AC-9 standalone progress uses stderr, terminal-aware "
        "output, and explicit quiet mode"
    ),
)
def test_standalone_progress_preserves_stdout_and_quiet_contract() -> None:
    """Check the command's reporting promise without model calls."""
    # Given
    # Controlled successful, failed, cancelled, and incomplete runs, with TTY,
    # redirected stderr, and explicit quiet-mode invocations.

    # When
    # The documented standalone command executes each case without model calls.

    # Then
    # Progress appears on stderr; stdout remains the normal/dry-run report;
    # redirected output has no ANSI escapes and keeps meaningful final status;
    # quiet suppresses progress without changing exit status or evidence.
    pass
