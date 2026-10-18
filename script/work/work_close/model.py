# SPDX-License-Identifier: Apache-2.0
"""Typed values shared by read-only Work closure planning."""

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
