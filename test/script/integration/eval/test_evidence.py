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


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason="not implemented: AC-2 attempted supervisor limits remain in evidence",
)
def test_attempt_record_retains_effective_deadline_grace_and_output_limit() -> None:
    """Trace request policy even for limits that are not CLI arguments."""
    # Given
    # A planned run with explicit execution, cleanup, grace, and output limits.

    # When
    # The actual AttemptRequest runs and its evidence is persisted.

    # Then
    # The record retains the limits used for that attempt, not later config values.
    pass


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason="not implemented: AC-2 staged instruction snapshot survives source edits",
)
def test_request_uses_staged_instructions_after_original_file_changes() -> None:
    """Prove the native setting targets frozen evidence, never a reopened source."""
    # Given
    # A clean tracked -i file frozen into the new evidence area.

    # When
    # The original source changes after freeze and the request is then constructed.

    # Then
    # argv maps -c model_instructions_file=PATH to the staged snapshot path and
    # execution remains based on the captured bytes.
    pass


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason="not implemented: AC-3 output destination containment and exclusivity",
)
def test_new_output_requires_external_or_ignored_location_before_any_launch() -> None:
    """Check destination policy before any artifacts or model process can exist."""
    # Given
    # New destinations inside the input repository (ignored and nonignored) and
    # outside it, plus already-existing destinations.

    # When
    # The evidence store prepares a run directory before supervisor dispatch.

    # Then
    # A new nonignored in-repository path is refused before writes or launch;
    # new ignored in-repository and external paths are accepted; existing paths
    # remain rejected without replacement.
    pass


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason="not implemented: AC-2 omitted instruction file preserves Codex defaults",
)
def test_omitted_instructions_file_adds_no_override_or_staged_artifact() -> None:
    """Retain default/unavailable metadata when the optional -i input is absent."""
    # Given
    # A clean planned invocation with no -i / --instructions-file setting.

    # When
    # The effective request is built and the frozen plan is persisted.

    # Then
    # argv has no model_instructions_file override, no instruction artifact is
    # staged, and metadata says defaults are preserved with automatic bytes
    # unavailable.
    pass
