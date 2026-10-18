# SPDX-License-Identifier: Apache-2.0
"""Immutable records for proposed Work closure and observed metadata.

API:
Consumers receive a ``ClosePlan`` containing the selected Works, proposed
reference updates, repository and pull request observations, and overall
readiness. Each ``WorkPlan`` groups a Work's ``CriterionPlan`` values with its
``WorkResult`` and optional reason. A ``CriterionPlan`` pairs a criterion's
current status with its proposed result; ``WorkResult`` distinguishes pending,
completed, and aborted outcomes. Each ``ReferencePlan`` records a source span
and its proposed replacement.

Representation:
Frozen dataclasses and tuples carry planning results between construction and
rendering. The records describe values; they do not validate fields, compute
readiness, inspect the repository, or update files.
"""

from dataclasses import dataclass
from typing import Literal

from script.work.contract import CriterionStatus

type WorkResult = Literal["PENDING", "DONE", "ABORT"]


@dataclass(frozen=True)
class CriterionPlan:
    """One criterion's current and proposed status."""

    identifier: str
    status: CriterionStatus
    result: CriterionStatus


@dataclass(frozen=True)
class WorkPlan:
    """One selected Work's proposed closure result."""

    path: str
    title: str
    result: WorkResult
    criteria: tuple[CriterionPlan, ...]
    reason: str | None


@dataclass(frozen=True)
class ReferencePlan:
    """One canonical parent/dependency source span and proposed update."""

    path: str
    line_start: int
    line_end: int
    before: str
    after: str | None


@dataclass(frozen=True)
class ClosePlan:
    """Read-only closure plan with repository and PR tip observations."""

    ready: bool
    repository: str
    pr_number: int
    branch: str
    local_tip: str
    remote_tip: str
    pr_head_repository: str
    pr_head: str
    works: tuple[WorkPlan, ...]
    references: tuple[ReferencePlan, ...]
