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
    reason="not implemented: AC-4 signals and task cancellation await active cleanup",
)
def test_interrupt_signals_and_task_cancel_wait_for_active_cleanup() -> None:
    """Exercise SIGINT, SIGTERM, and task cancellation with an active child."""
    # Given
    # Controlled attempts active when SIGINT, SIGTERM, or task cancellation occurs.

    # When
    # The stop hook latches shutdown while the supervisor owns the child lifecycle.

    # Then
    # No new attempt starts and cancellation does not bypass bounded active cleanup.
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
    reason="not implemented: AC-4 unsafe acquisition or cleanup latches a global stop",
)
def test_unsafe_acquisition_or_cleanup_prevents_every_later_dispatch() -> None:
    """Do not retry or continue after uncertain process ownership or unsafe cleanup."""
    # Given
    # An attempt returns acquisition-uncertain or cleanup evidence that forbids
    # dispatch.

    # When
    # The coordinator evaluates whether to start the next call or retry.

    # Then
    # It latches global stop and leaves later calls not started.
    pass


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason=(
        "not implemented: AC-4 cancellation, overflow, and recording failure "
        "never retry"
    ),
)
def test_cancellation_overflow_and_record_failure_are_not_retryable() -> None:
    """Keep all stop-triggering outcomes outside ordinary retry eligibility."""
    # Given
    # Cancellation, positive-cap output overflow, or attempt-recording failure.

    # When
    # A nonzero retry limit is configured and one of those outcomes occurs.

    # Then
    # No subsequent attempt is dispatched for that call.
    pass


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason="not implemented: AC-3/AC-4 stop hook precedes failed attempt recording",
)
def test_stop_hook_latches_before_attempt_recording_failure() -> None:
    """Observe actual supervisor stop-hook wiring before persistence fails."""
    # Given
    # A real supervisor outcome that requests DispatchStop and an evidence store
    # whose next attempt-record write fails.

    # When
    # call_supervisor forwards the stop request before the coordinator records it.

    # Then
    # The global latch is set before the fallible write; original control flow and
    # truthful not-started accounting survive.
    pass


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason="not implemented: AC-4 positive output caps overflow while zero is uncapped",
)
def test_positive_output_cap_overflows_but_zero_cap_keeps_capturing() -> None:
    """Make the supervisor's bounded and uncapped capture modes explicit."""
    # Given
    # Controlled children emit the same stream under a positive cap and a zero cap.

    # When
    # Both requests run through the existing supervisor capture boundary.

    # Then
    # The positive cap overflows safely while zero disables the cap and captures output.
    pass


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason="not implemented: AC-1 runtime model-effort rejection is a failed attempt",
)
def test_runtime_model_effort_rejection_is_failed_without_value_substitution() -> None:
    """Retain runtime CLI rejection under the originally requested values."""
    # Given
    # A syntactically valid requested model-effort pair rejected by the CLI.

    # When
    # The attempt runs with the resolved argv and records the CLI outcome.

    # Then
    # The attempt is failed and the requested model and effort remain unchanged.
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
