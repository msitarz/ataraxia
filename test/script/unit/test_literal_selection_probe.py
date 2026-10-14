# SPDX-License-Identifier: Apache-2.0
from enum import Enum
from typing import Literal, assert_type

import pytest

type ChangedInput = Literal["declaration", "evidence", "file", "link", "record"]


class Format(Enum):
    JSON = "json"
    TEXT = "text"


def narrow_changed_input(value: str) -> ChangedInput:
    match value:
        case "declaration" | "evidence" | "file" | "link" | "record":
            return value
        case _:
            raise ValueError(f"unknown fixture input: {value}")


def choose_format(value: str) -> str:
    match value:
        case "json":
            return "json"
        case _:
            return "text"


def test_closed_domain_validation_preserves_the_open_boundary() -> None:
    # Given
    external = "file"

    # When
    narrowed = narrow_changed_input(external)

    # Then
    assert_type(narrowed, ChangedInput)
    assert narrowed == "file"


def test_closed_domain_validation_rejects_unknown_values() -> None:
    # Given
    external = "future-option"

    # When / Then
    with pytest.raises(ValueError, match="future-option"):
        narrow_changed_input(external)


def test_open_string_match_default_still_accepts_future_values() -> None:
    # Given
    external = "yaml"

    # When
    selected = choose_format(external)

    # Then
    assert selected == "text"


def test_enum_provides_named_identity_without_closed_input_validation() -> None:
    # Given
    format_kind = Format.JSON

    # When
    wire_value = format_kind.value

    # Then
    assert wire_value == "json"
    assert format_kind is Format.JSON
