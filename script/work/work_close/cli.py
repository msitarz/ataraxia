# SPDX-License-Identifier: Apache-2.0
"""Parse command arguments and present read-only closure planning results.

API:
``main`` accepts an optional argument list and prints the stable rendering of
a plan. It returns zero when a plan is produced and two when a
``ClosePlanningError`` rejects the input, writing that error to standard
error. The ``--abort-remaining`` option controls whether TODO criteria are
proposed as ABORT; the command reports the proposal.

Implementation:
This module owns argument parsing and the standard output/error boundary. Plan
construction and repository observations belong to ``plan``; the CLI supplies
the Markdown parser when it requests a plan.
"""

import argparse
import sys

from script.markdown.markdown_it_adapter import MarkdownItParser
from script.work.work_close.plan import ClosePlanningError, make_plan, render_plan


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
