# SPDX-License-Identifier: Apache-2.0
"""Typed boundaries for the retained static C analysis."""

from typing import Literal

from pydantic import BaseModel


class Combination(BaseModel):
    """One public, manifest-bound packet."""

    rule_id: str
    file_id: str
    function_name: str
    function_file: str
    rule_file: str
    prompt_sha256: str
    prompt_bytes: int


class Function(BaseModel):
    """Function packet identity."""

    function_file: str
    sha256: str


class Source(BaseModel):
    """Source digest."""

    sha256: str


class Manifest(BaseModel):
    """Reviewed manifest fields consumed by scoring."""

    rules: dict[str, str]
    sources: dict[str, Source]
    functions: list[Function]
    combinations: list[Combination]
    shared_sha256: str


class Policy(BaseModel):
    """Pre-grading policy fields."""

    blocks: list[str]
    boundary_affected_positions: dict[str, list[int]]
    manifest_sha256: str
    private_index_sha256: str


class BlockIdentity(BaseModel):
    """Observed identity of a block."""

    run_id: str
    model: str
    effort: Literal["none", "low", "medium", "high"]
    concurrency: int
    thread_ids_sha256: str


class Identities(BaseModel):
    """Identity facts recorded after grading, not a new scoring policy."""

    recorded_after_grading: Literal[True]
    pre_grading_policy_sha256: str
    ordered_prompt_sha256: list[str]
    blocks: dict[str, BlockIdentity]


class InventoryRow(BaseModel):
    """Retained artifact identity."""

    relative_path: str
    size: int
    sha256: str


class Archive(BaseModel):
    """Archive identity."""

    file: str
    sha256: str


class Inventory(BaseModel):
    """Archive and launcher inventory."""

    blocks: dict[str, str]
    archives: dict[str, Archive]
    launcher_evidence: list[InventoryRow]
