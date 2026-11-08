# SPDX-License-Identifier: Apache-2.0
"""Resource totals retain signed values and missing categories."""

from script.reviewer_eval.c_resources import Usage, totals


def test_negative_adjustment_is_not_clamped() -> None:
    # Given input below the candidate baseline.
    usage = Usage(input_tokens=100, output_tokens=20)

    # When subtracting the baseline.
    result = totals([usage], 150)

    # Then both signed adjusted measures remain negative.
    assert result["candidate_adjusted_input"] == -50
    assert result["candidate_adjusted_complete"] == -30


def test_missing_usage_keeps_complete_totals_unknown() -> None:
    # Given one known and one unavailable usage record.
    usage = Usage(input_tokens=200, output_tokens=30)

    # When summing attempts.
    result = totals([usage, None], 150)

    # Then no complete total is fabricated.
    assert all(value is None for value in result.values())
