# SPDX-License-Identifier: Apache-2.0
"""Intent placeholders for supervisor-backed scheduling and stop policy."""

import pytest


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason="not implemented: AC-4 concurrency stays bounded through cleanup",
)
def test_concurrent_calls_wait_for_each_attempt_cleanup_before_reusing_its_slot() -> (
    None
):
    """Observe real controlled processes through the existing supervisor boundary."""
    # Given
    # Several independent calls and attempts with different completion and cleanup.

    # When
    # The coordinator dispatches calls under the configured concurrency bound.

    # Then
    # A slot remains held through cleanup and retries wait for their own cleanup.
    pass


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason="not implemented: AC-3/AC-4 cancellation and recording failure stop safely",
)
def test_cancel_or_recording_failure_stops_and_accounts_for_unstarted_calls() -> None:
    """Preserve the original cancellation or exception while stopping new dispatch."""
    # Given
    # A controlled cancellation or an evidence-write failure during a multi-call run.

    # When
    # The supervisor returns lifecycle evidence or persistence fails.

    # Then
    # Stop latches before fallible recording, no new call starts, and run accounting
    # marks every remaining planned call not started.
    pass


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason="not implemented: AC-4 retry only declared infrastructure outcomes",
)
def test_retries_require_eligible_failure_and_never_reinterpret_zero_exit_content() -> (
    None
):
    """Keep output semantics outside retry policy and wait for safe cleanup."""
    # Given
    # Infrastructure failure, nonzero exit, and completed zero-exit outcomes.

    # When
    # Retry limits and explicit nonzero-exit opt-in govern another attempt.

    # Then
    # Zero-exit content is never retried semantically; unsafe stop reasons never retry.
    pass
