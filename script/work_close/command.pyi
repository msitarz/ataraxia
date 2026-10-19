# SPDX-License-Identifier: Apache-2.0
"""Future Make ingress and composition root; no executable entry point yet."""

from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from script.work_close.model import ClosureRequest, PlanningResult

def parse_request(
    paths: Sequence[str], *, abort_remaining: str | None
) -> ClosureRequest:
    """Adapt exact README arguments and the separate Make confirmation flag.

    Only absent/false and true flag values are accepted; reject positional
    options, empty selection and unsupported flag values. No authorization
    file/token and no interactive input are consumed.

    Raises:
        ClosurePlanningError: The invocation is invalid.
    """
    ...

def render_plan(result: PlanningResult) -> str:
    """Render ready changes/results or pending questions without writing output."""
    ...

def main(
    paths: Sequence[str], *, root: Path, abort_remaining: str | None
) -> Literal[0, 1, 2]:
    """Compose parser/reader/planner and report through the command boundary.

    Return 0 for ready, 1 for pending decisions, 2 for invalid/unsafe input or
    observation failure. Never wait for input, apply a plan, stage, commit or
    push. A future Make work-close recipe owns environment/tool discovery and
    supplies ARGS and ABORT_REMAINING separately. Output belongs here, not in
    the core planner or read adapter.
    """
    ...
