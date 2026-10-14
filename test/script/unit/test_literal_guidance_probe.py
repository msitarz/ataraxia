# SPDX-License-Identifier: Apache-2.0
from collections.abc import Callable

import pytest

from test.ataraxia.typecheck.literal_guidance_probe import (
    ChangedInput,
    RecordName,
    changed_input,
    describe_change,
    record_name,
)

type DomainValue = ChangedInput | RecordName


@pytest.mark.parametrize(
    ("value", "validator"),
    [
        pytest.param("declaration", changed_input, id="changed-declaration"),
        pytest.param("file", changed_input, id="changed-file"),
        pytest.param("accepted", record_name, id="record-accepted"),
        pytest.param("version", record_name, id="record-version"),
    ],
)
def test_domain_validators_accept_each_declared_member(
    value: DomainValue,
    validator: Callable[[object], DomainValue],
) -> None:
    # Given
    # The parameterized value is a declared member of the selected domain.

    # When
    result = validator(value)

    # Then
    assert result == value


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param("declaration", "update declaration", id="declaration"),
        pytest.param("file", "replace file", id="file"),
    ],
)
def test_distinct_action_cases_cover_each_changed_input(
    value: ChangedInput,
    expected: str,
) -> None:
    # Given
    # Each supported ChangedInput has a distinct action.

    # When
    result = describe_change(value)

    # Then
    assert result == expected


@pytest.mark.parametrize(
    ("value", "validator"),
    [
        pytest.param(3, changed_input, id="non-string"),
        pytest.param("accepted", changed_input, id="other-domain"),
        pytest.param("file", record_name, id="other-domain-reversed"),
        pytest.param("future-option", changed_input, id="unknown"),
        pytest.param("future-option", record_name, id="unknown-other-domain"),
    ],
)
def test_domain_validators_reject_values_outside_their_domain(
    value: object,
    validator: Callable[[object], DomainValue],
) -> None:
    # Given
    # The parameterized value is invalid for the selected domain.

    # When
    with pytest.raises(ValueError):
        validator(value)

    # Then
    # Each consumed boundary rejects non-strings and unsupported names.
