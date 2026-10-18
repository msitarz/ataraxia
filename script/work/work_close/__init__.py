# SPDX-License-Identifier: Apache-2.0
"""Prepare and present read-only plans for Work closure.

Programmatic consumers use ``plan.make_plan`` to build a plan and
``plan.render_plan`` to produce review text. Command-line consumers use
``cli.main`` directly or invoke ``python -m script.work.work_close`` through
``__main__``. ``model`` supplies the records passed between planning and
rendering. The plan reads contracts and repository metadata, proposes
criterion outcomes and reference updates, and feeds the CLI presentation; it
does not update contract files or Git state.
"""
