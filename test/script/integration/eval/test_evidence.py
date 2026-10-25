# SPDX-License-Identifier: Apache-2.0
"""Intent placeholders for exclusive and truthful run evidence."""

import pytest


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason="not implemented: AC-3 exclusive output and frozen run evidence",
)
def test_run_setup_is_exclusive_and_persists_configuration_before_dispatch() -> None:
    """Observe directory exclusion and durable pre-dispatch plan artifacts."""
    # Given
    # An existing destination and a separate new destination for a planned run.

    # When
    # The evidence store creates the run area before the first supervisor attempt.

    # Then
    # Existing output is refused and the new area retains the frozen plan/settings.
    pass


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason="not implemented: AC-3 exact output, provenance, and partial evidence",
)
def test_attempt_records_preserve_raw_streams_and_missing_observations() -> None:
    """Keep empty, absent, partial, and failed evidence distinct and immutable."""
    # Given
    # Controlled attempts produce empty, partial, unavailable, or exact raw streams.

    # When
    # The evidence store finalizes attempt records and their stream artifacts.

    # Then
    # Provenance, settings, cleanup, timestamps, and available telemetry stay truthful.
    pass
