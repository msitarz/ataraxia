# SPDX-License-Identifier: Apache-2.0
"""Read-only Git and filesystem behavior for evaluation input freezing."""

from collections.abc import Mapping, Sequence
from hashlib import sha256
import os
from pathlib import Path
import subprocess

import pytest

from script.eval import inputs as inputs_module
from script.eval.inputs import GitRepositoryReader
from script.eval.model import DirectoryOption, HarnessConfig, SeparatorOption


def make_repository(path: Path) -> Path:
    """Create a disposable repository with a configured commit identity."""
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


def commit_blob_id(repository: Path, head: str, path: str) -> str:
    """Read one pinned commit blob ID using Git's literal pathspec support."""
    record = git(
        repository,
        "ls-tree",
        "-r",
        "-z",
        "--full-tree",
        head,
        "--",
        f":(literal){path}",
    ).split(b"\0", 1)[0]
    metadata, actual_path = record.split(b"\t", 1)
    assert os.fsdecode(actual_path) == path
    return metadata.decode("ascii").split()[2]


def repository_with_context(
    path: Path,
    files: Mapping[str, bytes] | None = None,
    *,
    extra_files: Mapping[str, bytes] | None = None,
) -> tuple[Path, Path]:
    """Create a committed repository with one context and optional other files."""
    repository = make_repository(path)
    context = repository / "context"
    context.mkdir()
    for name, content in (files or {"tracked.txt": b"tracked\n"}).items():
        target = context / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    for name, content in (extra_files or {}).items():
        target = repository / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    commit(repository)
    return repository, context


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
            *((SeparatorOption(position=index * 2 - 1, value="\n"),) if index else ()),
            DirectoryOption(position=index * 2, path=directory),
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


def worktree_status(repository: Path, *, include_submodules: bool = False) -> bytes:
    """Return complete staged, unstaged, and untracked status bytes."""
    arguments = ["status", "--porcelain=v1", "-z", "--untracked-files=all"]
    if include_submodules:
        arguments.append("--ignore-submodules=none")
    return git(repository, *arguments)


def test_freezing_preserves_order_repetitions_and_commit_verified_bytes(
    tmp_path: Path,
) -> None:
    # Given
    repository = make_repository(tmp_path / "repo")
    first = repository / "context one"
    second = repository / "second"
    first.mkdir()
    second.mkdir()
    first_files = {
        "z [x].txt": b"zeta\r\n",
        "a\n雪.txt": "alpha ☃\n".encode(),
        "empty.txt": b"",
    }
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
        (0, "context one/empty.txt"),
        (0, "context one/z [x].txt"),
        (2, "second/literal*file.txt"),
        (4, "context one/a\n雪.txt"),
        (4, "context one/empty.txt"),
        (4, "context one/z [x].txt"),
    ]
    assert [(source.content, source.commit_blob_sha) for source in frozen.sources] == [
        (content, commit_blob_id(repository, head, path))
        for (content, path) in [
            ("alpha ☃\n".encode(), "context one/a\n雪.txt"),
            (b"", "context one/empty.txt"),
            (b"zeta\r\n", "context one/z [x].txt"),
            (b"beta\n", "second/literal*file.txt"),
            ("alpha ☃\n".encode(), "context one/a\n雪.txt"),
            (b"", "context one/empty.txt"),
            (b"zeta\r\n", "context one/z [x].txt"),
        ]
    ]
    assert all(
        source.content_sha256 == sha256(source.content).hexdigest()
        for source in frozen.sources
    )
    assert frozen.instructions_file is not None
    assert frozen.instructions_file.repository_path == "instructions.txt"
    assert frozen.instructions_file.content == b"separate instructions\n"
    assert frozen.instructions_file.commit_blob_sha == commit_blob_id(
        repository, head, "instructions.txt"
    )
    assert (
        frozen.instructions_file.content_sha256
        == sha256(b"separate instructions\n").hexdigest()
    )


def test_freezing_accepts_empty_instructions_file(tmp_path: Path) -> None:
    # Given
    repository, context = repository_with_context(tmp_path / "repo")
    instructions = repository / "empty-instructions.txt"
    instructions.write_bytes(b"")
    commit(repository)

    # When
    frozen = GitRepositoryReader().freeze(config(context, instructions=instructions))

    # Then
    assert frozen.instructions_file is not None
    assert frozen.instructions_file.content == b""
    assert frozen.instructions_file.content_sha256 == sha256(b"").hexdigest()


def test_freezing_refuses_a_dirty_unstaged_input(tmp_path: Path) -> None:
    # Given
    repository, context = repository_with_context(tmp_path / "repo")
    source = context / "tracked.txt"
    source.write_bytes(b"changed\n")
    before = worktree_status(repository)

    # When
    with pytest.raises(ValueError, match="must be clean"):
        GitRepositoryReader().freeze(config(context))

    # Then
    assert worktree_status(repository) == before


def test_freezing_refuses_a_staged_input(tmp_path: Path) -> None:
    # Given
    repository, context = repository_with_context(tmp_path / "repo")
    source = context / "tracked.txt"
    source.write_bytes(b"changed\n")
    git(repository, "add", "context/tracked.txt")
    before = worktree_status(repository)

    # When
    with pytest.raises(ValueError, match="must be clean"):
        GitRepositoryReader().freeze(config(context))

    # Then
    assert worktree_status(repository) == before


def test_freezing_refuses_an_untracked_input(tmp_path: Path) -> None:
    # Given
    repository, context = repository_with_context(tmp_path / "repo")
    (context / "new.txt").write_bytes(b"new\n")
    before = worktree_status(repository)

    # When
    with pytest.raises(ValueError, match="must be clean"):
        GitRepositoryReader().freeze(config(context))

    # Then
    assert worktree_status(repository) == before


def test_freezing_checks_dirty_files_outside_selected_directories(
    tmp_path: Path,
) -> None:
    # Given
    repository, context = repository_with_context(
        tmp_path / "repo", extra_files={"elsewhere.txt": b"outside context\n"}
    )
    outside = repository / "elsewhere.txt"
    outside.write_bytes(b"dirty outside context\n")
    before = worktree_status(repository)

    # When
    with pytest.raises(ValueError, match="must be clean"):
        GitRepositoryReader().freeze(config(context))

    # Then
    assert worktree_status(repository) == before


def test_freezing_refuses_an_ignored_context_file(tmp_path: Path) -> None:
    # Given
    repository = make_repository(tmp_path / "repo")
    context = repository / "context"
    context.mkdir()
    (context / "tracked.txt").write_bytes(b"tracked\n")
    (repository / ".gitignore").write_text("context/ignored.txt\n", encoding="utf-8")
    commit(repository)
    ignored = context / "ignored.txt"
    ignored.write_bytes(b"ignored\n")
    before = worktree_status(repository)

    # When
    with pytest.raises(ValueError, match="not tracked"):
        GitRepositoryReader().freeze(config(context))

    # Then
    assert worktree_status(repository) == before
    assert ignored.read_bytes() == b"ignored\n"


def test_freezing_refuses_an_empty_context_directory(tmp_path: Path) -> None:
    # Given
    repository = make_repository(tmp_path / "repo")
    context = repository / "empty"
    context.mkdir()
    (repository / "tracked.txt").write_bytes(b"keeps HEAD available\n")
    commit(repository)

    # When
    with pytest.raises(ValueError, match="context directory is empty"):
        GitRepositoryReader().freeze(config(context))

    # Then
    assert worktree_status(repository) == b""


def test_freezing_refuses_invalid_utf8_context_bytes(tmp_path: Path) -> None:
    # Given
    repository, context = repository_with_context(
        tmp_path / "repo", {"invalid.txt": b"\xff"}
    )

    # When
    with pytest.raises(ValueError, match="not valid UTF-8"):
        GitRepositoryReader().freeze(config(context))

    # Then
    assert worktree_status(repository) == b""


def test_freezing_refuses_an_ignored_instructions_file(tmp_path: Path) -> None:
    # Given
    repository, context = repository_with_context(tmp_path / "repo")
    (repository / ".gitignore").write_text(
        "ignored-instructions.txt\n", encoding="utf-8"
    )
    commit(repository)
    instructions = repository / "ignored-instructions.txt"
    instructions.write_bytes(b"private instructions\n")
    before = worktree_status(repository)

    # When
    with pytest.raises(ValueError, match="instructions file is not tracked"):
        GitRepositoryReader().freeze(config(context, instructions=instructions))

    # Then
    assert worktree_status(repository) == before


def test_freezing_refuses_invalid_utf8_instructions(tmp_path: Path) -> None:
    # Given
    repository, context = repository_with_context(tmp_path / "repo")
    instructions = repository / "instructions.bin"
    instructions.write_bytes(b"\xff")
    commit(repository)

    # When
    with pytest.raises(ValueError, match="not valid UTF-8"):
        GitRepositoryReader().freeze(config(context, instructions=instructions))

    # Then
    assert worktree_status(repository) == b""


def test_freezing_refuses_external_instructions_path(tmp_path: Path) -> None:
    # Given
    repository, context = repository_with_context(tmp_path / "repo")
    instructions = tmp_path / "outside-instructions.txt"
    instructions.write_bytes(b"outside\n")

    # When
    with pytest.raises(ValueError, match="not a git repository"):
        GitRepositoryReader().freeze(config(context, instructions=instructions))

    # Then
    assert worktree_status(repository) == b""


def test_freezing_refuses_a_missing_context_path(tmp_path: Path) -> None:
    # Given
    repository, _ = repository_with_context(tmp_path / "repo")
    missing = repository / "missing"

    # When
    with pytest.raises(ValueError, match="must exist inside repository") as error:
        GitRepositoryReader().freeze(config(missing))

    # Then
    assert isinstance(error.value.__cause__, FileNotFoundError)


def test_freezing_refuses_a_repository_without_head(tmp_path: Path) -> None:
    # Given
    repository = make_repository(tmp_path / "repo")
    context = repository / "context"
    context.mkdir()
    (context / "untracked.txt").write_bytes(b"no HEAD\n")

    # When
    with pytest.raises(ValueError, match="Git repository has no HEAD") as error:
        GitRepositoryReader().freeze(config(context))

    # Then
    assert isinstance(error.value.__cause__, ValueError)


def test_freezing_refuses_two_independent_repositories(tmp_path: Path) -> None:
    # Given
    _, first_context = repository_with_context(tmp_path / "first")
    _, second_context = repository_with_context(tmp_path / "second")

    # When
    with pytest.raises(ValueError, match="same Git repository"):
        GitRepositoryReader().freeze(config(first_context, second_context))

    # Then
    assert (first_context / "tracked.txt").read_bytes() == b"tracked\n"
    assert (second_context / "tracked.txt").read_bytes() == b"tracked\n"


def test_freezing_refuses_nested_submodule_input(tmp_path: Path) -> None:
    # Given
    repository, context = repository_with_context(tmp_path / "repo")
    foreign_context = add_nested_repository(repository)

    # When
    with pytest.raises(ValueError, match="nested Git repository"):
        GitRepositoryReader().freeze(config(context, foreign_context))

    # Then
    assert (foreign_context / "file.txt").read_bytes() == b"foreign\n"


def test_freezing_detects_dirty_submodule_even_when_git_config_ignores_it(
    tmp_path: Path,
) -> None:
    # Given
    repository, context = repository_with_context(tmp_path / "repo")
    nested_context = add_nested_repository(repository)
    nested_file = nested_context / "file.txt"
    nested_file.write_bytes(b"changed foreign contents\n")
    git(repository, "config", "diff.ignoreSubmodules", "all")
    before = worktree_status(repository, include_submodules=True)

    # When
    with pytest.raises(ValueError, match="worktree must be clean"):
        GitRepositoryReader().freeze(config(context))

    # Then
    assert worktree_status(repository, include_submodules=True) == before
    assert nested_file.read_bytes() == b"changed foreign contents\n"


def test_freezing_ignores_inherited_git_pathspec_modes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given
    repository = make_repository(tmp_path / "repo")
    context = repository / "context"
    context.mkdir()
    context_file = context / "literal*file[1].txt"
    context_file.write_bytes(b"context\n")
    instructions = repository / "instructions*[2].txt"
    instructions.write_bytes(b"instructions\n")
    commit(repository)
    monkeypatch.setenv("GIT_LITERAL_PATHSPECS", "1")

    # When
    frozen = GitRepositoryReader().freeze(config(context, instructions=instructions))

    # Then
    assert [(source.repository_path, source.content) for source in frozen.sources] == [
        ("context/literal*file[1].txt", b"context\n")
    ]
    assert frozen.instructions_file is not None
    assert frozen.instructions_file.repository_path == "instructions*[2].txt"
    assert frozen.instructions_file.content == b"instructions\n"


def test_freezing_refuses_symbolic_link_entries(tmp_path: Path) -> None:
    # Given
    repository, context = repository_with_context(tmp_path / "repo")
    outside = tmp_path / "outside.txt"
    outside.write_bytes(b"outside\n")
    link = context / "link.txt"
    link.symlink_to(outside)
    commit(repository)
    before = worktree_status(repository)

    # When
    with pytest.raises(ValueError, match="symbolic-link"):
        GitRepositoryReader().freeze(config(context))

    # Then
    assert link.is_symlink()
    assert worktree_status(repository) == before


def test_freezing_checks_symlink_components_before_dotdot_resolution(
    tmp_path: Path,
) -> None:
    # Given
    repository, context = repository_with_context(tmp_path / "repo")
    ordinary = repository / "ordinary"
    ordinary.mkdir()
    alias = repository / "alias"
    alias.symlink_to(ordinary, target_is_directory=True)
    commit(repository)
    symlink_route = alias / ".." / context.name
    ordinary_route = ordinary / ".." / context.name

    # When
    with pytest.raises(ValueError, match="symbolic-link"):
        GitRepositoryReader().freeze(config(symlink_route))
    frozen = GitRepositoryReader().freeze(config(ordinary_route))

    # Then
    assert frozen.sources[0].repository_path == "context/tracked.txt"


def test_freezing_preserves_repository_root_trailing_spaces_and_newlines(
    tmp_path: Path,
) -> None:
    # Given
    repository, context = repository_with_context(tmp_path / "repo \n")

    # When
    frozen = GitRepositoryReader().freeze(config(context))

    # Then
    assert frozen.repository_root == repository
    assert frozen.sources[0].repository_path == "context/tracked.txt"


def test_freezing_refuses_bytes_changed_during_snapshot_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given
    _, context = repository_with_context(tmp_path / "repo")
    source = context / "tracked.txt"
    original_read_bytes = Path.read_bytes
    changed = False

    def race_on_source(path: Path) -> bytes:
        nonlocal changed
        if path == source and not changed:
            path.write_bytes(b"raced\n")
            changed = True
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", race_on_source)

    # When
    with pytest.raises(ValueError, match="differ from commit"):
        GitRepositoryReader().freeze(config(context))

    # Then
    assert original_read_bytes(source) == b"raced\n"


def test_git_query_count_does_not_grow_with_selected_file_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given
    repository = make_repository(tmp_path / "repo")
    one = repository / "one"
    many = repository / "many"
    one.mkdir()
    many.mkdir()
    (one / "single.txt").write_bytes(b"one\n")
    for index in range(12):
        (many / f"file-{index:02}.txt").write_bytes(f"{index}\n".encode())
    commit(repository)
    original_run = subprocess.run
    commands: list[tuple[str, ...]] = []

    def observe_run(
        arguments: Sequence[str],
        *,
        input: bytes | None = None,
        capture_output: bool = False,
        check: bool = False,
        timeout: float | None = None,
        env: Mapping[str, str] | None = None,
    ) -> subprocess.CompletedProcess[bytes]:
        commands.append(tuple(arguments))
        return original_run(
            arguments,
            input=input,
            capture_output=capture_output,
            check=check,
            timeout=timeout,
            env=dict(env) if env is not None else None,
        )

    monkeypatch.setattr(inputs_module.subprocess, "run", observe_run)

    # When
    small = GitRepositoryReader().freeze(config(one))
    small_query_count = len(commands)
    commands.clear()
    large = GitRepositoryReader().freeze(config(many))

    # Then
    assert len(small.sources) == 1
    assert len(large.sources) == 12
    assert len(commands) == small_query_count
    assert sum(command[3] == "cat-file" for command in commands) == 1


def test_git_missing_executable_preserves_the_os_error_cause(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given
    repository, context = repository_with_context(tmp_path / "repo")
    original_run = subprocess.run
    status_before = worktree_status(repository)

    def missing_git(
        *_args: object, **_kwargs: object
    ) -> subprocess.CompletedProcess[bytes]:
        raise FileNotFoundError("git is unavailable")

    monkeypatch.setattr(inputs_module.subprocess, "run", missing_git)

    # When
    with pytest.raises(ValueError, match="cannot run Git command rev-parse") as error:
        GitRepositoryReader().freeze(config(context))

    # Then
    assert isinstance(error.value.__cause__, FileNotFoundError)
    assert status_before == b""
    assert (
        original_run(
            ["git", "-C", str(repository), "status", "--porcelain=v1", "-z"],
            capture_output=True,
            check=True,
            timeout=10,
        ).stdout
        == status_before
    )


def test_git_timeout_preserves_the_timeout_cause(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given
    _, context = repository_with_context(tmp_path / "repo")

    def timed_out(
        arguments: Sequence[str], *, timeout: float | None = None, **_kwargs: object
    ) -> subprocess.CompletedProcess[bytes]:
        raise subprocess.TimeoutExpired(
            arguments[0], timeout=timeout if timeout is not None else 0.0
        )

    monkeypatch.setattr(inputs_module.subprocess, "run", timed_out)

    # When
    with pytest.raises(ValueError, match="Git command timed out") as error:
        GitRepositoryReader(timeout_seconds=0.5).freeze(config(context))

    # Then
    assert isinstance(error.value.__cause__, subprocess.TimeoutExpired)


def test_git_nonzero_exit_reports_binary_stderr_deterministically(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given
    _, context = repository_with_context(tmp_path / "repo")

    def git_failed(
        arguments: Sequence[str], **_kwargs: object
    ) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(arguments, 128, b"", b"git failed\xff")

    monkeypatch.setattr(inputs_module.subprocess, "run", git_failed)

    # When
    with pytest.raises(ValueError, match=r"Git rev-parse failed.*git failed") as error:
        GitRepositoryReader().freeze(config(context))

    # Then
    assert error.value.__cause__ is None
