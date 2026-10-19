# SPDX-License-Identifier: Apache-2.0
"""Immutable planning values; construction invariants await implementation.

Paths are repository-relative, normalized, contained, non-symlink paths.
Commit IDs are full object IDs, and branch names are full refs. Constructors
will enforce owned invariants without reparsing validated child values.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from script.markdown.model import SourceLocation

type ClosureStatus = Literal["DONE", "ABORT"]

@dataclass(frozen=True)
class ClosureRequest:
    """Exact nonempty README selection; never implicitly select descendants.

    The Boolean carries the separate Make ABORT_REMAINING flag. It is a caller
    instruction, not proof of session authorization. The constructor rejects
    empty selections, directories, options, and non-Work README paths.
    """

    contracts: tuple[Path, ...]
    abort_remaining: bool

@dataclass(frozen=True)
class FileSnapshot:
    """A tracked regular file's exact preimage at the captured head."""

    path: Path
    content: bytes

@dataclass(frozen=True)
class BranchTips:
    """Local and advertised upstream tips captured without fetching or writing."""

    local_ref: str
    local_oid: str
    remote: str
    remote_ref: str
    remote_oid: str

@dataclass(frozen=True)
class PullRequest:
    """Normalized host metadata; completion signals never establish review.

    Repository identity includes the host. A missing reviewed head remains
    explicit. The adapter must preserve head repository identity for forks.
    """

    repository: str
    number: int
    state: Literal["OPEN", "CLOSED", "MERGED"]
    base_ref: str
    head_repository: str
    head_ref: str
    head_oid: str
    reviewed_head_oid: str | None

@dataclass(frozen=True)
class RepositorySnapshot:
    """Observed Git facts, not a claim that closure is ready.

    Dirty paths include staged, unstaged, and untracked files. Documents and
    artifacts are captured separately by the observation adapter; reading HEAD
    uses optional-lock-free Git queries and never refreshes the index.
    """

    root: Path
    repository: str
    head_oid: str
    tips: BranchTips
    pull_request: PullRequest
    dirty_paths: tuple[Path, ...]

@dataclass(frozen=True)
class DoneCriterion:
    """An existing DONE heading, scoped by its owning contract."""

    identifier: str
    location: SourceLocation

@dataclass(frozen=True)
class TodoCriterion:
    """An unverified heading requiring an explicit abort decision."""

    identifier: str
    location: SourceLocation

@dataclass(frozen=True)
class AbortedCriterion:
    """An existing ABORT outcome with its retained nonempty reason."""

    identifier: str
    location: SourceLocation
    reason: str

type Criterion = DoneCriterion | TodoCriterion | AbortedCriterion

@dataclass(frozen=True)
class WorkContract:
    """Validated nonempty criteria with unique identities and source ranges."""

    source: FileSnapshot
    criteria: tuple[Criterion, ...]

@dataclass(frozen=True)
class PlannedAbort:
    """A proposed TODO-to-ABORT transition, never an on-disk change in AC-1."""

    contract: Path
    criterion: TodoCriterion
    reason: str

@dataclass(frozen=True)
class WorkResult:
    """One Work's disposition, derived solely from its own criteria.

    DONE requires all criteria DONE; ABORT requires an existing or proposed
    abort and no unresolved TODO. Planned abort identities/reasons survive as
    plan data for the later publication phase to preserve in Git history.
    """

    contract: WorkContract
    status: ClosureStatus
    planned_aborts: tuple[PlannedAbort, ...]

@dataclass(frozen=True)
class FileReplacement:
    """An exact proposed replacement, including a source preimage for rechecks."""

    before: FileSnapshot
    after: bytes

@dataclass(frozen=True)
class FileRemoval:
    """An exact proposed contract or unneeded supporting-artifact removal."""

    before: FileSnapshot

type FileChange = FileReplacement | FileRemoval

@dataclass(frozen=True)
class AbortRemainingDecision:
    """Report every selected TODO and ask whether to abort remaining outcomes.

    Return to the caller immediately; cancellation/no answer performs no work.
    Rerunning the same selection with the confirmed flag recomputes all facts.
    """

    remaining: tuple[tuple[Path, TodoCriterion], ...]
    question: str

@dataclass(frozen=True)
class ReferenceDecision:
    """A live link or supporting-artifact use without an unambiguous disposition."""

    source: Path
    target: Path
    location: SourceLocation
    question: str

type PendingDecision = AbortRemainingDecision | ReferenceDecision

@dataclass(frozen=True)
class PendingPlan:
    """Nonempty decisions; this variant cannot be consumed as a ready plan."""

    decisions: tuple[PendingDecision, ...]

@dataclass(frozen=True)
class ReadyClosurePlan:
    """Read-only proposal bound to selection, reviewed head, tips and preimages.

    Results cover exactly the request. Changes have unique contained paths;
    no unselected contract is removed. The plan never grants authorization or
    proves semantic acceptance. Application must recheck all captured facts.
    """

    request: ClosureRequest
    repository: RepositorySnapshot
    results: tuple[WorkResult, ...]
    changes: tuple[FileChange, ...]

type PlanningResult = ReadyClosurePlan | PendingPlan

class ClosurePlanningError(ValueError):
    """Invalid/unsafe input, inconsistent observation, or read-boundary failure."""
