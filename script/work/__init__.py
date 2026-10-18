# SPDX-License-Identifier: Apache-2.0
"""Shared contract interpretation and source handling for Work tools.

``contract`` interprets parsed Markdown blocks into checked criteria and
structural findings. ``source`` discovers selected contract README files and
reads their UTF-8 text. The ``work_check`` subpackage uses these shared
responsibilities to report structural diagnostics; ``work_close`` uses them to
prepare repository- and pull-request-bound closure plans. Both depend on the
common source and contract meanings rather than defining separate readers or
interpreters.
"""
