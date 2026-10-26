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


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason="not implemented: AC-9 progress projection and disjoint accounting",
)
def test_progress_projection_partitions_calls_attempts_and_probes() -> None:
    """Derive one truthful snapshot without combining different work units."""
    # Given
    # Queued and stopped calls, concurrent active calls, per-call capacity
    # waits, successful, failed, and cancelled calls, retries, quota probes,
    # and an evidence-write failure for a call, attempt, or probe outcome.

    # When
    # The coordinator projects its plan and lifecycle into one progress snapshot.

    # Then
    # Call states partition the frozen plan; attempt and probe counts remain
    # separate; one backoff does not hide other active calls; retries do not add
    # calls; and a successful process is never a reviewer PASS claim. Stopped
    # calls remain unexecuted remaining work, distinct from queued work; final
    # cancellation and incomplete evidence reconcile without claiming unwritten
    # outcomes.
    pass


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason=(
        "not implemented: AC-9 progress uses source quota percentage and age "
        "without extra reads"
    ),
)
def test_progress_preserves_quota_percentage_age_and_unknown_values() -> None:
    """Project only supplied usage and producer-time quota observations."""
    # Given
    # Used-percent, remaining-percent, missing and out-of-range values with
    # old, missing, future, invalid, and absent producer timestamps.

    # When
    # Progress snapshots are produced and the same source observations reread.

    # Then
    # Percentages normalize only from valid supplied values; age comes from the
    # producer time and never resets on reread; stale, missing, future, and
    # invalid ages remain unknown; reporting performs no quota reads or probes.
    pass
