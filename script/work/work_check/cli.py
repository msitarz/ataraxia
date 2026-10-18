# SPDX-License-Identifier: Apache-2.0
"""Command-line boundary for structural Work contract checking."""

import argparse
from pathlib import Path
import sys

from script.markdown.markdown_it_adapter import MarkdownItParser
from script.markdown.model import MarkdownParseError
from script.work.contract import inspect_work
from script.work.source import WorkSourceError, discover_work_sources


def main(arguments: list[str] | None = None) -> int:
    """Check discovered contracts and return the documented process status.

    Returns:
        0 for success, 1 for content failures, or 2 for invocation/input errors.
    """
    parser = argparse.ArgumentParser(description="Check Work contract structure")
    parser.add_argument(
        "paths", nargs="*", help="repository-local Work README or subtree"
    )
    options = parser.parse_args(arguments)
    root = Path.cwd().resolve(strict=True)
    try:
        contracts = discover_work_sources(root, options.paths)
    except WorkSourceError as error:
        sys.stderr.write(f"work-check: {error}\n")
        return 2

    markdown = MarkdownItParser()
    findings = []
    for contract in contracts:
        relative = contract.path.relative_to(root).as_posix()
        try:
            for finding in inspect_work(markdown.parse(contract.text)).diagnostics:
                findings.append((relative, finding))
        except MarkdownParseError as error:
            sys.stderr.write(f"work-check: cannot parse {relative}: {error}\n")
            return 2
    for path, finding in findings:
        sys.stdout.write(f"{path}:{finding.line}: {finding.rule}: {finding.context}\n")
    return 1 if findings else 0
