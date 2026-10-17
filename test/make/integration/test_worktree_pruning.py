# SPDX-License-Identifier: Apache-2.0
"""Observe pruning expiry, preview, and retention through real Git and Make."""

from dataclasses import dataclass
from pathlib import Path
import shutil

import pytest

from test.make.worktree_support import (
    CreationRepository,
    GitState,
    creation_repository,
    files_under,
)


@dataclass(frozen=True)
class PruningScenario:
    """Worktree state shared by cutoff, preview, and apply scenarios."""

    repository: CreationRepository
    live: Path
    missing: Path
    locked: Path
    before: GitState
    source_files: dict[str, bytes]
    live_files: dict[str, bytes]
    missing_head: str


def pruning_scenario(tmp_path: Path) -> PruningScenario:
    """Create live, stale, and locked registrations with stable snapshots."""
    repository = creation_repository(tmp_path / "repo")
    live, missing, locked = (tmp_path / name for name in ("live", "missing", "locked"))
    repository.git("worktree", "add", "-b", "live", str(live))
    repository.git("worktree", "add", "-b", "missing", str(missing))
    repository.git("worktree", "add", "-b", "locked", str(locked))
    repository.git("worktree", "lock", str(locked))
    shutil.rmtree(missing)
    shutil.rmtree(locked)
    return PruningScenario(
        repository,
        live,
        missing,
        locked,
        repository.state(),
        files_under(repository.sandbox.directory),
        files_under(live),
        repository.git("rev-parse", "missing").stdout.strip(),
    )


def assert_unmodified(scenario: PruningScenario) -> None:
    """Check that preview paths preserve refs, registrations, and files."""
    assert scenario.repository.state() == scenario.before
    assert files_under(scenario.repository.sandbox.directory) == scenario.source_files
    assert files_under(scenario.live) == scenario.live_files


@pytest.mark.parametrize(
    "target", ["worktree-prune-preview", "worktree-prune"], ids=["preview", "apply"]
)
def test_missing_expiry_refuses_without_mutation(tmp_path: Path, target: str) -> None:
    """AC-1: Given missing expiry, preview and apply refuse with defined
    failure codes before changing files, refs, or registrations.

    Cleanup AC-2: Missing selection or expiry fails without changing registrations.
    This case covers missing expiry for each pruning target.
    """
    # Given
    repository = creation_repository(tmp_path / "repo")
    before = repository.state()
    files = files_under(repository.sandbox.directory)

    # When
    result = repository.sandbox.run(target)

    # Then
    assert result.exit_code == 2, result.output
    assert f"Usage: make {target} EXPIRE=date" in result.stderr
    assert repository.state() == before
    assert files_under(repository.sandbox.directory) == files


def test_historical_cutoff_keeps_newly_stale_registration(tmp_path: Path) -> None:
    """A historical cutoff retains a worktree registered after that cutoff."""
    # Given
    scenario = pruning_scenario(tmp_path)

    # When
    preview = scenario.repository.sandbox.run(
        "worktree-prune-preview", "EXPIRE=2000-01-01"
    )
    applied = scenario.repository.sandbox.run("worktree-prune", "EXPIRE=2000-01-01")

    # Then
    assert preview.exit_code == applied.exit_code == 0
    assert_unmodified(scenario)


def test_preview_and_apply_preserve_live_locked_and_all_refs(tmp_path: Path) -> None:
    """Preview is read-only; apply prunes only eligible stale registrations."""
    # Given
    scenario = pruning_scenario(tmp_path)

    # When
    preview = scenario.repository.sandbox.run("worktree-prune-preview", "EXPIRE=now")

    # Then
    assert preview.exit_code == 0, preview.output
    assert "Removing worktrees/missing:" in preview.stderr
    assert "Removing worktrees/locked:" not in preview.stderr
    assert "Repository-wide" in preview.stdout
    assert_unmodified(scenario)

    # When
    applied = scenario.repository.sandbox.run("worktree-prune", "EXPIRE=now")

    # Then
    assert applied.exit_code == 0, applied.output
    assert applied.stdout == preview.stdout
    assert applied.stderr == preview.stderr
    assert scenario.repository.state() == GitState(
        scenario.before.refs,
        scenario.before.registrations.replace(
            f"worktree {scenario.missing}\nHEAD {scenario.missing_head}\n"
            "branch refs/heads/missing\n"
            "prunable gitdir file points to non-existent location\n\n",
            "",
        ),
    )
    assert scenario.live.is_dir()
    assert not scenario.missing.exists()
    assert not scenario.locked.exists()
    assert files_under(scenario.live) == scenario.live_files
    assert files_under(scenario.repository.sandbox.directory) == scenario.source_files


def test_hostile_expiry_is_literal_and_preserves_repository(tmp_path: Path) -> None:
    """AC-2: Given stale, live, and locked worktrees, a historical cutoff
    retains ineligible registrations; now-preview is read-only and now-apply
    prunes only eligible stale registrations while preserving live/locked state
    and all branch refs.

    This case covers literal expiry handling without executing caller expressions.
    """
    # Given
    repository = creation_repository(tmp_path / "repo")
    before = repository.state()
    files = files_under(repository.sandbox.directory)
    expiry = "now;$(shell touch PWNED)`touch PWNED`$HOME"

    # When
    result = repository.sandbox.run("worktree-prune-preview", f"EXPIRE={expiry}")

    # Then
    assert result.exit_code == 0, result.output
    assert expiry in result.stdout
    assert not (repository.sandbox.directory / "PWNED").exists()
    assert repository.state() == before
    assert files_under(repository.sandbox.directory) == files
