# SPDX-License-Identifier: Apache-2.0
"""Pure retry, quota-wait, and capacity-backoff policy calculations.

These functions decide policy eligibility and timing only. The coordinator
still owns cleanup, cancellation, overflow, uncertain acquisition, evidence
publication, and dispatch ordering.
"""

from datetime import datetime
from math import frexp, ldexp

from script.eval.model import HarnessConfig, ProcessRecord, RetryAssessment


def confident_no_result(assessment: RetryAssessment, /) -> bool:
    """Return whether the assessment explicitly establishes semantic absence.

    ``present_or_unknown`` refuses retry eligibility. This does not establish
    safe cleanup or successful evidence persistence.
    """
    return assessment.no_result_basis == "confident_absence"


def infrastructure_retry_allowed(
    assessment: RetryAssessment,
    retries_used: int,
    config: HarnessConfig,
    /,
) -> bool:
    """Gate an explicitly classified infrastructure retry by its allowance.

    Eligibility requires the infrastructure category, confident semantic
    absence, and an unspent ``retry_limit``. The coordinator retains cleanup,
    cancellation, overflow, evidence-publication, and caller-budget gates. The
    default limit is zero, so a fresh configuration allows no retry.

    Returns:
        Whether this category's retry allowance remains unspent.
    """
    return (
        assessment.retry_class == "infrastructure"
        and confident_no_result(assessment)
        and retries_used < config.retry_limit
    )


def capacity_retry_allowed(
    assessment: RetryAssessment,
    retries_used: int,
    config: HarnessConfig,
    /,
) -> bool:
    """Gate an explicitly classified capacity retry by its own allowance.

    Eligibility requires the capacity category, confident semantic absence,
    and an unspent ``capacity_retry_limit``, independently from infrastructure
    retries. The coordinator retains cleanup, cancellation, overflow,
    evidence-publication, and caller-budget gates.

    Returns:
        Whether this category's retry allowance remains unspent.
    """
    return (
        assessment.retry_class == "capacity"
        and confident_no_result(assessment)
        and retries_used < config.capacity_retry_limit
    )


def capacity_jitter_bound(
    retry_index: int, base_seconds: float, cap_seconds: float, /
) -> float:
    """Return the cap-saturated exponential upper bound for full jitter.

    For zero-based ``retry_index``, the bound is ``min(cap, base * 2**index)``.
    Saturation must happen before an exponential can overflow.
    """
    # ``frexp`` gives base = mantissa * 2**exponent. Check the exponent first
    # so even enormous retry indices saturate without constructing 2**index.
    exponent = frexp(base_seconds)[1] + retry_index
    if exponent > 1024:
        return cap_seconds
    try:
        bound = ldexp(base_seconds, retry_index)
    except OverflowError:
        return cap_seconds
    return min(cap_seconds, bound)


def quota_wait_remaining(
    config: HarnessConfig, cumulative_wait_seconds: float, /
) -> float | None:
    """Return remaining quota wait, or ``None`` when enabled without a bound.

    Disabled or exhausted waiting returns zero. An absent configured duration
    means unbounded waiting; it does not imply a reset estimate.
    """
    if not config.quota_wait_enabled:
        return 0.0
    limit = config.quota_wait_limit_seconds
    if limit is None:
        return None
    if cumulative_wait_seconds >= limit:
        return 0.0
    return limit - cumulative_wait_seconds


def quota_probe_allowed(config: HarnessConfig, probes_used: int, /) -> bool:
    """Require quota opt-in and an unspent configured probe cap.

    An absent cap adds no harness count limit; caller operational budgets still
    apply. A configured zero cap refuses every probe.

    Returns:
        Whether a quota probe is authorized by the configured policy.
    """
    return config.quota_wait_enabled and (
        config.quota_probe_budget is None or probes_used < config.quota_probe_budget
    )


def quota_poll_delay(
    interval_seconds: float,
    now_utc: str,
    reset_hint_utc: str | None,
    /,
) -> float:
    """Schedule the earlier future reset hint or periodic interval.

    Missing, stale, or past hints use the interval. A future hint schedules a
    check only; it never authorizes dispatch. A zero-delay polling loop is
    excluded. As a typed precondition, ``now_utc`` and a supplied hint are
    valid timezone-aware UTC timestamps from their runtime/provider boundary;
    adapters normalize or refuse malformed source timestamps before this
    function is called.

    Returns:
        The positive delay until the next check.
    """
    if reset_hint_utc is None:
        return interval_seconds
    now = datetime.fromisoformat(now_utc.replace("Z", "+00:00"))
    hint = datetime.fromisoformat(reset_hint_utc.replace("Z", "+00:00"))
    seconds_until_hint = (hint - now).total_seconds()
    if seconds_until_hint <= 0:
        return interval_seconds
    return min(interval_seconds, seconds_until_hint)


def safe_process_cleanup(record: ProcessRecord, /) -> bool:
    """Return whether recorded supervisor cleanup permits dispatch."""
    cleanup = record.cleanup
    if cleanup is None or cleanup.wait_diagnostic is not None:
        return False
    if cleanup.process == "not_started":
        return not cleanup.signals and cleanup.direct_wait == "not_started"
    return (
        cleanup.process == "owned"
        and cleanup.direct_wait == "reaped"
        and tuple(item.signal for item in cleanup.signals)
        in {("SIGKILL",), ("SIGTERM", "SIGKILL")}
        and all(
            item.outcome in {"sent", "no_target"} and item.diagnostic is None
            for item in cleanup.signals
        )
    )
