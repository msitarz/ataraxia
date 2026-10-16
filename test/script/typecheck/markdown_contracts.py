# SPDX-License-Identifier: Apache-2.0
from typing import assert_type

from script.markdown.markdown_it_adapter import MarkdownItParser
from script.markdown.model import (
    HeadingBlock,
    MarkdownBlock,
    MarkdownParser,
    SourceLocation,
    TextBlock,
)


def contracts(parser: MarkdownParser) -> None:
    concrete: MarkdownParser = MarkdownItParser()
    blocks = parser.parse("# title")
    assert_type(blocks, tuple[MarkdownBlock, ...])
    assert_type(concrete.parse("# title"), tuple[MarkdownBlock, ...])
    for block in blocks:
        if block.kind == "heading":
            assert_type(block, HeadingBlock)
            assert_type(block.heading_level, int)
    HeadingBlock(SourceLocation(1, 1), "title", "two")  # E: is not assignable
    TextBlock(SourceLocation(1, 1), "heading", "title")  # E: is not assignable
