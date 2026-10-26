# SPDX-License-Identifier: Apache-2.0
"""Pure retry eligibility, allowance, and backoff calculations."""

from ..model import HarnessConfig, RetryAssessment  # ruff: ignore[relative-imports]

def confident_no_result(assessment: RetryAssessment, /) -> bool:
    """Return whether supplied evidence establishes semantic-result absence."""
    ...

def infrastructure_retry_allowed(
    assessment: RetryAssessment,
    retries_used: int,
    config: HarnessConfig,
    /,
) -> bool:
    """Apply only the ordinary infrastructure retry category and limit."""
    ...

def capacity_retry_allowed(
    assessment: RetryAssessment,
    retries_used: int,
    config: HarnessConfig,
    /,
) -> bool:
    """Apply only the separate capacity retry category and limit."""
    ...

def capacity_jitter_bound(
    retry_index: int, base_seconds: float, cap_seconds: float, /
) -> float:
    """Return min(cap, base * 2**index) using cap-saturating arithmetic."""
    ...

def quota_wait_remaining(
    config: HarnessConfig, cumulative_wait_seconds: float, /
) -> float | None:
    """Return remaining configured wait, zero when disabled/exhausted.

    ``None`` means quota waiting is enabled without an optional cumulative
    duration bound; it does not mean reset information may be guessed.
    """
    ...

def quota_probe_allowed(config: HarnessConfig, probes_used: int, /) -> bool:
    """Require quota opt-in and an unspent optional operational probe cap.

    An absent cap means no additional harness count limit; a configured zero
    refuses dispatch. Caller operational limits still apply.
    """
    ...

def quota_poll_delay(
    interval_seconds: float,
    now_utc: str,
    reset_hint_utc: str | None,
    /,
) -> float:
    """Schedule the earlier positive reset hint or periodic interval.

    A missing, stale, or past hint falls back to the configured interval; a
    hint schedules a check only and never authorizes dispatch. Zero-delay hint
    loops are excluded.
    """
    ...
