# SPDX-License-Identifier: Apache-2.0
"""Shared contract interpretation and source handling for Work tools.

Modules and subpackages:
* ``contract`` interprets parsed Markdown blocks into checked criteria and
  structural findings.
* ``source`` discovers selected contract README files and reads their text.
* ``work_check`` reports structural diagnostics using the shared source and
  contract interpretation.
* ``work_close`` prepares repository- and pull-request-bound closure plans
  using the shared source and contract interpretation.

Connections:
* ``source`` supplies contract text to consumers, which parse it into blocks
  for ``contract`` to interpret.
* ``work_check`` and ``work_close`` build their distinct command behavior on
  these shared source and structure responsibilities.
"""
