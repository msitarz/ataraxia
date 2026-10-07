# SPDX-License-Identifier: Apache-2.0
"""Observe process scratch isolation through the real Make boundary."""

from pathlib import Path
import shutil

import pytest

from test.make.support import ROOT
from test.make.worktree_support import creation_repository, files_under


@pytest.mark.covers(
    work="doc/feat/testing-conformance/make/scratch-isolation/README.md", ac="AC-1"
)
def test_make_process_caches_preserve_repository_snapshot(tmp_path: Path) -> None:
    """AC-1: Given a complete repository snapshot before execution and
    process home/scratch outside that repository, writes during a real Make
    action preserve repository files including similarly named legitimate data,
    refs and worktree registrations; the regression detects the old arrangement
    and removal/pruning retain their promises.

    This case covers cache writes and complete repository/state preservation;
    existing removal/pruning cases cover their command-specific promises.
    """
    # Given
    repository = creation_repository(tmp_path / "repository")
    directory = repository.sandbox.directory
    shutil.copyfile(ROOT / "test/make/fixtures/uv_scratch.py", directory / "bin/uv")
    (directory / "home").mkdir(exist_ok=True)
    (directory / "tmp").mkdir(exist_ok=True)
    (directory / "home/cache").write_text("repository home data\n")
    (directory / "tmp/xcrun_db").write_text("repository scratch data\n")
    files, state = files_under(directory), repository.state()

    # When
    result = repository.sandbox.run("format-check", "ARGS=Makefile")

    # Then
    assert result.exit_code == 0, result.output
    assert files_under(directory) == files
    assert repository.state() == state
    home = Path(repository.sandbox.environment["HOME"])
    scratch = Path(repository.sandbox.environment["TMPDIR"])
    assert not home.is_relative_to(directory)
    assert not scratch.is_relative_to(directory)
    assert home.is_relative_to(tmp_path)
    assert scratch.is_relative_to(tmp_path)
    assert (home / "cache").read_text() == "process home cache\n"
    assert (scratch / "xcrun_db").read_text() == "process scratch cache\n"
    assert (directory / "home/cache").read_text() == "repository home data\n"
    assert (directory / "tmp/xcrun_db").read_text() == "repository scratch data\n"
