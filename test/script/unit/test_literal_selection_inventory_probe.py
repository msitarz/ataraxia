# SPDX-License-Identifier: Apache-2.0
import pytest

from test.script.literal_selection_inventory_probe import (
    changed_input_name,
    is_changed_input,
    is_record_name,
    record_fixture_name,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("declaration", True),
        ("file", True),
        ("accepted", False),
        ("future-option", False),
    ],
    ids=["changed-name", "changed-name-two", "other-domain", "unknown"],
)
def test_changed_input_membership_uses_its_literal_inventory(
    value: str, expected: bool
) -> None:
    # Given
    candidate = value

    # When
    result = is_changed_input(candidate)

    # Then
    assert result is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [("accepted", True), ("metadata", True), ("link", False), ("unknown", False)],
    ids=["record-name", "record-name-two", "other-domain", "unknown"],
)
def test_record_name_membership_keeps_its_distinct_inventory(
    value: str, expected: bool
) -> None:
    # Given
    candidate = value

    # When
    result = is_record_name(candidate)

    # Then
    assert result is expected


def test_validators_preserve_supported_values_as_strings() -> None:
    # Given
    changed_name = "file"
    record_name = "accepted"

    # When
    changed_result = changed_input_name(changed_name)
    record_result = record_fixture_name(record_name)

    # Then
    assert changed_result == changed_name
    assert record_result == record_name
    assert isinstance(changed_result, str)
    assert isinstance(record_result, str)


def test_changed_input_validator_rejects_unknown_names() -> None:
    # Given
    external = "future-option"

    # When / Then
    with pytest.raises(ValueError, match="future-option"):
        changed_input_name(external)


def test_record_name_validator_rejects_unknown_names() -> None:
    # Given
    external = "unknown"

    # When / Then
    with pytest.raises(ValueError, match="unknown"):
        record_fixture_name(external)
