# SPDX-License-Identifier: Apache-2.0
"""Exercise cleanup Make proxies against disposable Git worktrees."""

import os
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[3]


def git(repo, *args):
    """Run one fixture Git operation and return its output."""
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout


@pytest.fixture
def repository(tmp_path):
    """Provide a committed repository without a prepared Python environment."""
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "master")
    (repo / "Makefile").write_bytes((ROOT / "Makefile").read_bytes())
    git(repo, "add", "Makefile")
    git(
        repo,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.com",
        "commit",
        "-m",
        "init",
    )
    return repo


def make(repo, target, **values):
    """Invoke the actual Make target with literal caller values."""
    env = os.environ.copy()
    for name in ("MAKEFLAGS", "MAKEOVERRIDES", "MFLAGS", "WORKTREE", "EXPIRE"):
        env.pop(name, None)
    return subprocess.run(
        ["make", target, *(f"{key}={value}" for key, value in values.items())],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


@pytest.mark.parametrize("target", ["worktree-prune-preview", "worktree-prune"])
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/worktree-cleanup/README.md",
    ac="AC-2",
)
def test_missing_inputs_fail_before_mutation(repository, target):
    """AC-2: Missing selection or expiry fails without changing registrations."""
    listing = make(repository, "worktree-list").stdout
    result = make(repository, target)
    assert result.returncode != 0
    assert "Usage:" in result.stderr
    assert make(repository, "worktree-list").stdout == listing


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/worktree-cleanup/README.md",
    ac="AC-3",
)
def test_prune_preview_and_apply_share_expiry_and_preserve_live_and_locked(
    repository, tmp_path
):
    """AC-3: Explicit expiry previews repository-wide pruning and preserves locks."""
    paths = {name: tmp_path / name for name in ("live", "missing", "locked")}
    for name, path in paths.items():
        git(repository, "worktree", "add", "-b", name, str(path))
    git(repository, "worktree", "lock", str(paths["locked"]))
    shutil.rmtree(paths["missing"])
    shutil.rmtree(paths["locked"])
    before = make(repository, "worktree-list").stdout
    old_preview = make(repository, "worktree-prune-preview", EXPIRE="2000-01-01")
    old_apply = make(repository, "worktree-prune", EXPIRE="2000-01-01")
    assert old_preview.returncode == old_apply.returncode == 0
    assert make(repository, "worktree-list").stdout == before
    preview = make(repository, "worktree-prune-preview", EXPIRE="now")
    assert preview.returncode == 0
    assert "Removing worktrees/missing:" in preview.stderr
    assert "Removing worktrees/locked:" not in preview.stderr
    assert "Repository-wide" in preview.stdout
    assert make(repository, "worktree-list").stdout == before
    applied = make(repository, "worktree-prune", EXPIRE="now")
    assert applied.returncode == 0
    assert applied.stdout == preview.stdout
    assert applied.stderr == preview.stderr
    after = make(repository, "worktree-list").stdout
    assert str(paths["missing"]) not in after
    assert str(paths["locked"]) in after
    assert str(paths["live"]) in after
    assert paths["live"].is_dir()
    assert "refs/heads/missing" in git(repository, "show-ref", "--heads")
