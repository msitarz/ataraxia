# SPDX-License-Identifier: Apache-2.0
"""Consumer-owned observation port, pure safety decisions, and composition."""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from script.markdown.model import MarkdownBlock, SourceLocation
from script.work_close.model import (
    ClosureRequest,
    FileChange,
    FileSnapshot,
    PlanningResult,
    ReferenceDecision,
    RepositorySnapshot,
    WorkContract,
    WorkResult,
)

@dataclass(frozen=True)
class DocumentSnapshot:
    """One exact UTF-8 file and its repository Markdown parser output."""

    source: FileSnapshot
    blocks: tuple[MarkdownBlock, ...]

@dataclass(frozen=True)
class RepositoryLink:
    """A normalized local link, including resolved reference-style links.

    Ingress resolves link syntax, anchors, escaping and source-relative paths.
    This retains all live local links, not just links to selected contracts,
    so supporting-artifact retention can consider unselected Works/documents.
    """

    source: Path
    target: Path
    location: SourceLocation

@dataclass(frozen=True)
class ClosureObservation:
    """One consistent read of selected contracts and their reference context.

    Documents cover repository-owned live Markdown, including parent/dependency
    maps; artifacts cover supporting files whose retention is under review.
    All sources match the captured head. The adapter checks head/tips again
    after collection and refuses a mixed observation.
    """

    repository: RepositorySnapshot
    contracts: tuple[WorkContract, ...]
    documents: tuple[DocumentSnapshot, ...]
    links: tuple[RepositoryLink, ...]
    artifacts: tuple[FileSnapshot, ...]

class ClosureReader(Protocol):
    """Consumer-owned read-only effect boundary, supplied by composition.

    Owns process/file handles and closes them on success/failure. It validates
    untyped Git/host output once, contained paths and regular tracked files,
    UTF-8/Markdown, complete reference discovery and consistent snapshots.
    It exposes no write, fetch, checkout, index-refresh, or publication method.
    """

    def observe(self, request: ClosureRequest, /) -> ClosureObservation:
        """Read Git, host metadata and repository context without mutation.

        Raises:
            ClosurePlanningError: Reads fail, paths are unsafe, selection is
                missing/invalid, or metadata/sources cannot be normalized.
        """
        ...

def validate_closure_boundary(
    request: ClosureRequest, observation: ClosureObservation
) -> None:
    """Validate selection, clean state, reviewed open PR and exact branch tips.

    Require the selected contracts to match their reviewed-head versions and
    PR scope; reject detached/protected targets, mismatched repositories/refs,
    missing review binding and unequal HEAD/local/remote/PR/reviewed object IDs.
    Selection is exact: ancestry never adds contracts or infers authorization.

    Raises:
        ClosurePlanningError: The observation cannot safely bind this request.
    """
    ...

def plan_reference_changes(
    observation: ClosureObservation, results: tuple[WorkResult, ...]
) -> tuple[FileChange, ...] | tuple[ReferenceDecision, ...]:
    """Plan removals and mechanical rewrites using lifecycle reference rules.

    Preserve map entry titles/purpose while removing selected contract links;
    use each Work's own result and abort reason. Remove other obsolete live
    links only when mechanical; request steering for semantic retargeting or
    ambiguous artifact retention. Preserve active dependencies and unrelated
    text/files. Return changes only if every reference has a safe disposition.
    """
    ...

def build_closure_plan(
    request: ClosureRequest, observation: ClosureObservation
) -> PlanningResult:
    """Purely validate, decide Work results, and assemble a complete proposal.

    Pending TODO outcomes return an abort question before further planning.
    Reference ambiguity returns decisions rather than a partially ready plan.

    Raises:
        ClosurePlanningError: Boundary checks or plan invariants fail.
    """
    ...

def prepare_closure(request: ClosureRequest, reader: ClosureReader) -> PlanningResult:
    """Effectful orchestration: observe once, then call the pure plan builder.

    Raises:
        ClosurePlanningError: Observation or planning refuses the request.
    """
    ...
