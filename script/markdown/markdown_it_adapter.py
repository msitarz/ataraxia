# SPDX-License-Identifier: Apache-2.0
"""Adapt markdown-it-py tokens to the repository-owned Markdown boundary."""

from typing import Literal

from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode

from script.markdown.model import (
    ContainerBlock,
    ContainerKind,
    HeadingBlock,
    MarkdownBlock,
    MarkdownParseError,
    SourceLocation,
    TextBlock,
    TextKind,
    ThematicBreak,
)

type LeafKind = TextKind | Literal["thematic_break"]
_LEAF_KINDS: dict[str, LeafKind] = {
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
        """Return immutable Markdown blocks with source locations.

        Markdown-it owns syntax recognition. This adapter maps its documented
        syntax tree to repository-owned values. Unsupported blocks and blocks
        without source locations propagate ``MarkdownParseError`` from the
        mapping helpers.

        Args:
            source: Complete Markdown text.

        Returns:
            Immutable top-level Markdown blocks.
        """
        tree = SyntaxTreeNode(self._parser.parse(source))
        return tuple(_block(child) for child in tree.children)


def _block(node: SyntaxTreeNode) -> MarkdownBlock:
    kind = node.type
    match kind:
        case "blockquote":
            return _container(node, "blockquote")
        case "bullet_list" | "ordered_list":
            return _container(node, "list")
        case "list_item":
            return _container(node, "list_item")
    if kind == "heading":
        return HeadingBlock(
            _location(node), node.children[0].content, int(node.tag[1:])
        )
    if kind == "paragraph":
        return TextBlock(_location(node), "paragraph", node.children[0].content)
    if kind in _LEAF_KINDS:
        leaf_kind = _LEAF_KINDS[kind]
        if leaf_kind == "thematic_break":
            return ThematicBreak(_location(node))
        return TextBlock(_location(node), leaf_kind, node.content)
    raise MarkdownParseError(f"unsupported Markdown block: {kind!r}")


def _container(node: SyntaxTreeNode, kind: ContainerKind) -> ContainerBlock:
    return ContainerBlock(
        _location(node),
        kind,
        tuple(_block(child) for child in node.children),
    )


def _location(node: SyntaxTreeNode) -> SourceLocation:
    source_map = node.map
    if source_map is None:
        raise MarkdownParseError(f"Markdown block {node.type!r} has no source range")
    start, end = source_map
    return SourceLocation(start + 1, end)
