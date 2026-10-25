# SPDX-License-Identifier: Apache-2.0
"""Read-only Git and filesystem behavior for evaluation input freezing."""

from hashlib import sha256
from pathlib import Path
import subprocess
from typing import override

import pytest

from script.eval.inputs import GitRepositoryReader
from script.eval.model import DirectoryOption, HarnessConfig, SeparatorOption


def make_repository(path: Path) -> Path:
    """Create a clean committed repository for input-boundary scenarios."""
    path.mkdir()
    git(path, "init", "-b", "master")
    git(path, "config", "user.email", "tests@example.invalid")
    git(path, "config", "user.name", "Input tests")
    return path


def git(repository: Path, *arguments: str) -> bytes:
    """Run Git in a disposable test repository."""
    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        timeout=10,
    )
    return result.stdout


def commit(repository: Path) -> str:
    """Commit fixture contents and return the resulting HEAD."""
    git(repository, "add", "--all")
    git(repository, "commit", "-m", "fixture")
    return git(repository, "rev-parse", "HEAD").decode().strip()


def add_nested_repository(repository: Path) -> Path:
    """Add a committed embedded repository as a superproject gitlink."""
    nested = make_repository(repository / "nested")
    context = nested / "context"
    context.mkdir()
    (context / "file.txt").write_bytes(b"foreign\n")
    commit(nested)
    git(repository, "add", "nested")
    commit(repository)
    return context


def config(*directories: Path, instructions: Path | None = None) -> HarnessConfig:
    """Build the minimum valid harness config for freezer integration tests."""
    options = tuple(
        option
        for index, directory in enumerate(directories)
        for option in (
            DirectoryOption(position=index * 2, path=directory),
            *((SeparatorOption(position=index * 2 + 1, value="\n"),) if index else ()),
        )
    )
    return HarnessConfig(
        ordered_options=options,
        models=("model-a",),
        efforts=("low",),
        concurrency=1,
        output_directory=None,
        dry_run=True,
        timeout_seconds=1.0,
        cleanup_timeout_seconds=1.0,
        grace_seconds=0.0,
        output_limit_bytes=0,
        instructions_file_path=instructions,
    )


def test_freezing_preserves_order_repetitions_and_commit_verified_bytes(
    tmp_path: Path,
) -> None:
    # Given
    repository = make_repository(tmp_path / "repo")
    first = repository / "context one"
    second = repository / "second"
    first.mkdir()
    second.mkdir()
    first_files = {"z [x].txt": b"zeta\r\n", "a\n雪.txt": "alpha ☃\n".encode()}
    for name, content in first_files.items():
        (first / name).write_bytes(content)
    nested_directory = first / "nested"
    nested_directory.mkdir()
    (nested_directory / "not-selected.txt").write_bytes(b"not recursive\n")
    (second / "literal*file.txt").write_bytes(b"beta\n")
    instructions = repository / "instructions.txt"
    instructions.write_bytes(b"separate instructions\n")
    head = commit(repository)

    # When
    frozen = GitRepositoryReader().freeze(
        config(first, second, first, instructions=instructions)
    )

    # Then
    assert frozen.repository_root == repository
    assert frozen.head_commit == head
    assert [
        (source.directory_position, source.repository_path) for source in frozen.sources
    ] == [
        (0, "context one/a\n雪.txt"),
        (0, "context one/z [x].txt"),
        (2, "second/literal*file.txt"),
        (4, "context one/a\n雪.txt"),
        (4, "context one/z [x].txt"),
    ]
    assert [source.content for source in frozen.sources] == [
        "alpha ☃\n".encode(),
        b"zeta\r\n",
        b"beta\n",
        "alpha ☃\n".encode(),
        b"zeta\r\n",
    ]
    assert all(
        source.content_sha256 == sha256(source.content).hexdigest()
        for source in frozen.sources
    )
    assert frozen.instructions_file is not None
    assert frozen.instructions_file.repository_path == "instructions.txt"
    assert frozen.instructions_file.content == b"separate instructions\n"
    assert (
        frozen.instructions_file.content_sha256
        == sha256(b"separate instructions\n").hexdigest()
    )


@pytest.mark.parametrize(
    ("scenario", "reason"),
    [
        ("unstaged", "must be clean"),
        ("staged", "must be clean"),
        ("untracked", "must be clean"),
        ("ignored", "not tracked"),
        ("empty", "is empty"),
        ("bad-utf8", "UTF-8"),
    ],
    ids=[
        "unstaged-change",
        "staged-change",
        "untracked-file",
        "ignored-input",
        "empty-dir",
        "invalid-utf8",
    ],
)
def test_freezing_refuses_dirty_or_unverifiable_inputs(
    tmp_path: Path, scenario: str, reason: str
) -> None:
    # Given
    repository = make_repository(tmp_path / "repo")
    context = repository / "context"
    context.mkdir()
    (context / "tracked.txt").write_bytes(b"baseline\n")
    if scenario == "ignored":
        (repository / ".gitignore").write_text(
            "context/ignored.txt\n", encoding="utf-8"
        )
    if scenario == "empty":
        context = repository / "empty"
        context.mkdir()
    if scenario == "bad-utf8":
        (context / "tracked.txt").write_bytes(b"\xff")
    commit(repository)
    if scenario == "unstaged":
        (context / "tracked.txt").write_bytes(b"changed\n")
    elif scenario == "staged":
        (context / "tracked.txt").write_bytes(b"changed\n")
        git(repository, "add", "context/tracked.txt")
    elif scenario == "untracked":
        (context / "new.txt").write_bytes(b"new\n")
    elif scenario == "ignored":
        (context / "ignored.txt").write_bytes(b"ignored\n")
    # When
    with pytest.raises(ValueError, match=reason):
        GitRepositoryReader().freeze(config(context))

    # Then
    assert not (repository / "outputs").exists()


def test_freezing_refuses_bytes_changed_during_snapshot_read(tmp_path: Path) -> None:
    # Given
    repository = make_repository(tmp_path / "repo")
    context = repository / "context"
    context.mkdir()
    source = context / "tracked.txt"
    source.write_bytes(b"committed\n")
    commit(repository)

    class RacingReader(GitRepositoryReader):
        """Change a source after the clean check to model a concurrent editor."""

        @override
        def _read_utf8(self, path: Path) -> bytes:
            path.write_bytes(b"raced\n")
            return super()._read_utf8(path)

    # When
    with pytest.raises(ValueError, match="differ from commit"):
        RacingReader().freeze(config(context))

    # Then
    assert source.read_bytes() == b"raced\n"


def test_freezing_refuses_symlinks_and_external_or_foreign_inputs(
    tmp_path: Path,
) -> None:
    # Given
    repository = make_repository(tmp_path / "repo")
    context = repository / "context"
    context.mkdir()
    (context / "tracked.txt").write_bytes(b"tracked\n")
    outside = tmp_path / "outside.txt"
    outside.write_bytes(b"outside\n")
    (context / "link.txt").symlink_to(outside)
    commit(repository)
    foreign_context = add_nested_repository(repository)

    # When
    with pytest.raises(ValueError, match="symbolic-link"):
        GitRepositoryReader().freeze(config(context))
    linked_directory = repository / "linked-context"
    linked_directory.symlink_to(context, target_is_directory=True)
    with pytest.raises(ValueError, match="symbolic-link"):
        GitRepositoryReader().freeze(config(linked_directory))
    with pytest.raises(ValueError, match="nested Git repository"):
        GitRepositoryReader().freeze(config(context, foreign_context))
    with pytest.raises(ValueError, match="not a git repository"):
        GitRepositoryReader().freeze(config(outside.parent))

    # Then
    assert (context / "tracked.txt").read_bytes() == b"tracked\n"
