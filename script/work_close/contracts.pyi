# SPDX-License-Identifier: Apache-2.0
"""Pure contract adaptation and independent per-Work outcome decisions."""

from script.markdown.model import MarkdownBlock
from script.work_close.model import (
    AbortRemainingDecision,
    FileSnapshot,
    WorkContract,
    WorkResult,
)

def parse_contract(
    source: FileSnapshot, blocks: tuple[MarkdownBlock, ...]
) -> WorkContract:
    """Validate structure and adapt criterion headings, including ABORT reasons.

    Reuse the work_check rules after extending their authoritative criterion
    status model to ABORT; do not introduce a competing heading parser.
    Blocks must describe this exact UTF-8 source, parsed at ingress.

    Raises:
        ClosurePlanningError: Invalid structure, status, reason, or identity.
    """
    ...

def plan_work_results(
    contracts: tuple[WorkContract, ...], *, abort_remaining: bool
) -> tuple[WorkResult, ...] | AbortRemainingDecision:
    """Derive each result independently, or report all remaining TODO outcomes.

    A true flag proposes ABORT with a nonempty explicit-abandonment reason for
    each TODO; existing abort reasons remain unchanged. No parent or sibling's
    criterion status establishes another Work's result.
    """
    ...
