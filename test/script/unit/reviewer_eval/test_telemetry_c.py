# SPDX-License-Identifier: Apache-2.0
"""Checks for offline C telemetry arithmetic and error classification."""

import json

import pytest

from script.reviewer_eval.telemetry_c import distribution, notices, timeline


def test_quantiles_and_unknown_values() -> None:
    # Given
    values = [1.0, 2.0, 3.0, 4.0, None, float("nan")]

    # When
    result = distribution(values)

    # Then
    assert result == {
        "known": 4,
        "missing": 2,
        "min": 1.0,
        "max": 4.0,
        "mean": 2.5,
        "p50": 2.5,
        "p90": 3.7,
        "p95": 3.85,
        "p99": 3.97,
    }


def test_timeline_uses_half_open_intervals() -> None:
    # Given
    intervals = [(0.0, 2.0), (1.0, 2.0), (2.0, 4.0), (5.0, 6.0)]

    # When
    result = timeline(intervals)

    # Then
    assert result == {
        "peak": 2,
        "window_seconds": 6.0,
        "active_union_seconds": 5.0,
        "mean_active_over_window": 1.0,
        "start_span_seconds": 5.0,
    }


@pytest.mark.parametrize("intervals", [[], [(0.0, 0.0)], [(0.0, float("inf"))]])
def test_invalid_timeline_rejected(intervals: list[tuple[float, float]]) -> None:
    # Given
    # The parameter supplies the invalid interval set.

    # When / Then
    with pytest.raises(ValueError, match="invalid process interval"):
        timeline(intervals)


def test_notices_count_errors_without_inspecting_answers() -> None:
    # Given
    events = [
        {
            "type": "error",
            "message": "Reconnecting... 2/5 (unexpected status 403 Forbidden)",
        },
        {
            "type": "item.completed",
            "item": {
                "id": "x",
                "type": "error",
                "message": (
                    "Falling back from WebSockets to HTTPS transport. "
                    "unexpected status 403 Forbidden"
                ),
            },
        },
        {
            "type": "item.completed",
            "item": {
                "id": "y",
                "type": "agent_message",
                "text": "unexpected status 429",
            },
        },
        {"type": "error", "message": "opaque failure"},
    ]
    raw = b"\n".join(json.dumps(event).encode() for event in events) + b"\n{"

    # When
    result = notices(raw)

    # Then
    assert result == (1, 1, 2, 2, 0, 0, 0)


@pytest.mark.parametrize("input_tokens", [None, -1])
def test_missing_usage_makes_category_total_unknown(input_tokens: int | None) -> None:
    # Given
    from script.reviewer_eval.telemetry_c import Attempt, usage_summary

    usage = {
        "input_tokens": input_tokens,
        "cached_input_tokens": 2,
        "cache_write_input_tokens": 0,
        "output_tokens": 3,
        "reasoning_output_tokens": 1,
    }
    row = Attempt(
        "rep1-high",
        "high",
        0,
        1,
        "failed",
        False,
        False,
        "2026-01-01T00:00:00Z",
        None,
        None,
        0,
        0,
        1,
        0,
        0,
        0,
        0,
        False,
        usage,
    )

    # When
    result = usage_summary([row])

    # Then
    assert result["input_tokens"] == {
        "total": None,
        "distribution": {
            "known": 0,
            "missing": 1,
            "min": None,
            "max": None,
            "mean": None,
            "p50": None,
            "p90": None,
            "p95": None,
            "p99": None,
        },
    }
