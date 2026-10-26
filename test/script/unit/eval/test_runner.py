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
    """Reconcile disjoint progress outcomes without combining work units."""
    # Given
    # Queued and stopped calls, concurrent active calls, per-call capacity
    # waits, successful, failed, and cancelled calls, quota probes,
    # and an evidence-write failure for a call, attempt, or probe outcome.
    # Use 6 calls (2 succeeded, 1 failed, 1 cancelled, 1 stopped, 1 pending);
    # 5 dispatched attempts (2 succeeded, 1 failed, 1 cancelled, 1 pending);
    # and 5 dispatched probes (4 conclusive available/exhausted checks, 1
    # cancelled by shutdown).

    # When
    # The coordinator projects its plan and lifecycle into one progress snapshot.

    # Then
    # Call states partition the frozen plan; attempt and probe counts remain
    # separate and each attempt/probe counter reconciles exactly once across
    # disjoint active, evidence-pending, and terminal outcomes. A successful
    # zero-exit attempt is not a reviewer PASS claim. One backoff does not hide
    # other active calls; retries do not add calls. Stopped calls remain
    # unexecuted remaining work, distinct from queued work; cancellation and
    # incomplete evidence do not claim unwritten outcomes.
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
    # Already-normalized observations with known and unknown usage, an old
    # producer timestamp, missing/future/invalid timestamps, and an unknown
    # quota state whose age is still known.

    # When
    # Progress snapshots are produced and the same source observations reread.

    # Then
    # Progress preserves the normalized value and computes age from producer
    # time without resetting on reread. A valid stale timestamp has known age
    # even when the observation state is unknown; missing, future, and invalid
    # timestamps have unknown age. Reporting performs no reads or probes.
    pass


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason="not implemented: AC-9 Codex quota adapter normalizes supplied percentages",
)
def test_codex_quota_adapter_normalizes_supplied_percentages() -> None:
    """Keep raw percentage validation inside the Codex quota adapter."""
    # Given
    # A fake correlated quota source with valid used-percent, valid
    # remaining-percent, missing, and out-of-range raw values.

    # When
    # The Codex quota adapter maps the source windows into generic observations.

    # Then
    # Valid used values pass through, valid remaining values convert to used
    # percent, and missing or invalid values become unknown. Progress consumes
    # only these normalized observations and does not repeat source validation.
    pass
