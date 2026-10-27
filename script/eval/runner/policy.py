# SPDX-License-Identifier: Apache-2.0
"""Pure retry, quota-wait, and capacity-backoff policy calculations.

These functions decide policy eligibility and timing only. The coordinator
still owns cleanup, cancellation, overflow, uncertain acquisition, evidence
publication, and dispatch ordering.
"""

from script.eval.model import HarnessConfig, RetryAssessment


def confident_no_result(assessment: RetryAssessment, /) -> bool:
    """Return whether the assessment explicitly establishes semantic absence.

    ``present_or_unknown`` refuses retry eligibility. This does not establish
    safe cleanup or successful evidence persistence.
    """
    raise NotImplementedError("confident_no_result policy is pending")


def infrastructure_retry_allowed(
    assessment: RetryAssessment,
    retries_used: int,
    config: HarnessConfig,
    /,
) -> bool:
    """Gate an explicitly classified infrastructure retry by its allowance.

    Only the infrastructure category and ``retry_limit`` belong here;
    callers retain the other lifecycle and budget gates. The default limit is
    zero, so a fresh configuration allows no retry.
    """
    raise NotImplementedError("infrastructure_retry_allowed policy is pending")


def capacity_retry_allowed(
    assessment: RetryAssessment,
    retries_used: int,
    config: HarnessConfig,
    /,
) -> bool:
    """Gate an explicitly classified capacity retry by its own allowance.

    This uses ``capacity_retry_limit`` independently from infrastructure
    retries. Cleanup and evidence gates remain with the coordinator.
    """
    raise NotImplementedError("capacity_retry_allowed policy is pending")


def capacity_jitter_bound(
    retry_index: int, base_seconds: float, cap_seconds: float, /
) -> float:
    """Return the cap-saturated exponential upper bound for full jitter.

    For zero-based ``retry_index``, the bound is ``min(cap, base * 2**index)``.
    Saturation must happen before an exponential can overflow.
    """
    raise NotImplementedError("capacity_jitter_bound policy is pending")


def quota_wait_remaining(
    config: HarnessConfig, cumulative_wait_seconds: float, /
) -> float | None:
    """Return remaining quota wait, or ``None`` when enabled without a bound.

    Disabled or exhausted waiting returns zero. An absent configured duration
    means unbounded waiting; it does not imply a reset estimate.
    """
    raise NotImplementedError("quota_wait_remaining policy is pending")


def quota_probe_allowed(config: HarnessConfig, probes_used: int, /) -> bool:
    """Require quota opt-in and an unspent configured probe cap.

    An absent cap adds no harness count limit; caller operational budgets still
    apply. A configured zero cap refuses every probe.
    """
    raise NotImplementedError("quota_probe_allowed policy is pending")


def quota_poll_delay(
    interval_seconds: float,
    now_utc: str,
    reset_hint_utc: str | None,
    /,
) -> float:
    """Schedule the earlier future reset hint or periodic interval.

    Missing, stale, or past hints use the interval. A future hint schedules a
    check only; it never authorizes dispatch. A zero-delay polling loop is
    excluded.
    """
    raise NotImplementedError("quota_poll_delay policy is pending")
