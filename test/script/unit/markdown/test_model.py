# SPDX-License-Identifier: Apache-2.0
"""Check runtime invariants for repository-owned Markdown values."""

from collections.abc import Callable
from dataclasses import FrozenInstanceError

import pytest

from script.markdown.model import (
    ContainerBlock,
    ContainerKind,
    HeadingBlock,
    MarkdownBlock,
    SourceLocation,
    TextBlock,
)


@pytest.mark.parametrize(
    ("construct", "error", "message"),
    [
        pytest.param(
            lambda: SourceLocation(True, 1),
            ValueError,
            "must not be Boolean",
            id="boolean-line",
        ),
        pytest.param(
            lambda: SourceLocation(2, 1),
            ValueError,
            "must not precede",
            id="reversed-lines",
        ),
        pytest.param(
            lambda: HeadingBlock(SourceLocation(1, 1), "", True),
            ValueError,
            "must not be Boolean",
            id="boolean-heading-level",
        ),
        pytest.param(
            lambda: HeadingBlock(SourceLocation(1, 1), "", 7),
            ValueError,
            "from 1 through 6",
            id="unsupported-heading-level",
        ),
        pytest.param(
            lambda: ContainerBlock(
                SourceLocation(1, 1),
                "blockquote",
                (TextBlock(SourceLocation(2, 2), "paragraph", "outside"),),
            ),
            ValueError,
            "lies outside its container",
            id="child-outside-container",
        ),
        pytest.param(
            lambda: ContainerBlock(
                SourceLocation(1, 1),
                "list",
                (TextBlock(SourceLocation(1, 1), "paragraph", "item"),),
            ),
            ValueError,
            "lists must contain list items",
            id="list-child-kind",
        ),
    ],
)
def test_markdown_values_reject_invalid_locations_and_shapes(
    construct: Callable[[], MarkdownBlock | SourceLocation],
    error: type[Exception],
    message: str,
) -> None:
    # Given
    # The parametrized constructor represents the invalid value.

    # When
    with pytest.raises(error) as error_info:
        construct()

    # Then
    assert message in str(error_info.value)


@pytest.mark.parametrize(
    ("container_lines", "child_lines", "contains"),
    [
        pytest.param((4, 8), (4, 8), True, id="equal-ranges"),
        pytest.param((4, 8), (5, 7), True, id="interior-range"),
        pytest.param((4, 8), (3, 5), False, id="before-start"),
        pytest.param((4, 8), (7, 9), False, id="after-end"),
    ],
)
def test_source_location_membership_uses_inclusive_ranges(
    container_lines: tuple[int, int],
    child_lines: tuple[int, int],
    contains: bool,
) -> None:
    # Given
    container = SourceLocation(*container_lines)
    child = SourceLocation(*child_lines)

    # When
    result = child in container

    # Then
    assert result is contains


def test_heading_keeps_empty_text_and_frozen_owned_values() -> None:
    # Given
    location = SourceLocation(1, 1)
    heading = HeadingBlock(location, "", 1)

    # When
    attribute_name = "heading_level"
    with pytest.raises(FrozenInstanceError):
        setattr(heading, attribute_name, 2)

    # Then
    assert heading.location is location
    assert heading.text == ""
    assert heading.heading_level == 1


def test_container_keeps_nested_values_in_an_immutable_tuple() -> None:
    # Given
    heading = HeadingBlock(SourceLocation(1, 1), "Nested", 2)
    children = (heading,)

    # When
    container = ContainerBlock(SourceLocation(1, 1), "blockquote", children)

    # Then
    assert container.children == (heading,)
    assert isinstance(container.children, tuple)


@pytest.mark.parametrize(
    "kind",
    ["blockquote", "list_item"],
    ids=["empty-blockquote", "empty-list-item"],
)
def test_container_values_allow_empty_commonmark_shapes(
    kind: ContainerKind,
) -> None:
    # Given
    location = SourceLocation(1, 1)

    # When
    container = ContainerBlock(location, kind, ())

    # Then
    assert container.children == ()
