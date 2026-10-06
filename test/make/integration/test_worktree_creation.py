# SPDX-License-Identifier: Apache-2.0
"""Preserve real Make worktree creation, failure, and refusal effects."""

from dataclasses import dataclass
from pathlib import Path

import pytest

from test.make.support import UvCall
from test.make.worktree_support import CreationRepository, GitState, creation_repository


@dataclass(frozen=True)
class CreationCase:
    """Disposable creation input and pre-action Git observations."""

    repository: CreationRepository
    destination: Path
    before: GitState
    head: str


def arrange_case(tmp_path: Path, name: str) -> CreationCase:
    """Arrange one committed source and independently captured starting state."""
    repository = creation_repository(tmp_path / "source")
    return CreationCase(
        repository,
        tmp_path / name,
        repository.state(),
        repository.git("rev-parse", "master").stdout.strip(),
    )


def write_cache(
    repository: CreationRepository, files: tuple[tuple[str, str], ...]
) -> None:
    """Write the complete named source cache arrangement."""
    for name, content in files:
        path = repository.sandbox.directory / ".cache" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


def cache_files(directory: Path) -> dict[str, bytes]:
    """Observe complete file contents below the relevant cache directory."""
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in directory.rglob("*")
        if path.is_file()
    }


def created_state(case: CreationCase, branch: str) -> GitState:
    """Describe the expected added branch and registration from pre-action HEAD."""
    return GitState(
        case.before.refs + f"{case.head} refs/heads/{branch}\n",
        case.before.registrations + f"worktree {case.destination}\nHEAD {case.head}\n"
        f"branch refs/heads/{branch}\n\n",
    )


def setup_calls(destination: Path) -> tuple[UvCall, ...]:
    """Independent literal expectations for the two setup phases."""
    environment = {
        "UV_CACHE_DIR": str(destination / ".cache/uv"),
        "PREK_HOME": str(destination / ".cache/prek"),
        "UV_PROJECT_ENVIRONMENT": str(destination / ".venv"),
        "VIRTUAL_ENV": None,
        "UV_OFFLINE": "true",
    }
    return (
        UvCall(
            ("sync", "--locked", "--group", "dev"),
            environment | {"UV_NO_SYNC": "false"},
        ),
        UvCall(
            ("sync", "--locked", "--group", "dev", "--check", "--offline"),
            environment | {"UV_NO_SYNC": "true"},
        ),
    )


@pytest.mark.covers(
    work="doc/feat/testing-conformance/make/worktree-creation/cases/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/workspace-preparation/README.md",
    ac="AC-1",
)
def test_creation_copies_cache_and_overrides_parent_environment(tmp_path: Path) -> None:
    """AC-1: Given usable, missing, partial, or verification-failing setup,
    creation succeeds with independent destination caches/environment or fails
    with the recoverable worktree retained; hostile input never executes commands.

    Workspace AC-1: A new worktree gets its own cache and verified environment.
    This case covers cache/routing and literal hostile input.
    Fake setup does not prove real dependency installation or environment validity.
    """
    # Given
    case = arrange_case(tmp_path, "agent's worktree;touch PWNED")
    source = case.repository.sandbox.directory
    write_cache(case.repository, (("uv/ready", "cached"), ("prek/example", "cached")))
    (source / ".venv").mkdir()
    (source / ".venv/parent-only").write_text("do not copy")
    before_cache = cache_files(source / ".cache")

    # When
    result = case.repository.sandbox.run(
        "worktree-create",
        f"WORKTREE={case.destination}",
        "BRANCH=work/example",
        f"UV_CACHE_DIR={source / 'parent-cache'}",
        f"PREK_HOME={source / 'parent-prek'}",
        f"UV_PROJECT_ENVIRONMENT={source / 'parent-venv'}",
        "UV_NO_SYNC=true",
        environment={"VIRTUAL_ENV": str(source / ".venv")},
    )

    # Then
    assert result.exit_code == 0, result.output
    assert "Worktree ready" in result.stdout
    assert cache_files(case.destination / ".cache") == {
        "uv/ready": b"cached",
        "prek/example": b"cached",
    }
    assert cache_files(source / ".cache") == before_cache
    assert not (source / "PWNED").exists()
    assert not (case.destination / ".venv/parent-only").exists()
    assert (source / ".venv/parent-only").read_text() == "do not copy"
    assert (case.destination / ".venv").is_dir()
    assert result.calls == setup_calls(case.destination)
    assert case.repository.state() == created_state(case, "work/example")


@pytest.mark.parametrize(
    ("files", "expected_cache"),
    [((), {}), ((("uv/partial", "partial"),), {"uv/partial": b"partial"})],
    ids=["absent-cache", "incomplete-cache"],
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/make/worktree-creation/cases/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/workspace-preparation/README.md",
    ac="AC-1",
)
def test_unusable_cache_retains_a_recoverable_worktree(
    tmp_path: Path,
    files: tuple[tuple[str, str], ...],
    expected_cache: dict[str, bytes],
) -> None:
    """AC-1: Given usable, missing, partial, or verification-failing setup,
    creation succeeds with independent destination caches/environment or fails
    with the recoverable worktree retained; hostile input never executes commands.

    Workspace AC-1: A new worktree gets its own cache and verified environment.
    This case covers unusable-cache retained state.
    Fake setup does not prove real dependency installation or environment validity.
    """
    # Given
    case = arrange_case(tmp_path, "failed-worktree")
    write_cache(case.repository, files)

    # When
    result = case.repository.sandbox.run(
        "worktree-create", f"WORKTREE={case.destination}", "BRANCH=work/failed"
    )

    # Then
    assert result.exit_code == 2, result.output
    assert case.destination.is_dir()
    assert "worktree retained" in result.stderr
    assert "make ci-setup UV_OFFLINE=true" in result.stderr
    assert "Error 17" in result.stderr
    assert not (case.destination / ".venv").exists()
    assert cache_files(case.destination / ".cache") == expected_cache
    assert cache_files(case.repository.sandbox.directory / ".cache") == expected_cache
    assert result.calls == setup_calls(case.destination)[:1]
    assert case.repository.state() == created_state(case, "work/failed")


@pytest.mark.covers(
    work="doc/feat/testing-conformance/make/worktree-creation/cases/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/workspace-preparation/README.md",
    ac="AC-1",
)
def test_failed_verification_retains_the_prepared_worktree(tmp_path: Path) -> None:
    """AC-1: Given usable, missing, partial, or verification-failing setup,
    creation succeeds with independent destination caches/environment or fails
    with the recoverable worktree retained; hostile input never executes commands.

    Workspace AC-1: A new worktree gets its own cache and verified environment.
    This case covers verification-failure retained state.
    Fake setup does not prove real dependency installation or environment validity.
    """
    # Given
    case = arrange_case(tmp_path, "check-failed")
    write_cache(case.repository, (("uv/ready", "cached"),))

    # When
    result = case.repository.sandbox.run(
        "worktree-create",
        f"WORKTREE={case.destination}",
        "BRANCH=work/verify",
        environment={"STUB_SETUP_FAIL_VERIFY": "true"},
    )

    # Then
    assert result.exit_code == 2, result.output
    assert case.destination.is_dir()
    assert (case.destination / ".venv").is_dir()
    assert "Environment check failed" in result.stderr
    assert "worktree retained" in result.stderr
    assert "Error 24" in result.stderr
    assert cache_files(case.destination / ".cache") == {"uv/ready": b"cached"}
    assert cache_files(case.repository.sandbox.directory / ".cache") == {
        "uv/ready": b"cached"
    }
    assert result.calls == setup_calls(case.destination)
    assert case.repository.state() == created_state(case, "work/verify")


@pytest.mark.covers(
    work="doc/feat/testing-conformance/make/worktree-creation/cases/README.md",
    ac="AC-2",
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/workspace-preparation/README.md",
    ac="AC-1",
)
def test_existing_destination_is_preserved_before_setup(tmp_path: Path) -> None:
    """AC-2: Given an existing destination or branch, refusal preserves
    existing files/refs/registrations and creates no unintended worktree.

    Workspace AC-1: A new worktree gets its own cache and verified environment.
    This case covers destination refusal and preserved state.
    Fake setup does not prove real dependency installation or environment validity.
    """
    # Given
    case = arrange_case(tmp_path, "conflict")
    case.destination.mkdir()
    (case.destination / "keep").write_text("preserve")

    # When
    result = case.repository.sandbox.run(
        "worktree-create", f"WORKTREE={case.destination}", "BRANCH=work/example"
    )

    # Then
    assert result.exit_code == 2, result.output
    assert "destination already exists" in result.stderr
    assert cache_files(case.destination) == {"keep": b"preserve"}
    assert result.calls == ()
    assert case.repository.state() == case.before


@pytest.mark.covers(
    work="doc/feat/testing-conformance/make/worktree-creation/cases/README.md",
    ac="AC-2",
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/workspace-preparation/README.md",
    ac="AC-1",
)
def test_existing_branch_is_preserved_without_creating_a_worktree(
    tmp_path: Path,
) -> None:
    """AC-2: Given an existing destination or branch, refusal preserves
    existing files/refs/registrations and creates no unintended worktree.

    Workspace AC-1: A new worktree gets its own cache and verified environment.
    This case covers branch refusal and preserved state.
    Fake setup does not prove real dependency installation or environment validity.
    """
    # Given
    case = arrange_case(tmp_path, "conflict")
    case.repository.git("branch", "work/existing")
    before = case.repository.state()

    # When
    result = case.repository.sandbox.run(
        "worktree-create", f"WORKTREE={case.destination}", "BRANCH=work/existing"
    )

    # Then
    assert result.exit_code == 2, result.output
    assert "Branch already exists" in result.stderr
    assert not case.destination.exists()
    assert result.calls == ()
    assert case.repository.state() == before
