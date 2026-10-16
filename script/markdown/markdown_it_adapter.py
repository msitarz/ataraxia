# SPDX-License-Identifier: Apache-2.0
"""Adapt markdown-it-py tokens to the repository-owned Markdown boundary."""

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
    ThematicBreak,
)


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
    match node.type:
        case "blockquote":
            return _container(node, "blockquote")
        case "bullet_list" | "ordered_list":
            return _container(node, "list")
        case "list_item":
            return _container(node, "list_item")
        case "heading":
            return HeadingBlock(
                _location(node), node.children[0].content, int(node.tag[1:])
            )
        case "paragraph":
            return TextBlock(_location(node), "paragraph", node.children[0].content)
        case "fence":
            return TextBlock(_location(node), "fenced_code", node.content)
        case "code_block":
            return TextBlock(_location(node), "code_block", node.content)
        case "html_block":
            return TextBlock(_location(node), "html_block", node.content)
        case "hr":
            return ThematicBreak(_location(node))
        case _:
            raise MarkdownParseError(f"unsupported Markdown block: {node.type!r}")


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
