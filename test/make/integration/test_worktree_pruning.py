# SPDX-License-Identifier: Apache-2.0
"""Observe pruning expiry, preview, and retention through real Git and Make."""

from pathlib import Path
import shutil

import pytest

from test.make.worktree_support import GitState, creation_repository, files_under


@pytest.mark.parametrize(
    "target", ["worktree-prune-preview", "worktree-prune"], ids=["preview", "apply"]
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/make/worktree-cleanup/pruning/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/worktree-cleanup/README.md",
    ac="AC-2",
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


@pytest.mark.covers(
    work="doc/feat/testing-conformance/make/worktree-cleanup/pruning/README.md",
    ac="AC-2",
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/worktree-cleanup/README.md",
    ac="AC-3",
)
def test_cutoff_preview_and_apply_preserve_live_locked_and_all_refs(
    tmp_path: Path,
) -> None:
    """AC-2: Given stale, live, and locked worktrees, a historical cutoff
    retains ineligible registrations; now-preview is read-only and now-apply
    prunes only eligible stale registrations while preserving live/locked state
    and all branch refs.

    Cleanup AC-3: Explicit expiry previews repository-wide pruning and preserves locks.
    This case covers historical cutoff and now preview/apply retention.
    """
    # Given
    repository = creation_repository(tmp_path / "repo")
    live, missing, locked = (tmp_path / name for name in ("live", "missing", "locked"))
    repository.git("worktree", "add", "-b", "live", str(live))
    repository.git("worktree", "add", "-b", "missing", str(missing))
    repository.git("worktree", "add", "-b", "locked", str(locked))
    repository.git("worktree", "lock", str(locked))
    shutil.rmtree(missing)
    shutil.rmtree(locked)
    before = repository.state()
    source_files = files_under(repository.sandbox.directory)
    live_files = files_under(live)
    head = repository.git("rev-parse", "missing").stdout.strip()

    # When: a historical cutoff makes the newly stale registration ineligible.
    old_preview = repository.sandbox.run("worktree-prune-preview", "EXPIRE=2000-01-01")
    old_apply = repository.sandbox.run("worktree-prune", "EXPIRE=2000-01-01")

    # Then
    assert old_preview.exit_code == old_apply.exit_code == 0
    assert repository.state() == before
    assert files_under(repository.sandbox.directory) == source_files
    assert files_under(live) == live_files

    # When: preview the eligible stale registration without applying pruning.
    preview = repository.sandbox.run("worktree-prune-preview", "EXPIRE=now")

    # Then
    assert preview.exit_code == 0, preview.output
    assert "Removing worktrees/missing:" in preview.stderr
    assert "Removing worktrees/locked:" not in preview.stderr
    assert "Repository-wide" in preview.stdout
    assert repository.state() == before
    assert files_under(repository.sandbox.directory) == source_files
    assert files_under(live) == live_files

    # When: apply the identical expiry selection.
    applied = repository.sandbox.run("worktree-prune", "EXPIRE=now")

    # Then
    assert applied.exit_code == 0, applied.output
    assert applied.stdout == preview.stdout
    assert applied.stderr == preview.stderr
    assert repository.state() == GitState(
        before.refs,
        before.registrations.replace(
            f"worktree {missing}\nHEAD {head}\nbranch refs/heads/missing\n"
            "prunable gitdir file points to non-existent location\n\n",
            "",
        ),
    )
    assert live.is_dir()
    assert not missing.exists()
    assert not locked.exists()
    assert files_under(live) == live_files
    assert files_under(repository.sandbox.directory) == source_files


@pytest.mark.covers(
    work="doc/feat/testing-conformance/make/worktree-cleanup/pruning/README.md",
    ac="AC-2",
)
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
