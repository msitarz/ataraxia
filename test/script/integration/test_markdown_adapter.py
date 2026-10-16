# SPDX-License-Identifier: Apache-2.0
"""Exercise markdown-it adaptation through its public parser port."""

from pathlib import Path

import pytest

from script.markdown_it_adapter import MarkdownItParser
from script.markdown_model import (
    ContainerBlock,
    HeadingBlock,
    MarkdownBlock,
    MarkdownParser,
    SourceLocation,
    TextBlock,
    ThematicBreak,
)

ROOT = Path(__file__).resolve().parents[3]


def test_parser_returns_complete_typed_tree_with_source_locations() -> None:
    # Given
    source = (ROOT / "test/script/fixtures/markdown_context.md").read_text(
        encoding="utf-8"
    )
    parser: MarkdownParser = MarkdownItParser()

    # When
    blocks = parser.parse(source)

    # Then
    assert blocks == (
        HeadingBlock(SourceLocation(1, 1), "Main heading", 1),
        TextBlock(SourceLocation(3, 3), "paragraph", "Intro paragraph."),
        ContainerBlock(
            SourceLocation(5, 7),
            "blockquote",
            (
                HeadingBlock(SourceLocation(5, 5), "Quoted heading", 2),
                TextBlock(SourceLocation(7, 7), "paragraph", "Quote text."),
            ),
        ),
        ContainerBlock(
            SourceLocation(9, 10),
            "list",
            (
                ContainerBlock(
                    SourceLocation(9, 10),
                    "list_item",
                    (HeadingBlock(SourceLocation(9, 9), "Listed heading", 3),),
                ),
            ),
        ),
        TextBlock(
            SourceLocation(11, 13),
            "fenced_code",
            "## Heading inside a fence\n",
        ),
        TextBlock(
            SourceLocation(15, 17),
            "html_block",
            "<!--\n## Heading inside a comment\n-->\n",
        ),
        HeadingBlock(SourceLocation(19, 19), "Final heading", 2),
    )


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        pytest.param("", (), id="empty-document"),
        pytest.param(
            "#\n",
            (HeadingBlock(SourceLocation(1, 1), "", 1),),
            id="empty-heading",
        ),
        pytest.param(
            "alpha\r\nβeta\r\n---\r\n",
            (HeadingBlock(SourceLocation(1, 3), "alpha\nβeta", 2),),
            id="multiline-unicode-setext-with-crlf",
        ),
        pytest.param(
            "    indented code\n\n---\n",
            (
                TextBlock(SourceLocation(1, 1), "code_block", "indented code\n"),
                ThematicBreak(SourceLocation(3, 3)),
            ),
            id="indented-code-and-thematic-break",
        ),
        pytest.param(
            ">\n",
            (ContainerBlock(SourceLocation(1, 1), "blockquote", ()),),
            id="empty-blockquote",
        ),
        pytest.param(
            "-\n",
            (
                ContainerBlock(
                    SourceLocation(1, 1),
                    "list",
                    (ContainerBlock(SourceLocation(1, 1), "list_item", ()),),
                ),
            ),
            id="empty-list-item",
        ),
    ],
)
def test_parser_handles_empty_and_multiline_source_boundaries(
    source: str, expected: tuple[MarkdownBlock, ...]
) -> None:
    # Given
    parser = MarkdownItParser()

    # When
    blocks = parser.parse(source)

    # Then
    assert blocks == expected
