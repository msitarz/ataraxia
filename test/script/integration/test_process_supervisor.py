# SPDX-License-Identifier: Apache-2.0
"""Pending process-level specifications for the process-supervisor Work.

See ``doc/feat/reviewer/engineering/evaluation/process-supervisor/README.md``
for AC-1/AC-2/AC-3. These strict xfails are scenario specifications only; they
do not exercise or prove runtime behavior. Each placeholder raises only the
specific pending exception so unexpected errors remain failures.
"""

import pytest


@pytest.mark.parametrize(
    ("limit_case", "invalid_value"),
    [
        pytest.param("timeout", 0, id="zero-timeout"),
        pytest.param("cleanup timeout", -1, id="negative-cleanup-timeout"),
        pytest.param("timeout", float("nan"), id="nonfinite-timeout"),
        pytest.param("output cap", float("inf"), id="unbounded-output-cap"),
    ],
)
@pytest.mark.xfail(
    raises=NotImplementedError,
    reason="AC-1 pending: reject invalid invocation limits before launch",
    strict=True,
)
def test_invalid_or_unbounded_limits_refuse_to_launch(
    limit_case: str,
    invalid_value: int | float,
) -> None:
    """AC-1: invalid and nonfinite limits are rejected before child launch."""
    # Given
    # One invocation request has limit_case set to invalid_value.

    # When
    # The integrated caller submits it to the future one-attempt boundary.

    # Then
    # Launch must be refused, with no process acquired and no hidden retry.
    raise NotImplementedError(f"Pending observation for {limit_case}={invalid_value!r}")


@pytest.mark.parametrize(
    ("exit_code", "stdout", "stderr"),
    [
        pytest.param(0, b'{"ok":true}\n', b"warning\n", id="success"),
        pytest.param(7, b"partial\n", b"failed\n", id="nonzero-exit-7"),
    ],
)
@pytest.mark.xfail(
    raises=NotImplementedError,
    reason="AC-1 pending: preserve actual completion and stream observations",
    strict=True,
)
def test_completion_preserves_actual_exit_and_distinct_streams(
    exit_code: int,
    stdout: bytes,
    stderr: bytes,
) -> None:
    """AC-1: completed calls retain their actual status and bounded streams."""
    # Given
    # A disposable CLI emits the parameterized literal streams and exit code.

    # When
    # The integrated caller observes that CLI through one attempt.

    # Then
    # The result must retain the actual exit code and distinct bounded streams;
    # fields unavailable on an incomplete attempt must remain unavailable.
    raise NotImplementedError(
        f"Pending exit={exit_code}; stdout={stdout!r}; stderr={stderr!r}"
    )


@pytest.mark.parametrize(
    ("stdout", "stderr", "cap", "overflows"),
    [
        pytest.param(b"1234", b"5678", 8, False, id="exactly-at-cap"),
        pytest.param(b"12345", b"6789", 8, True, id="one-over-cap"),
    ],
)
@pytest.mark.xfail(
    raises=NotImplementedError,
    reason="AC-1 pending: enforce and report the combined stream cap",
    strict=True,
)
def test_combined_output_cap_distinguishes_exact_limit_from_overflow(
    stdout: bytes,
    stderr: bytes,
    cap: int,
    overflows: bool,
) -> None:
    """AC-1: stdout and stderr share one output allowance."""
    # Given
    # A disposable CLI writes the literal streams; in the overflow case each
    # stream is individually below cap while their combined size exceeds it.

    # When
    # The integrated caller captures output with the parameterized cap.

    # Then
    # Exactly-at-cap output is complete; overflow is visible, cannot succeed,
    # and retained prefixes total no more than cap bytes.
    raise NotImplementedError(
        f"Pending observation for streams={stdout!r}/{stderr!r}, cap={cap}, "
        f"overflows={overflows}"
    )


@pytest.mark.xfail(
    raises=NotImplementedError,
    reason="AC-1 pending: bound timeout with a descendant-held output pipe",
    strict=True,
)
def test_timeout_bounds_call_when_exited_leader_child_keeps_pipe_open() -> None:
    """AC-1: an exited leader cannot hide the still-open invocation pipe."""
    # Given
    # A disposable leader emits b"seen\n", exits zero, and leaves an owned
    # child holding stdout open.

    # When
    # The integrated invocation reaches its deadline.

    # Then
    # The result must report timeout, retain every observed output prefix and
    # leader status 0 if observed, and leave exit/time unavailable only when
    # those observations were genuinely unavailable.
    raise NotImplementedError("Pending observation for descendant-held pipe timeout")


@pytest.mark.parametrize(
    "terminal_outcome",
    [
        pytest.param("success", id="success"),
        pytest.param("nonzero exit", id="nonzero-exit"),
        pytest.param("timeout", id="timeout"),
        pytest.param("cancellation", id="cancellation"),
        pytest.param("overflow", id="overflow"),
    ],
)
@pytest.mark.xfail(
    raises=NotImplementedError,
    reason="AC-2 pending: signal the owned group and await the direct CLI",
    strict=True,
)
def test_terminal_outcome_signals_owned_group_and_waits_for_direct_cli(
    terminal_outcome: str,
) -> None:
    """AC-2: terminal paths record group signaling and direct-child wait."""
    # Given
    # A real disposable CLI reaches terminal_outcome; its owned group may
    # outlive its leader.

    # When
    # The integrated boundary performs bounded cleanup.

    # Then
    # It must request a signal to the owned group, even after leader exit, and
    # await/reap the direct CLI within the cleanup deadline, recording both
    # outcomes without claiming a process-tree audit.
    raise NotImplementedError(f"Pending observation for {terminal_outcome}")


@pytest.mark.xfail(
    raises=NotImplementedError,
    reason="AC-2 pending: propagate cancellation after bounded cleanup",
    strict=True,
)
def test_cancellation_propagates_after_bounded_cleanup_with_evidence() -> None:
    """AC-2: cancellation remains cancellation after cleanup is attempted."""
    # Given
    # A launched CLI is active when its owning task is cancelled.

    # When
    # The future public boundary completes bounded cleanup.

    # Then
    # Cancellation must propagate with partial and cleanup evidence, never as
    # successful completion or a retryable OSError.
    raise NotImplementedError("Pending observation for cancellation cleanup")


@pytest.mark.parametrize(
    "cleanup_failure",
    [
        pytest.param("signal error", id="signal-error"),
        pytest.param("signal deadline", id="signal-expiry"),
        pytest.param("wait error", id="wait-error"),
        pytest.param("wait deadline", id="wait-expiry"),
        pytest.param("unknown signal or wait result", id="unknown-result"),
    ],
)
@pytest.mark.xfail(
    raises=NotImplementedError,
    reason="AC-2 pending: retain failed or uncertain cleanup evidence",
    strict=True,
)
def test_cleanup_uncertainty_is_explicit_and_keeps_original_diagnostic(
    cleanup_failure: str,
) -> None:
    """AC-2: cleanup failure cannot be reported as confirmed cleanup."""
    # Given
    # A launched CLI has an original failure and cleanup encounters
    # cleanup_failure, including permission errors where applicable.

    # When
    # The future public boundary returns or propagates its outcome.

    # Then
    # Signal and wait evidence must identify failure, expiry, or uncertainty,
    # and the original failure diagnostic must remain inspectable.
    raise NotImplementedError(f"Pending observation for {cleanup_failure}")


@pytest.mark.xfail(
    raises=NotImplementedError,
    reason="AC-2 pending: account for interrupted process acquisition",
    strict=True,
)
def test_interrupted_acquisition_cannot_leave_a_late_unowned_child() -> None:
    """AC-2: acquisition interruption leaves no pending child acquisition."""
    # Given
    # Process acquisition fails or is interrupted before ownership is known.

    # When
    # The future public boundary finishes its acquisition cleanup path.

    # Then
    # No unawaited operation may later acquire an unowned subprocess, and any
    # unresolved ownership must be reported as incomplete cleanup.
    raise NotImplementedError("Pending observation for interrupted acquisition")


@pytest.mark.parametrize(
    "stop_trigger",
    [
        pytest.param("SIGINT", id="sigint"),
        pytest.param("SIGTERM", id="sigterm"),
        pytest.param("task cancellation", id="task-cancellation"),
        pytest.param("failed signal cleanup", id="failed-signal-cleanup"),
        pytest.param("unknown wait cleanup", id="unknown-wait-cleanup"),
    ],
)
@pytest.mark.xfail(
    raises=NotImplementedError,
    reason="AC-3 pending: stop dispatch and preserve incomplete accounting",
    strict=True,
)
def test_caller_stop_trigger_prevents_dispatch_and_accounts_for_calls(
    stop_trigger: str,
) -> None:
    """AC-3: each global stop prevents new calls and preserves accounting."""
    # Given
    # The Evaluation caller has planned calls and an active attempt; it receives
    # stop_trigger at its integrated dispatch boundary.

    # When
    # The owning caller handles that stop.

    # Then
    # It must dispatch no further call or retry, mark the run incomplete, retain
    # the active failure and cleanup status, and mark every undispatched call
    # not-started.
    raise NotImplementedError(f"Pending observation for {stop_trigger}")


@pytest.mark.xfail(
    raises=NotImplementedError,
    reason="AC-3 pending: retry only after confirmed cleanup without overlap",
    strict=True,
)
def test_caller_retry_starts_only_after_prior_cleanup_is_confirmed() -> None:
    """AC-3: retry ownership remains with the caller and cannot overlap."""
    # Given
    # A planned call has a retry-eligible failure and the previous attempt's
    # signal and direct-child wait cleanup are both confirmed.

    # When
    # The Evaluation caller dispatches its permitted retry.

    # Then
    # The retry must be caller-owned, start after confirmed cleanup, and never
    # overlap an unstopped direct CLI from the previous attempt.
    raise NotImplementedError("Pending observation for retry ordering")
