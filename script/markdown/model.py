# SPDX-License-Identifier: Apache-2.0
"""Repository-owned values and parser port for Markdown consumers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol, get_args

type ContainerKind = Literal["blockquote", "list", "list_item"]
type TextKind = Literal["fenced_code", "code_block", "html_block", "paragraph"]


@dataclass(frozen=True)
class SourceLocation:
    """One-based inclusive source lines for a Markdown block."""

    line_start: int
    line_end: int

    def contains(self, other: SourceLocation) -> bool:
        """Return whether this inclusive range contains another location."""
        return self.line_start <= other.line_start and other.line_end <= self.line_end

    def __post_init__(self) -> None:
        """Reject invalid source line ranges.

        Raises:
            TypeError: A line value is not an integer.
            ValueError: A line value is Boolean, nonpositive, or reversed.
        """
        if not isinstance(self.line_start, int):
            raise TypeError("source start line must be an integer")
        if isinstance(self.line_start, bool):
            raise ValueError("source start line must not be Boolean")
        if self.line_start < 1:
            raise ValueError("source start line must be positive")
        if not isinstance(self.line_end, int):
            raise TypeError("source end line must be an integer")
        if isinstance(self.line_end, bool):
            raise ValueError("source end line must not be Boolean")
        if self.line_end < self.line_start:
            raise ValueError("source end line must not precede its start")


@dataclass(frozen=True)
class _LocatedBlock:
    location: SourceLocation

    def __post_init__(self) -> None:
        if not isinstance(self.location, SourceLocation):
            raise TypeError("Markdown blocks require a SourceLocation")


@dataclass(frozen=True)
class HeadingBlock(_LocatedBlock):
    """A heading whose level is present and valid by construction."""

    text: str
    heading_level: int
    kind: Literal["heading"] = field(default="heading", init=False)

    def __post_init__(self) -> None:
        """Validate heading text and level.

        Raises:
            TypeError: Text or level has the wrong type.
            ValueError: The level is Boolean or outside the supported range.
        """
        super().__post_init__()
        if not isinstance(self.text, str):
            raise TypeError("Markdown heading text must be a string")
        if not isinstance(self.heading_level, int):
            raise TypeError("Markdown heading level must be an integer")
        if isinstance(self.heading_level, bool):
            raise ValueError("Markdown heading level must not be Boolean")
        if self.heading_level < 1 or self.heading_level > 6:
            raise ValueError("Markdown heading level must be from 1 through 6")


@dataclass(frozen=True)
class TextBlock(_LocatedBlock):
    """A text-bearing leaf such as a paragraph, code block, or HTML block."""

    kind: TextKind
    text: str

    def __post_init__(self) -> None:
        """Validate the text leaf's kind and content.

        Raises:
            TypeError: The kind or text has the wrong type.
            ValueError: The kind is not supported by this value shape.
        """
        super().__post_init__()
        if not isinstance(self.kind, str):
            raise TypeError("Markdown text block kind must be a string")
        if self.kind not in get_args(TextKind.__value__):
            raise ValueError(f"unsupported Markdown text block kind: {self.kind!r}")
        if not isinstance(self.text, str):
            raise TypeError("Markdown block text must be a string")


@dataclass(frozen=True)
class ContainerBlock(_LocatedBlock):
    """A quote or list container owning immutable nested blocks.

    Typed child values are assumed to be valid Markdown blocks. Construction
    enforces the relationships owned by this container.
    """

    kind: ContainerKind
    children: tuple[MarkdownBlock, ...]

    def __post_init__(self) -> None:
        """Validate container kind, children, and their source ranges.

        Raises:
            TypeError: Children are not an immutable tuple.
            ValueError: The kind, a child's range, or a list's child kind is
                invalid for this container.
        """
        super().__post_init__()
        if not isinstance(self.kind, str):
            raise TypeError("Markdown container kind must be a string")
        if self.kind not in get_args(ContainerKind.__value__):
            raise ValueError(f"unsupported Markdown container kind: {self.kind!r}")
        if not isinstance(self.children, tuple):
            raise TypeError("Markdown container children must be a tuple")
        for child in self.children:
            if not self.location.contains(child.location):
                raise ValueError("Markdown child lies outside its container")
        if self.kind == "list" and any(
            child.kind != "list_item" for child in self.children
        ):
            raise ValueError("Markdown lists must contain list items")


@dataclass(frozen=True)
class ThematicBreak(_LocatedBlock):
    """A thematic break, which has a location and no text payload."""

    kind: Literal["thematic_break"] = field(default="thematic_break", init=False)


type MarkdownBlock = HeadingBlock | TextBlock | ContainerBlock | ThematicBreak


class MarkdownParser(Protocol):
    """Consumer-owned port that parses text into validated Markdown values."""

    def parse(self, source: str) -> tuple[MarkdownBlock, ...]:
        """Parse Markdown text into validated values.

        Args:
            source: Complete Markdown text.

        Returns:
            Immutable top-level Markdown blocks.

        Raises:
            MarkdownParseError: The parser adapter cannot produce valid values.
        """


class MarkdownParseError(ValueError):
    """Raised when a parser adapter cannot produce valid Markdown values."""
