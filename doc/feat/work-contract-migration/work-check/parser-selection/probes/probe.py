# SPDX-License-Identifier: Apache-2.0
"""One-time parser-selection probe; run through the child probe Makefile."""

from __future__ import annotations

from html.parser import HTMLParser
from importlib.metadata import distribution, distributions
import json
from pathlib import Path
import platform
import sys
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from markdown_it.token import Token


FIXTURES = Path(__file__).parent / "fixtures"


def inline_token_record(token: Token) -> dict[str, object]:
    """Return the public fields used to inspect one inline token."""
    return {"type": token.type, "content": token.content}


class ProbeOutput(TypedDict):
    """Serializable probe metadata and decision-relevant observations."""

    candidate: str
    version: str
    python: str
    platform: str
    dependencies: list[str]
    installed_packages: list[str]
    fixtures: list[dict[str, object]]


def byte_line(text: str, offset: int) -> int:
    """Return a one-based source line for a UTF-8 byte offset."""
    return text.encode("utf-8")[:offset].count(b"\n") + 1


def byte_heading_start(text: str, line_number: int) -> int:
    """Find a parsed heading marker's byte offset in its original source line.

    Returns:
        The byte offset of the first Markdown heading marker on the line.
    """
    lines = text.encode("utf-8").splitlines(keepends=True)
    preceding = sum(len(line) for line in lines[: line_number - 1])
    return preceding + lines[line_number - 1].find(b"#")


def markdown_it_result(name: str, text: str) -> dict[str, object]:
    """Extract headings and excluded block types from markdown-it-py tokens.

    Returns:
        The compact observations for one fixture.
    """
    from markdown_it import MarkdownIt

    tokens = MarkdownIt("commonmark").parse(text)
    stack: list[str] = []
    headings: list[dict[str, object]] = []
    excluded: list[dict[str, object]] = []
    open_to_close = {
        "blockquote_open": "blockquote_close",
        "bullet_list_open": "bullet_list_close",
        "ordered_list_open": "ordered_list_close",
        "list_item_open": "list_item_close",
    }
    close_to_open = {close: opening for opening, close in open_to_close.items()}

    for index, token in enumerate(tokens):
        if token.type in open_to_close:
            stack.append(token.type.removesuffix("_open"))
            continue
        if token.type in close_to_open:
            opening = close_to_open[token.type]
            if opening.removesuffix("_open") in stack:
                stack.pop(stack.index(opening.removesuffix("_open")))
            continue
        if token.type == "heading_open":
            inline = tokens[index + 1]
            if inline.type == "inline":
                line_map = token.map
                headings.append({
                    "level": int(token.tag[1:]),
                    "depth": token.level,
                    "containers": stack.copy(),
                    "line": None if line_map is None else line_map[0] + 1,
                    "text": inline.content,
                    "inline_tokens": [
                        inline_token_record(child) for child in inline.children or []
                    ]
                    if inline.content.startswith("**AC-")
                    else [],
                })
            continue
        if token.type in {"fence", "html_block"}:
            line_map = token.map
            excluded.append({
                "kind": token.type,
                "line": None if line_map is None else line_map[0] + 1,
                "content": token.content,
            })
    return {"fixture": name, "headings": headings, "excluded_blocks": excluded}


def update_pyromark_containers(
    start: object, end: object, containers: list[str]
) -> bool:
    """Update the observed block nesting stack for one pyromark event.

    Returns:
        Whether the event opened or closed a tracked container.
    """
    if isinstance(start, dict) and "BlockQuote" in start:
        containers.append("BlockQuote")
    elif isinstance(start, dict) and "List" in start:
        containers.append("List")
    elif start == "Item":
        containers.append("Item")
    elif isinstance(end, dict) and "BlockQuote" in end:
        containers.remove("BlockQuote")
    elif isinstance(end, dict) and "List" in end:
        containers.remove("List")
    elif end == "Item":
        containers.remove("Item")
    else:
        return False
    return True


def pyromark_result(name: str, text: str) -> dict[str, object]:
    """Extract source-located headings and excluded blocks from pyromark.

    Returns:
        The compact observations for one fixture.
    """
    import pyromark

    headings: list[dict[str, object]] = []
    excluded: list[dict[str, object]] = []
    containers: list[str] = []
    current_heading: dict[str, object] | None = None
    current_code: dict[str, object] | None = None

    for event, source_range in pyromark.events_with_range(text):
        event_value: object = event
        start = event.get("Start") if isinstance(event, dict) else None
        end = event.get("End") if isinstance(event, dict) else None
        if isinstance(start, dict) and "Heading" in start:
            heading = start["Heading"]
            assert isinstance(heading, dict)
            current_heading = {
                "level": heading["level"],
                "containers": containers.copy(),
                "range": source_range,
                "line": byte_line(text, source_range["start"]),
                "line_if_character_offset": text.count("\n", 0, source_range["start"])
                + 1,
                "source_match": source_range["start"]
                == byte_heading_start(text, byte_line(text, source_range["start"])),
                "inline_events": [],
            }
            continue
        if current_heading is not None:
            if isinstance(end, dict) and "Heading" in end:
                headings.append(current_heading)
                current_heading = None
            else:
                inline_events = current_heading["inline_events"]
                assert isinstance(inline_events, list)
                inline_events.append(event_value)
            continue
        if isinstance(start, dict) and "CodeBlock" in start:
            current_code = {
                "kind": "CodeBlock",
                "line": byte_line(text, source_range["start"]),
                "range": source_range,
                "events": [],
            }
            continue
        if current_code is not None:
            if end == "CodeBlock":
                excluded.append(current_code)
                current_code = None
            else:
                events = current_code["events"]
                assert isinstance(events, list)
                events.append(event_value)
            continue
        if update_pyromark_containers(start, end, containers):
            continue
        if start == "HtmlBlock":
            excluded.append({
                "kind": "HtmlBlock",
                "line": byte_line(text, source_range["start"]),
                "range": source_range,
            })
        elif isinstance(event, dict) and "Html" in event:
            excluded.append({"kind": "Html", "content": event["Html"]})

    return {"fixture": name, "headings": headings, "excluded_blocks": excluded}


class CmarkHTMLParser(HTMLParser):
    """Extract only headings and source-bearing exclusion blocks from HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.containers: list[str] = []
        self.headings: list[dict[str, object]] = []
        self.excluded: list[dict[str, object]] = []
        self.current_heading: dict[str, object] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Collect heading structure and enclosing HTML block tags."""
        attributes = dict(attrs)
        if tag in {"blockquote", "ul", "ol", "li"}:
            self.containers.append(tag)
        if tag == "pre":
            self.excluded.append({
                "kind": "pre",
                "containers": self.containers.copy(),
                "sourcepos": attributes.get("data-sourcepos"),
            })
        if len(tag) == 2 and tag[0] == "h" and tag[1].isdigit():
            self.current_heading = {
                "level": int(tag[1]),
                "containers": self.containers.copy(),
                "sourcepos": attributes.get("data-sourcepos"),
                "text": [],
                "inline_tags": [],
            }
        if self.current_heading is not None and tag in {"strong", "em", "code", "a"}:
            tags = self.current_heading["inline_tags"]
            assert isinstance(tags, list)
            tags.append({"tag": tag, "start": True})

    def handle_endtag(self, tag: str) -> None:
        """Close a heading or block container in the rendered HTML stream."""
        if self.current_heading is not None and tag in {"strong", "em", "code", "a"}:
            tags = self.current_heading["inline_tags"]
            assert isinstance(tags, list)
            tags.append({"tag": tag, "start": False})
        if (
            len(tag) == 2
            and tag[0] == "h"
            and tag[1].isdigit()
            and self.current_heading is not None
        ):
            text = self.current_heading["text"]
            assert isinstance(text, list)
            self.current_heading["text"] = "".join(text)
            self.headings.append(self.current_heading)
            self.current_heading = None
        if tag in self.containers:
            self.containers.pop(
                len(self.containers) - 1 - self.containers[::-1].index(tag)
            )

    def handle_data(self, data: str) -> None:
        """Append text contained by the current heading, if any."""
        if self.current_heading is not None:
            text = self.current_heading["text"]
            assert isinstance(text, list)
            text.append(data)

    def handle_comment(self, data: str) -> None:
        """Retain comments emitted by cmark's HTML renderer."""
        self.excluded.append({"kind": "html_comment", "content": data})


def cmarkgfm_result(name: str, text: str) -> dict[str, object]:
    """Extract heading and exclusion structure from cmark-rendered HTML.

    Returns:
        The compact observations for one fixture.
    """
    from cmarkgfm import cmark

    root = cmark.parse_document(text)
    rendered = cmark.render_html(root, cmark.Options.CMARK_OPT_SOURCEPOS)
    parser = CmarkHTMLParser()
    parser.feed(rendered)
    return {
        "fixture": name,
        "headings": parser.headings,
        "excluded_blocks": parser.excluded,
    }


def run(candidate: str) -> ProbeOutput:
    """Run one pinned candidate on every shared fixture.

    Returns:
        Package metadata and the parser's observations.
    """
    package_names = {
        "pyromark": "pyromark",
        "markdown-it-py": "markdown-it-py",
        "cmarkgfm": "cmarkgfm",
    }
    package = distribution(package_names[candidate])
    handlers = {
        "pyromark": pyromark_result,
        "markdown-it-py": markdown_it_result,
        "cmarkgfm": cmarkgfm_result,
    }
    return {
        "candidate": candidate,
        "version": package.version,
        "python": platform.python_version(),
        "platform": f"{platform.system()} {platform.machine()}",
        "dependencies": package.requires or [],
        "installed_packages": sorted(
            f"{installed.metadata.get('Name', 'unknown')}=={installed.version}"
            for installed in distributions()
        ),
        "fixtures": [
            handlers[candidate](path.name, path.read_text())
            for path in sorted(FIXTURES.glob("*.fixture"))
        ],
    }


if __name__ == "__main__":
    sys.stdout.write(json.dumps(run(sys.argv[1]), indent=2) + "\n")
