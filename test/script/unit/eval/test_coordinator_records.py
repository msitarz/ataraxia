# SPDX-License-Identifier: Apache-2.0
"""Stable binding settings digests for run record projection."""

import pytest

from script.eval.runner.coordinator.records import settings_digest


def test_settings_digest_hashes_ordered_compact_utf8_json() -> None:
    # Given
    settings = (("mode", "fast"), ("limit", 0), ("flag", True), ("missing", None))

    # When
    digest = settings_digest(settings)

    # Then
    # SHA-256 of the UTF-8 bytes for the compact JSON array of pairs.
    assert digest == "28a2ac63a8938c8f655346ed96e159666c562697c2a1c08f14a25f9e0edb0317"


def test_settings_digest_rejects_nonfinite_numbers() -> None:
    # Given
    settings = (("value", float("inf")),)

    # When / Then
    with pytest.raises(ValueError, match="Out of range float"):
        settings_digest(settings)
