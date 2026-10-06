# SPDX-License-Identifier: Apache-2.0
"""Exercise real Git removal and refusal effects through isolated Make."""

from dataclasses import dataclass
from pathlib import Path

import pytest

from test.make.worktree_support import CreationRepository, GitState, creation_repository


def files_under(directory: Path) -> dict[str, bytes]:
    """Snapshot relevant files including untracked data, excluding Git internals."""
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in directory.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(directory).parts
    }


@dataclass(frozen=True)
class RefusalCase:
    """Complete unsafe arrangement and pre-action observations."""

    repository: CreationRepository
    destination: Path
    reason: str
    before: GitState
    files: dict[str, bytes]


@pytest.fixture
def unsafe_case(tmp_path: Path, request: pytest.FixtureRequest) -> RefusalCase:
    """Prepare each unsafe input outside the test's action and assertions."""
    condition: object = request.param
    if not isinstance(condition, str):
        raise ValueError("unsafe condition must be a string")
    repository = creation_repository(tmp_path / "repo")
    destination = (
        repository.sandbox.directory if condition == "main" else tmp_path / "completed"
    )
    if condition != "main":
        repository.git("worktree", "add", "-b", "completed", str(destination))
    match condition:
        case "main":
            pass
        case "dirty":
            with (destination / "Makefile").open("a") as stream:
                stream.write("# undelivered\n")
        case "untracked":
            (destination / "keep").write_text("undelivered")
        case "locked":
            repository.git("worktree", "lock", str(destination))
    reasons = {
        "main": "is a main working tree",
        "dirty": "contains modified or untracked files",
        "untracked": "contains modified or untracked files",
        "locked": "cannot remove a locked working tree",
    }
    return RefusalCase(
        repository,
        destination,
        reasons[condition],
        repository.state(),
        files_under(destination),
    )


@pytest.mark.covers(
    work="doc/feat/testing-conformance/make/worktree-cleanup/removal/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/worktree-cleanup/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/worktree-cleanup/README.md",
    ac="AC-2",
)
def test_clean_literal_removal_retains_refs_and_unrelated_worktree(
    tmp_path: Path,
) -> None:
    """AC-1: Given an eligible clean worktree with a hostile literal path,
    removal deletes only that worktree while retaining its branch and unrelated
    worktree; caller expressions never execute, and help lists cleanup targets.

    Cleanup AC-1/AC-2: Clean removal is literal and retains branches and other
    worktrees.
    This case covers literal clean removal, listing, and retained state.
    """
    # Given
    repository = creation_repository(tmp_path / "repo")
    destination = tmp_path / "agent's tree;$(shell touch PWNED)`touch PWNED`$HOME"
    unrelated = tmp_path / "active"
    repository.git("worktree", "add", "-b", "completed", str(destination))
    repository.git("worktree", "add", "-b", "active", str(unrelated))
    before = repository.state()
    unrelated_files = files_under(unrelated)
    head = repository.git("rev-parse", "completed").stdout.strip()

    # When
    result = repository.sandbox.run("worktree-remove", f"WORKTREE={destination}")
    listing = repository.sandbox.run("worktree-list")

    # Then
    assert result.exit_code == 0, result.output
    assert listing.exit_code == 0, listing.output
    assert not destination.exists()
    assert not (repository.sandbox.directory / "PWNED").exists()
    assert unrelated.is_dir()
    assert files_under(unrelated) == unrelated_files
    assert repository.state() == GitState(
        before.refs,
        before.registrations.replace(
            f"worktree {destination}\nHEAD {head}\nbranch refs/heads/completed\n\n", ""
        ),
    )
    assert str(destination) not in listing.stdout
    assert str(unrelated) in listing.stdout


@pytest.mark.covers(
    work="doc/feat/testing-conformance/make/worktree-cleanup/removal/README.md",
    ac="AC-1",
)
def test_help_lists_all_worktree_cleanup_targets(tmp_path: Path) -> None:
    """AC-1: Given an eligible clean worktree with a hostile literal path,
    removal deletes only that worktree while retaining its branch and unrelated
    worktree; caller expressions never execute, and help lists cleanup targets.


    This case covers independent help discoverability.
    """
    # Given
    repository = creation_repository(tmp_path / "repo")

    # When
    result = repository.sandbox.run("help")

    # Then
    assert result.exit_code == 0, result.output
    assert all(
        f"make {target} " in result.stdout
        for target in (
            "worktree-list",
            "worktree-remove",
            "worktree-prune-preview",
            "worktree-prune",
        )
    )


@pytest.mark.parametrize(
    "unsafe_case",
    ["main", "dirty", "untracked", "locked"],
    indirect=True,
    ids=["main", "dirty", "untracked", "locked"],
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/make/worktree-cleanup/removal/README.md",
    ac="AC-2",
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/worktree-cleanup/README.md",
    ac="AC-2",
)
def test_unsafe_removal_preserves_complete_relevant_state(
    unsafe_case: RefusalCase,
) -> None:
    """AC-2: Given missing input, an unknown worktree, or an unsafe main,
    dirty, untracked, locked, or submodule worktree, refusal preserves required
    files, refs, and registrations and reports the precise reason.

    Cleanup AC-2: Git refusal preserves main, dirty, untracked, and locked worktrees.
    This case covers main/dirty/untracked/locked refusal.
    """
    # Given: the fixture supplies complete pre-action state and expected reason.

    # When
    result = unsafe_case.repository.sandbox.run(
        "worktree-remove", f"WORKTREE={unsafe_case.destination}"
    )

    # Then
    assert result.exit_code == 2, result.output
    assert unsafe_case.reason in result.stderr
    assert files_under(unsafe_case.destination) == unsafe_case.files
    assert unsafe_case.repository.state() == unsafe_case.before


@pytest.mark.covers(
    work="doc/feat/testing-conformance/make/worktree-cleanup/removal/README.md",
    ac="AC-2",
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/worktree-cleanup/README.md",
    ac="AC-2",
)
def test_missing_removal_input_preserves_repository_state(tmp_path: Path) -> None:
    """AC-2: Given missing input, an unknown worktree, or an unsafe main,
    dirty, untracked, locked, or submodule worktree, refusal preserves required
    files, refs, and registrations and reports the precise reason.

    Cleanup AC-2: Missing selection or expiry fails without changing registrations.
    This case covers missing removal selector refusal.
    """
    # Given
    repository = creation_repository(tmp_path / "repo")
    before = repository.state()
    files = files_under(repository.sandbox.directory)

    # When
    result = repository.sandbox.run("worktree-remove")

    # Then
    assert result.exit_code == 2, result.output
    assert "Usage: make worktree-remove WORKTREE=/path" in result.stderr
    assert repository.state() == before
    assert files_under(repository.sandbox.directory) == files


@pytest.mark.covers(
    work="doc/feat/testing-conformance/make/worktree-cleanup/removal/README.md",
    ac="AC-2",
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/worktree-cleanup/README.md",
    ac="AC-2",
)
def test_unknown_worktree_refusal_preserves_files_and_repository(
    tmp_path: Path,
) -> None:
    """AC-2: Given missing input, an unknown worktree, or an unsafe main,
    dirty, untracked, locked, or submodule worktree, refusal preserves required
    files, refs, and registrations and reports the precise reason.

    Cleanup AC-2: An unsupported removal selection fails without filesystem fallback.
    This case covers unknown selection refusal without filesystem fallback.
    """
    # Given
    repository = creation_repository(tmp_path / "repo")
    destination = tmp_path / "unregistered"
    destination.mkdir()
    (destination / "keep").write_text("preserve")
    before = repository.state()
    files = files_under(destination)

    # When
    result = repository.sandbox.run("worktree-remove", f"WORKTREE={destination}")

    # Then
    assert result.exit_code == 2, result.output
    assert "is not a working tree" in result.stderr
    assert files_under(destination) == files
    assert repository.state() == before


@pytest.mark.covers(
    work="doc/feat/testing-conformance/make/worktree-cleanup/removal/README.md",
    ac="AC-2",
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/worktree-cleanup/README.md",
    ac="AC-2",
)
def test_populated_submodule_refusal_preserves_complete_worktree_state(
    tmp_path: Path,
) -> None:
    """AC-2: Given missing input, an unknown worktree, or an unsafe main,
    dirty, untracked, locked, or submodule worktree, refusal preserves required
    files, refs, and registrations and reports the precise reason.

    Cleanup AC-2: Populated submodules retain Git's unsupported-removal refusal.
    This case covers populated submodule refusal.
    """
    # Given
    repository = creation_repository(tmp_path / "repo")
    module = tmp_path / "module"
    repository.git("clone", str(repository.sandbox.directory), str(module))
    repository.git(
        "-c", "protocol.file.allow=always", "submodule", "add", str(module), "module"
    )
    repository.git(
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.com",
        "commit",
        "-am",
        "add module",
    )
    destination = tmp_path / "completed"
    repository.git("worktree", "add", "-b", "completed", str(destination))
    repository.git(
        "-c",
        "protocol.file.allow=always",
        "submodule",
        "update",
        "--init",
        cwd=destination,
    )
    before = repository.state()
    files = files_under(destination)

    # When
    result = repository.sandbox.run("worktree-remove", f"WORKTREE={destination}")

    # Then
    assert result.exit_code == 2, result.output
    assert "containing submodules cannot" in result.stderr
    assert (destination / "module/Makefile").is_file()
    assert files_under(destination) == files
    assert repository.state() == before
