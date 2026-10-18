# SPDX-License-Identifier: Apache-2.0
"""Command-line boundary for read-only Work closure planning."""

import argparse
import sys

from script.markdown.markdown_it_adapter import MarkdownItParser
from script.work_close.plan import ClosePlanningError, make_plan, render_plan


def main(arguments: list[str] | None = None) -> int:
    """Print a closure plan or pending decisions without changing repository state.

    Returns:
        0 when a plan or pending decision was produced, or 2 on invalid input.
    """
    parser = argparse.ArgumentParser(description="Plan authorized Work closure")
    parser.add_argument("paths", nargs="+", help="explicit Work README paths")
    parser.add_argument(
        "--abort-remaining",
        action="store_true",
        help="plan ABORT for TODO criteria after maintainer confirmation",
    )
    options = parser.parse_args(arguments)
    try:
        plan = make_plan(options.paths, options.abort_remaining, MarkdownItParser())
    except ClosePlanningError as error:
        sys.stderr.write(f"work-close: {error}\n")
        return 2
    sys.stdout.write(render_plan(plan))
    return 0
