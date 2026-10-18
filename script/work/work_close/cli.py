# SPDX-License-Identifier: Apache-2.0
"""Parse command arguments and present read-only closure planning results.

API:
* ``main`` runs the closure planning command for the supplied arguments.
* ``--abort-remaining`` requests ABORT proposals for remaining TODO criteria.

Implementation:
Argument parsing accepts explicit README paths and the optional abort proposal.

The command boundary writes rendered plan text to standard output and a
handled ``ClosePlanningError`` to standard error; these outcomes return status
zero and two, respectively.

Connections:
* ``main`` supplies a Markdown parser and parsed options to ``plan.make_plan``.
* Successful plans pass to ``plan.render_plan`` for display.
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
