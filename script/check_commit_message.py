# SPDX-License-Identifier: Apache-2.0
"""Check optional commit bodies for separation and 72-column wrapping."""

from pathlib import Path
import re
import subprocess
import sys

BODY_WIDTH = 72
PREFIX = re.compile(r"^\s*(?:(?:[-*+] |\d+[.)] )|(?:[\w-]+: |BREAKING CHANGE: ))?")


def is_wrapped(line: str) -> bool:
    """Allow a long line only for a standalone, unbreakable token.

    Indentation, bullet markers, and trailer labels may precede that token.
    Tabs count as eight-column tab stops.

    Returns:
        Whether the line fits or contains only an unbreakable token and prefix.
    """
    expanded = line.expandtabs(8)
    if len(expanded) <= BODY_WIDTH:
        return True
    content = PREFIX.sub("", expanded, count=1)
    return len(content.split()) == 1


def check_message(message: str) -> list[str]:
    """Return formatting errors after Git removes comments and whitespace.

    Git's stripspace honors the configured comment character. Empty messages
    remain valid here so Git can handle aborted commits itself.
    """
    cleaned = subprocess.run(
        ["git", "stripspace", "--strip-comments"],
        input=message,
        text=True,
        capture_output=True,
        check=True,
    ).stdout
    lines = cleaned.splitlines()
    errors: list[str] = []
    if len(lines) > 1 and lines[1]:
        errors.append("Separate the subject and body with a blank line.")
    for line in lines[1:]:
        if not is_wrapped(line):
            errors.append(f"Wrap body prose at {BODY_WIDTH} columns: {line}")
    return errors


def main() -> int:
    """Validate the commit-message file supplied by prek.

    Returns:
        Zero on success, or one for formatting errors.
    """
    message = Path(sys.argv[1]).read_text(encoding="utf-8")
    errors = check_message(message)
    for error in errors:
        sys.stderr.write(f"commit message format: {error}\n")
    return int(bool(errors))


if __name__ == "__main__":
    sys.exit(main())
