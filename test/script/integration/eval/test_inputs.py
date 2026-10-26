# SPDX-License-Identifier: Apache-2.0
"""Read-only Git and filesystem behavior for evaluation input freezing."""

from collections.abc import Mapping, Sequence
from hashlib import sha256
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

import pytest

from script.eval import inputs as inputs_module
from script.eval.inputs import GitCommandError, GitRepositoryReader
from script.eval.model import DirectoryOption, HarnessConfig, SeparatorOption


def make_repository(path: Path) -> Path:
    """Create a disposable repository with a configured commit identity."""
    path.mkdir()
    git(path, "init", "-b", "master")
    git(path, "config", "user.email", "tests@example.invalid")
    git(path, "config", "user.name", "Input tests")
    return path


def git_test_environment() -> dict[str, str]:
    """Isolate fixture Git commands from ambient config, hooks, and variables."""
    environment = os.environ.copy()
    for name in tuple(environment):
        if name.startswith("GIT_"):
            environment.pop(name)
    environment.update({
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_COUNT": "3",
        "GIT_CONFIG_KEY_0": "core.fsmonitor",
        "GIT_CONFIG_VALUE_0": "false",
        "GIT_CONFIG_KEY_1": "core.hooksPath",
        "GIT_CONFIG_VALUE_1": os.devnull,
        "GIT_CONFIG_KEY_2": "commit.gpgsign",
        "GIT_CONFIG_VALUE_2": "false",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "LC_ALL": "C",
        "LANG": "C",
    })
    return environment


def git(repository: Path, *arguments: str) -> bytes:
    """Run Git in a disposable test repository."""
    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        timeout=10,
        env=git_test_environment(),
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
    contents = files if files is not None else {"tracked.txt": b"tracked\n"}
    for name, content in contents.items():
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


def assert_tree_queries_are_directory_scoped(
    small: tuple[str, ...], large: tuple[str, ...], long_name: str
) -> None:
    """Require selected filename count and length not to expand tree argv."""
    assert len(small) == len(large)
    assert sum(map(len, small)) == sum(map(len, large))
    for query, directory in ((small, "one"), (large, "two")):
        pathspecs = query[query.index("--") + 1 :]
        assert pathspecs == (f":(top,literal){directory}/",)
        assert long_name not in query


def test_fixture_git_commands_ignore_ambient_repository_and_config_redirects(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given
    repository = make_repository(tmp_path / "target")
    other_repository = make_repository(tmp_path / "redirected")
    staged_input = repository / "input.txt"
    staged_input.write_text("fixture data\n", encoding="utf-8")
    external_index = tmp_path / "ambient-index"
    external_config = tmp_path / "ambient-config"
    external_config.write_text("[user]\n\tname = preserved\n", encoding="utf-8")
    original_config = external_config.read_bytes()
    monkeypatch.setenv("GIT_DIR", str(other_repository / ".git"))
    monkeypatch.setenv("GIT_INDEX_FILE", str(external_index))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(external_config))
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.fsmonitor")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "ambient-command-that-does-not-exist")

    # When
    root = git(repository, "rev-parse", "--show-toplevel").rstrip(b"\n")
    git(repository, "add", "--", "input.txt")
    status = git(repository, "status", "--porcelain=v1", "-z")

    # Then
    assert Path(os.fsdecode(root)) == repository
    assert (repository / ".git" / "index").exists()
    assert not external_index.exists()
    assert external_config.read_bytes() == original_config
    assert status == b"A  input.txt\0"


def test_freezing_clears_all_ambient_git_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given
    repository, context = repository_with_context(tmp_path / "target")
    other_repository = make_repository(tmp_path / "redirected")
    external_index = tmp_path / "ambient-index"
    external_config = tmp_path / "ambient-config"
    external_config.write_text("[user]\n\tname = preserved\n", encoding="utf-8")
    original_config = external_config.read_bytes()
    trace_file = tmp_path / "ambient-trace"
    monkeypatch.setenv("GIT_DIR", str(other_repository / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(other_repository))
    monkeypatch.setenv("GIT_INDEX_FILE", str(external_index))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(external_config))
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.fsmonitor")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "ambient-command-that-does-not-exist")
    monkeypatch.setenv("GIT_TRACE", str(trace_file))

    # When
    frozen = GitRepositoryReader().freeze(config(context))

    # Then
    assert frozen.repository_root == repository
    assert frozen.sources[0].repository_path == "context/tracked.txt"
    assert not external_index.exists()
    assert external_config.read_bytes() == original_config
    assert not trace_file.exists()


def test_missing_promisor_blob_is_not_fetched(
    tmp_path: Path,
) -> None:
    # Given
    repository, context = repository_with_context(tmp_path / "repo")
    blob = git(repository, "rev-parse", "HEAD:context/tracked.txt").decode().strip()
    loose_blob = repository / ".git" / "objects" / blob[:2] / blob[2:]
    assert loose_blob.is_file()
    loose_blob.unlink()

    marker = tmp_path / "promisor-fetch-attempted"
    uploadpack = tmp_path / "fake-upload-pack"
    uploadpack.write_text(
        f"#!/bin/sh\n: > {shlex.quote(str(marker))}\nexit 1\n",
        encoding="utf-8",
    )
    uploadpack.chmod(0o755)
    git(repository, "config", "extensions.partialClone", "origin")
    git(repository, "config", "remote.origin.promisor", "true")
    git(repository, "config", "remote.origin.url", "file:///missing-promisor")
    git(repository, "config", "remote.origin.uploadpack", str(uploadpack))

    # When / Then
    with pytest.raises(ValueError, match="invalid blob record"):
        GitRepositoryReader().freeze(config(context))

    assert not marker.exists()


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
        "copy.txt": b"zeta\r\n",
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
        (0, "context one/copy.txt"),
        (0, "context one/empty.txt"),
        (0, "context one/z [x].txt"),
        (2, "second/literal*file.txt"),
        (4, "context one/a\n雪.txt"),
        (4, "context one/copy.txt"),
        (4, "context one/empty.txt"),
        (4, "context one/z [x].txt"),
    ]
    assert [(source.content, source.commit_blob_sha) for source in frozen.sources] == [
        (content, commit_blob_id(repository, head, path))
        for (content, path) in [
            ("alpha ☃\n".encode(), "context one/a\n雪.txt"),
            (b"zeta\r\n", "context one/copy.txt"),
            (b"", "context one/empty.txt"),
            (b"zeta\r\n", "context one/z [x].txt"),
            (b"beta\n", "second/literal*file.txt"),
            ("alpha ☃\n".encode(), "context one/a\n雪.txt"),
            (b"zeta\r\n", "context one/copy.txt"),
            (b"", "context one/empty.txt"),
            (b"zeta\r\n", "context one/z [x].txt"),
        ]
    ]
    assert all(
        source.content_sha256 == sha256(source.content).hexdigest()
        for source in frozen.sources
    ) and next(
        source.commit_blob_sha
        for source in frozen.sources
        if source.repository_path == "context one/copy.txt"
    ) == next(
        source.commit_blob_sha
        for source in frozen.sources
        if source.repository_path == "context one/z [x].txt"
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


def test_instructions_file_may_also_be_selected_as_context(tmp_path: Path) -> None:
    # Given
    repository = make_repository(tmp_path / "repo")
    context = repository / "context"
    context.mkdir()
    (context / "context.txt").write_bytes(b"context\n")
    instructions = context / "instructions.txt"
    instructions.write_bytes(b"same path, separate role\n")
    commit(repository)

    # When
    frozen = GitRepositoryReader().freeze(config(context, instructions=instructions))

    # Then
    assert [(source.repository_path, source.content) for source in frozen.sources] == [
        ("context/context.txt", b"context\n"),
        ("context/instructions.txt", b"same path, separate role\n"),
    ]
    assert frozen.instructions_file is not None
    assert frozen.instructions_file.repository_path == "context/instructions.txt"
    assert frozen.instructions_file.content == b"same path, separate role\n"


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
    repository, context = repository_with_context(
        tmp_path / "repo", {}, extra_files={"tracked.txt": b"keeps HEAD available\n"}
    )

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


def test_freezing_rejects_skip_worktree_edits_hidden_from_status(
    tmp_path: Path,
) -> None:
    # Given
    repository, context = repository_with_context(tmp_path / "repo")
    source = context / "tracked.txt"
    git(repository, "update-index", "--skip-worktree", "--", "context/tracked.txt")
    source.write_bytes(b"hidden edit\n")
    assert worktree_status(repository) == b""

    # When
    with pytest.raises(ValueError, match="differ from the pinned commit blob"):
        GitRepositoryReader().freeze(config(context))

    # Then
    assert source.read_bytes() == b"hidden edit\n"
    assert worktree_status(repository) == b""


def test_freezing_rejects_filter_transformed_worktree_bytes(
    tmp_path: Path,
) -> None:
    # Given
    repository, context = repository_with_context(tmp_path / "repo")
    filter_script = tmp_path / "filter.py"
    shutil.copyfile(
        Path(__file__).parents[2] / "fixtures" / "eval" / "line_ending_filter.py",
        filter_script,
    )
    command = f"{shlex.quote(sys.executable)} {shlex.quote(str(filter_script))}"
    git(repository, "config", "filter.harness.clean", f"{command} clean")
    git(repository, "config", "filter.harness.smudge", f"{command} smudge")
    attributes = repository / ".gitattributes"
    attributes.write_text("*.txt filter=harness\n", encoding="utf-8")
    source = context / "tracked.txt"
    source.write_bytes(b"tracked\r\n")
    git(repository, "add", "context/tracked.txt")
    commit(repository)
    assert worktree_status(repository) == b""

    # When
    with pytest.raises(
        ValueError,
        match="possibly due to filters or line-ending conversion",
    ):
        GitRepositoryReader().freeze(config(context))

    # Then
    assert source.read_bytes() == b"tracked\r\n"


def test_freezing_uses_raw_objects_when_head_has_a_replacement_ref(
    tmp_path: Path,
) -> None:
    # Given
    repository, context = repository_with_context(tmp_path / "repo")
    original_head = git(repository, "rev-parse", "HEAD").decode().strip()
    source = context / "tracked.txt"
    source.write_bytes(b"replacement contents\n")
    replacement_head = commit(repository)
    git(repository, "reset", "--hard", original_head)
    git(repository, "replace", original_head, replacement_head)

    # When
    frozen = GitRepositoryReader().freeze(config(context))

    # Then
    assert frozen.head_commit == original_head
    assert frozen.sources[0].content == b"tracked\n"
    assert frozen.sources[0].commit_blob_sha == commit_blob_id(
        repository, original_head, "context/tracked.txt"
    )


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
    with pytest.raises(ValueError, match="same Git repository"):
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


def test_freezing_reports_filesystem_error_classifying_loop_symlink(
    tmp_path: Path,
) -> None:
    # Given
    repository = make_repository(tmp_path / "repo")
    context = repository / "context"
    context.mkdir()
    (context / "tracked.txt").write_bytes(b"tracked\n")
    loop = context / "self-loop"
    loop.symlink_to(loop.name)
    commit(repository)

    # When / Then
    with pytest.raises(
        ValueError, match=r"cannot classify context entry .*self-loop"
    ) as error:
        GitRepositoryReader().freeze(config(context))

    assert isinstance(error.value.__cause__, OSError)


def test_freezing_accepts_symlinked_directory_and_parent_alias(
    tmp_path: Path,
) -> None:
    # Given
    _, context = repository_with_context(tmp_path / "repo")
    alias = tmp_path / "context-alias"
    alias.symlink_to(context, target_is_directory=True)

    # When
    frozen = GitRepositoryReader().freeze(config(alias / ".." / "context"))

    # Then
    assert frozen.sources[0].repository_path == "context/tracked.txt"


def test_freezing_ignores_symlinked_directory_entries(tmp_path: Path) -> None:
    # Given
    repository, context = repository_with_context(tmp_path / "repo")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "not-selected.txt").write_bytes(b"outside\n")
    (context / "directory-alias").symlink_to(outside, target_is_directory=True)
    commit(repository)

    # When
    frozen = GitRepositoryReader().freeze(config(context))

    # Then
    assert [source.repository_path for source in frozen.sources] == [
        "context/tracked.txt"
    ]


def test_freezing_refuses_symlinked_instructions_file(tmp_path: Path) -> None:
    # Given
    repository, context = repository_with_context(tmp_path / "repo")
    instructions_target = repository / "real-instructions.txt"
    instructions_target.write_bytes(b"instructions\n")
    instructions = repository / "instructions.txt"
    instructions.symlink_to(instructions_target)
    commit(repository)

    # When
    with pytest.raises(ValueError, match="instructions input is not a regular file"):
        GitRepositoryReader().freeze(config(context, instructions=instructions))

    # Then
    assert instructions.is_symlink()


def test_freezing_root_context_in_linked_worktree_skips_git_admin_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given
    repository, _ = repository_with_context(tmp_path / "repo")
    root_file = repository / "root.txt"
    root_file.write_bytes(b"root input\n")
    head = commit(repository)
    linked = tmp_path / "linked"
    git(repository, "worktree", "add", "--detach", str(linked), head)
    monkeypatch.chdir(linked)

    # When
    frozen = GitRepositoryReader().freeze(config(Path(".")))

    # Then
    assert frozen.repository_root == linked
    assert [source.repository_path for source in frozen.sources] == ["root.txt"]


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
    with pytest.raises(ValueError, match="differ from the pinned commit blob"):
        GitRepositoryReader().freeze(config(context))

    # Then
    assert original_read_bytes(source) == b"raced\n"


def test_git_query_count_does_not_grow_with_selected_file_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given
    repository = make_repository(tmp_path / "repo")
    one = repository / "one"
    many = repository / "two"
    one.mkdir()
    many.mkdir()
    (one / "single.txt").write_bytes(b"one\n")
    long_name = f"{'x' * 180}.txt"
    for index in range(12):
        filename = long_name if index == 0 else f"file-{index:02}.txt"
        (many / filename).write_bytes(f"{index}\n".encode())
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
    small_tree_query = next(command for command in commands if "ls-tree" in command)
    commands.clear()
    large = GitRepositoryReader().freeze(config(many))
    large_tree_query = next(command for command in commands if "ls-tree" in command)

    # Then
    assert (len(small.sources), len(large.sources)) == (1, 12)
    assert len(commands) == small_query_count <= 6
    assert (
        all(command[1] == "--no-lazy-fetch" for command in commands)
        and sum("cat-file" in command for command in commands) == 1
    )
    assert_tree_queries_are_directory_scoped(
        small_tree_query, large_tree_query, long_name
    )


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
            env=git_test_environment(),
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


def test_git_nonzero_status_retains_structured_error_details(
    tmp_path: Path,
) -> None:
    # Given
    outside = tmp_path / "not-a-repository"
    outside.mkdir()
    context = outside / "context"
    context.mkdir()

    # When
    with pytest.raises(GitCommandError, match="Git rev-parse failed") as error:
        GitRepositoryReader().freeze(config(context))

    # Then
    assert error.value.returncode != 0
    assert error.value.stderr
    assert error.value.cwd == context
    assert error.value.arguments[0] == "rev-parse"


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
