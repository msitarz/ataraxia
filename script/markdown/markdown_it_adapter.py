# SPDX-License-Identifier: Apache-2.0
"""Adapt markdown-it-py tokens to the repository-owned Markdown boundary."""

from dataclasses import dataclass, field
import re
from typing import Literal, assert_never

from markdown_it import MarkdownIt
from markdown_it.token import Token

from script.markdown.model import (
    BlockKind,
    ContainerBlock,
    HeadingBlock,
    MarkdownBlock,
    MarkdownParseError,
    SourceLocation,
    TextBlock,
    TextKind,
    ThematicBreak,
)


@dataclass
class _BlockBuilder:
    kind: BlockKind
    line_start: int
    line_end: int
    heading_level: int | None = None
    text: str = ""
    children: list[_BlockBuilder] = field(default_factory=list)

    def build(self) -> MarkdownBlock:
        """Create a validated immutable block and recursively owned children.

        Returns:
            The complete immutable block represented by this builder.

        Raises:
            MarkdownParseError: The builder lacks a heading level.
        """
        location = SourceLocation(self.line_start, self.line_end)
        match self.kind:
            case "heading":
                if self.heading_level is None:
                    raise MarkdownParseError("Markdown heading has no level")
                return HeadingBlock(location, self.text, self.heading_level)
            case "blockquote" | "list" | "list_item":
                return ContainerBlock(
                    location,
                    self.kind,
                    tuple(child.build() for child in self.children),
                )
            case "thematic_break":
                return ThematicBreak(location)
            case "fenced_code" | "code_block" | "html_block" | "paragraph":
                return TextBlock(location, self.kind, self.text)
            case _ as unreachable:
                assert_never(unreachable)


_OPEN_BLOCKS: dict[str, BlockKind] = {
    "blockquote_open": "blockquote",
    "bullet_list_open": "list",
    "ordered_list_open": "list",
    "list_item_open": "list_item",
    "heading_open": "heading",
    "paragraph_open": "paragraph",
}
_CLOSE_BLOCKS: dict[str, BlockKind] = {
    "blockquote_close": "blockquote",
    "bullet_list_close": "list",
    "ordered_list_close": "list",
    "list_item_close": "list_item",
    "heading_close": "heading",
    "paragraph_close": "paragraph",
}
type LeafKind = TextKind | Literal["thematic_break"]
_LEAF_BLOCKS: dict[str, LeafKind] = {
    "fence": "fenced_code",
    "code_block": "code_block",
    "html_block": "html_block",
    "hr": "thematic_break",
}


class MarkdownItParser:
    """Parse source text with markdown-it-py CommonMark rules and locations."""

    def __init__(self) -> None:
        self._parser = MarkdownIt("commonmark")

    def parse(self, source: str) -> tuple[MarkdownBlock, ...]:
        """Return immutable blocks, raising MarkdownParseError for bad tokens.

        Markdown-it owns syntax recognition. This adapter owns the mapping of
        its block tokens and source ranges into the repository model.

        Args:
            source: Complete Markdown text.

        Returns:
            Immutable top-level Markdown blocks.

        Raises:
            MarkdownParseError: A token is unsupported or has invalid location
                or block data.
        """
        roots: list[_BlockBuilder] = []
        stack: list[_BlockBuilder] = []
        for token in self._parser.parse(source):
            _consume_token(token, roots, stack)
        if stack:
            raise MarkdownParseError("unclosed Markdown block token")
        try:
            return tuple(root.build() for root in roots)
        except (TypeError, ValueError) as error:
            raise MarkdownParseError("invalid Markdown block data") from error


def _consume_token(
    token: Token, roots: list[_BlockBuilder], stack: list[_BlockBuilder]
) -> None:
    if token.type in _OPEN_BLOCKS:
        block = _open_block(token, _OPEN_BLOCKS[token.type])
        _append(block, roots, stack)
        stack.append(block)
        return
    if token.type in _CLOSE_BLOCKS:
        if not stack or stack[-1].kind != _CLOSE_BLOCKS[token.type]:
            raise MarkdownParseError("unexpected Markdown closing token")
        stack.pop()
        return
    if token.type == "inline":
        if not stack or stack[-1].kind not in {"heading", "paragraph"}:
            raise MarkdownParseError("Markdown inline token has no text block")
        stack[-1].text = token.content
        return
    if token.type in _LEAF_BLOCKS:
        block = _leaf_block(token, _LEAF_BLOCKS[token.type])
        _append(block, roots, stack)
        return
    raise MarkdownParseError(f"unsupported Markdown token: {token.type!r}")


def _append(
    block: _BlockBuilder,
    roots: list[_BlockBuilder],
    stack: list[_BlockBuilder],
) -> None:
    if stack:
        stack[-1].children.append(block)
    else:
        roots.append(block)


def _source_lines(token: Token) -> tuple[int, int]:
    source_map = token.map
    if source_map is None:
        raise _source_range_error(token)
    if len(source_map) != 2:
        raise _source_range_error(token)
    start, end = source_map
    if not isinstance(start, int):
        raise _source_range_error(token)
    if isinstance(start, bool):
        raise _source_range_error(token)
    if start < 0:
        raise _source_range_error(token)
    if not isinstance(end, int):
        raise _source_range_error(token)
    if isinstance(end, bool):
        raise _source_range_error(token)
    if end <= start:
        raise _source_range_error(token)
    return start + 1, end


def _source_range_error(token: Token) -> MarkdownParseError:
    return MarkdownParseError(
        f"Markdown block token {token.type!r} has no valid source range"
    )


def _open_block(token: Token, kind: BlockKind) -> _BlockBuilder:
    line_start, line_end = _source_lines(token)
    heading_level: int | None = None
    if kind == "heading":
        heading_match = re.fullmatch(r"h([1-6])", token.tag)
        if heading_match is None:
            raise MarkdownParseError("Markdown heading has an invalid level")
        heading_level = int(heading_match.group(1))
    return _BlockBuilder(kind, line_start, line_end, heading_level)


def _leaf_block(
    token: Token, kind: TextKind | Literal["thematic_break"]
) -> _BlockBuilder:
    line_start, line_end = _source_lines(token)
    text = "" if kind == "thematic_break" else token.content
    return _BlockBuilder(kind, line_start, line_end, text=text)
