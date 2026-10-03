# SPDX-License-Identifier: Apache-2.0
"""Exercise cleanup Make proxies against disposable Git worktrees."""

import os
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]


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


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/worktree-cleanup/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/worktree-cleanup/README.md",
    ac="AC-2",
)
def test_remove_literal_path_retains_branch_and_unrelated_checkout(
    repository, tmp_path
):
    """AC-1/AC-2: Clean removal is literal and retains branches and other worktrees."""
    destination = tmp_path / "agent's tree;$(shell touch PWNED)`touch PWNED`$HOME"
    unrelated = tmp_path / "active"
    git(repository, "worktree", "add", "-b", "completed", str(destination))
    git(repository, "worktree", "add", "-b", "active", str(unrelated))
    before = make(repository, "worktree-list")
    assert before.returncode == 0
    assert str(destination) in before.stdout
    help_output = make(repository, "help").stdout
    for target in (
        "worktree-list",
        "worktree-remove",
        "worktree-prune-preview",
        "worktree-prune",
    ):
        assert f"make {target} " in help_output
    result = make(repository, "worktree-remove", WORKTREE=destination)
    assert result.returncode == 0, result.stderr
    assert not destination.exists()
    assert not (repository / "PWNED").exists()
    assert unrelated.is_dir()
    assert "refs/heads/completed" in git(repository, "show-ref", "--heads")
    listing = make(repository, "worktree-list")
    assert str(destination) not in listing.stdout
    assert str(unrelated) in listing.stdout


@pytest.mark.parametrize("condition", ["main", "dirty", "untracked", "locked"])
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/worktree-cleanup/README.md",
    ac="AC-2",
)
def test_unsafe_remove_preserves_data_and_registration(repository, tmp_path, condition):
    """AC-2: Git refusal preserves main, dirty, untracked, and locked checkouts."""
    destination = repository if condition == "main" else tmp_path / "completed"
    if condition != "main":
        git(repository, "worktree", "add", "-b", "completed", str(destination))
    if condition == "dirty":
        with (destination / "Makefile").open("a") as stream:
            stream.write("# undelivered\n")
    if condition == "untracked":
        (destination / "keep").write_text("undelivered")
    if condition == "locked":
        git(repository, "worktree", "lock", str(destination))
    contents = (destination / "Makefile").read_bytes()
    refs = git(repository, "show-ref", "--heads")
    listing = make(repository, "worktree-list").stdout
    result = make(repository, "worktree-remove", WORKTREE=destination)
    assert result.returncode != 0
    assert (destination / "Makefile").read_bytes() == contents
    assert git(repository, "show-ref", "--heads") == refs
    assert make(repository, "worktree-list").stdout == listing
    if condition == "untracked":
        assert (destination / "keep").read_text() == "undelivered"


@pytest.mark.parametrize(
    "target", ["worktree-remove", "worktree-prune-preview", "worktree-prune"]
)
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
    ac="AC-2",
)
def test_unknown_worktree_failure_preserves_repository(repository, tmp_path):
    """AC-2: An unsupported removal selection fails without filesystem fallback."""
    unrelated = tmp_path / "unregistered"
    unrelated.mkdir()
    (unrelated / "keep").write_text("preserve")
    listing = make(repository, "worktree-list").stdout
    result = make(repository, "worktree-remove", WORKTREE=unrelated)
    assert result.returncode != 0
    assert (unrelated / "keep").read_text() == "preserve"
    assert make(repository, "worktree-list").stdout == listing


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/worktree-cleanup/README.md",
    ac="AC-2",
)
def test_submodule_worktree_refusal_is_retained(repository, tmp_path):
    """AC-2: Populated submodules retain Git's unsupported-removal refusal."""
    module = tmp_path / "module"
    git(repository, "clone", str(repository), str(module))
    git(
        repository,
        "-c",
        "protocol.file.allow=always",
        "submodule",
        "add",
        str(module),
        "module",
    )
    git(
        repository,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.com",
        "commit",
        "-am",
        "add module",
    )
    destination = tmp_path / "completed"
    git(repository, "worktree", "add", "-b", "completed", str(destination))
    git(
        destination, "-c", "protocol.file.allow=always", "submodule", "update", "--init"
    )
    listing = make(repository, "worktree-list").stdout
    result = make(repository, "worktree-remove", WORKTREE=destination)
    assert result.returncode != 0
    assert (destination / "module/Makefile").is_file()
    assert make(repository, "worktree-list").stdout == listing
    assert "refs/heads/completed" in git(repository, "show-ref", "--heads")


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
