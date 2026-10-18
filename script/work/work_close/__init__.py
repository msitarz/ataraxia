# SPDX-License-Identifier: Apache-2.0
"""Prepare and present read-only plans for Work closure.

API:
* ``plan.make_plan`` builds a closure plan from explicit Work selections and a
  Markdown parser.
* ``plan.render_plan`` formats a closure plan as review text.
* ``cli.main`` parses command arguments, prints a plan, and returns a command
  status.
* ``python -m script.work.work_close`` invokes the command through
  ``__main__``.
* ``model`` defines the records passed between planning and rendering.

Implementation:
The package's planning flow prepares a reviewable proposal without updating
contract files or Git state.

Connections:
* ``plan`` reads contract sources and repository metadata to produce proposed
  outcomes, reference updates, and observations.
* ``cli.main`` supplies the parser to ``plan.make_plan`` and prints the result
  from ``plan.render_plan``.
"""
