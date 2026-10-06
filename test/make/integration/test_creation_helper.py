# SPDX-License-Identifier: Apache-2.0
"""Prove the disposable repository/setup helper through real Make and Git."""

from pathlib import Path

import pytest

from test.make.worktree_support import creation_repository


@pytest.mark.covers(
    work="doc/feat/testing-conformance/make/worktree-creation/helper/README.md",
    ac="AC-1",
)
def test_real_make_creates_a_worktree_with_destination_local_setup(
    tmp_path: Path,
) -> None:
    """AC-1: Given a disposable committed repository and usable cache, real
    Make/Git create a branch worktree; fixture setup creates its local environment
    and records destination-local cache/project paths and offline flags.
    """
    # Given
    repository = creation_repository(tmp_path / "source")
    cache = repository.sandbox.directory / ".cache/uv"
    cache.mkdir(parents=True)
    (cache / "ready").write_text("usable cache")
    destination = tmp_path / "created"
    before = repository.state()
    head = repository.git("rev-parse", "master").stdout.strip()

    # When
    result = repository.sandbox.run(
        "worktree-create", f"WORKTREE={destination}", "BRANCH=work/smoke"
    )

    # Then
    assert result.exit_code == 0, result.output
    assert (destination / ".venv").is_dir()
    assert (destination / ".cache/uv/ready").read_text() == "usable cache"
    assert tuple(call.argv for call in result.calls) == (
        ("sync", "--locked", "--group", "dev"),
        ("sync", "--locked", "--group", "dev", "--check", "--offline"),
    )
    assert tuple(call.environment for call in result.calls) == (
        {
            "UV_CACHE_DIR": str(destination / ".cache/uv"),
            "PREK_HOME": str(destination / ".cache/prek"),
            "UV_PROJECT_ENVIRONMENT": str(destination / ".venv"),
            "VIRTUAL_ENV": None,
            "UV_OFFLINE": "true",
            "UV_NO_SYNC": "false",
        },
        {
            "UV_CACHE_DIR": str(destination / ".cache/uv"),
            "PREK_HOME": str(destination / ".cache/prek"),
            "UV_PROJECT_ENVIRONMENT": str(destination / ".venv"),
            "VIRTUAL_ENV": None,
            "UV_OFFLINE": "true",
            "UV_NO_SYNC": "true",
        },
    )
    after = repository.state()
    assert after.refs == before.refs + before.refs.replace(
        "refs/heads/master", "refs/heads/work/smoke"
    )
    assert after.registrations == before.registrations + (
        f"worktree {destination}\nHEAD {head}\nbranch refs/heads/work/smoke\n\n"
    )
