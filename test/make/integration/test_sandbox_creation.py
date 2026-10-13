# SPDX-License-Identifier: Apache-2.0
"""Exercise the managed sandbox creation boundary with disposable Git repos."""

import json
from pathlib import Path
import shutil
import stat
import sys

import pytest

from test.make.support import ROOT, MakeResult, MakeSandbox
from test.make.worktree_support import CreationRepository, creation_repository


def sandbox_source(
    directory: Path, *, cache_target: Path | None = None
) -> CreationRepository:
    """Extend the shared disposable Git/Make fixture with sandbox inputs."""
    repository = creation_repository(directory)
    sandbox = repository.sandbox
    shutil.copyfile(
        ROOT / "test/make/fixtures/sandbox_uv_recorder.sh", directory / "bin/uv"
    )
    (directory / "bin/uv").chmod(0o755)
    setup = directory / "bin/make"
    shutil.copyfile(ROOT / "test/make/fixtures/sandbox_setup_recorder.py", setup)
    setup.chmod(0o755)
    (directory / "script").mkdir()
    shutil.copyfile(ROOT / "script/sandbox.py", directory / "script/sandbox.py")
    (directory / "pyproject.toml").write_text('[project]\nname = "fixture-project"\n')
    (directory / "README.md").write_text("fixture\n")
    if cache_target is not None:
        cache_target.mkdir()
        (cache_target / "sentinel").write_text("preserve me\n")
        (directory / ".cache").symlink_to(cache_target, target_is_directory=True)
    repository.git("add", ".")
    repository.git(
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.com",
        "commit",
        "-m",
        "source",
    )
    git = directory / "bin/git"
    shutil.copyfile(ROOT / "test/make/fixtures/sandbox_git_recorder.sh", git)
    git.chmod(0o755)
    sandbox = MakeSandbox(
        directory,
        sandbox.environment
        | {
            "UV_TEST_PYTHON": sys.executable,
            "REAL_GIT_PATH": shutil.which("git") or "git",
            "REAL_MAKE_PATH": shutil.which("make") or "make",
        },
    )
    return CreationRepository(sandbox)


def make_create(
    repository: CreationRepository,
    name: str,
    root: Path | None,
    *,
    extra_environment: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> MakeResult:
    """Run the real Make target through the shared disposable Make runner."""
    arguments = ["sandbox-create", f"NAME={name}"]
    if root is not None:
        arguments.append(f"SANDBOX_ROOT={root}")
    return repository.sandbox.run(*arguments, environment=extra_environment, cwd=cwd)


def assert_prepared_clone(
    repository: CreationRepository, destination: Path, metadata: Path
) -> None:
    """Check clone independence and the exact setup environment at its final path."""
    shallow = repository.git(
        "-C", str(destination), "rev-parse", "--is-shallow-repository"
    )
    assert shallow.stdout.strip() == "true"
    assert repository.git("-C", str(destination), "remote").stdout == ""
    refs = repository.git("-C", str(destination), "show-ref").stdout.splitlines()
    base = json.loads(metadata.read_text())["base"]
    assert refs == [f"{base} refs/heads/work/sandbox-run-1"]
    count = repository.git("-C", str(destination), "rev-list", "--count", "HEAD")
    assert count.stdout.strip() == "1"
    assert not (destination / ".git/objects/info/alternates").exists()
    log = destination / ".sandbox-setup-log.jsonl"
    records = [json.loads(line) for line in log.read_text().splitlines()]
    assert [record["argv"] for record in records] == [["setup"], ["verify-setup"]]
    assert [record["cwd"] for record in records] == [str(destination)] * 2
    expected = {
        "UV_CACHE_DIR": str(destination / ".cache/uv"),
        "PREK_HOME": str(destination / ".cache/prek"),
        "UV_PROJECT_ENVIRONMENT": str(destination / ".venv"),
        "HOME": str(destination / ".home"),
        "TMPDIR": str(destination / ".tmp"),
        "VIRTUAL_ENV": None,
    }
    assert [record["environment"] for record in records] == [expected] * 2
    assert (destination / ".cache/uv").is_dir()
    assert (destination / ".cache/prek").is_dir()


def checkout_conflict_attempt(
    repository: CreationRepository, managed: Path, other: Path
) -> MakeResult:
    """Prepare a second checkout and return its root-ownership attempt."""
    repository.git("clone", "--no-local", str(repository.sandbox.directory), str(other))
    first_owner = make_create(repository, "owned", managed)
    assert first_owner.exit_code == 0, first_owner.output
    return make_create(repository, "conflict", managed, cwd=other)


@pytest.mark.covers(work="doc/feat/evaluation-sandboxes/creation/README.md", ac="AC-1")
def test_make_creates_owned_shallow_clone_and_refuses_unsafe_names(
    tmp_path: Path,
) -> None:
    """AC-1: Create a depth-one owned clone and reject traversal names."""
    # Given
    source = sandbox_source(tmp_path / "source")
    managed = tmp_path / "managed"
    metadata = managed / ".run-1.ataraxia-sandbox.json"
    marker = tmp_path / "shell-injected"

    # When
    result = make_create(source, "run-1", managed)
    before = metadata.read_bytes()
    rejected = make_create(source, "../escape", managed)
    invalid_ref = make_create(source, "bad..name", managed)
    hostile = make_create(source, f"bad; touch {marker}", managed)

    # Then
    destination = managed / "run-1"
    assert result.exit_code == 0, result.output
    assert json.loads(metadata.read_text()) == {
        "common_dir": str((source.sandbox.directory / ".git").resolve()),
        "project": "fixture-project",
        "base": source.git("rev-parse", "master").stdout.strip(),
        "state": "ready",
    }
    assert stat.S_IMODE(metadata.stat().st_mode) == 0o600
    assert_prepared_clone(source, destination, metadata)
    assert rejected.exit_code == 2
    assert invalid_ref.exit_code == 2
    assert hostile.exit_code == 2
    assert not marker.exists()
    assert metadata.read_bytes() == before
    assert not (tmp_path / "escape").exists()
    assert not (managed / "bad..name").exists()
    assert not (managed / ".bad..name.ataraxia-sandbox.json").exists()
    assert not (managed / f"bad; touch {marker}").exists()


@pytest.mark.covers(work="doc/feat/evaluation-sandboxes/creation/README.md", ac="AC-2")
def test_setup_failure_retains_owned_clone_and_diagnostics(tmp_path: Path) -> None:
    """AC-2: Given a setup double failure, creation retains the owned partial clone."""
    # Given
    source = sandbox_source(tmp_path / "source")
    managed = tmp_path / "managed"

    # When
    result = make_create(source, "failed", managed)
    retry = make_create(source, "failed", managed)

    # Then
    destination = managed / "failed"
    assert result.exit_code == 2
    assert "simulated setup failure" in result.stderr
    record = json.loads((managed / ".failed.ataraxia-sandbox.json").read_text())
    assert record["state"] == "failed"
    assert record["failure_stage"] == "setup"
    assert record["failure_status"] == "17"
    assert record["failure_stderr"] == "simulated setup failure\n"
    assert record["failure_stdout"] == ""
    assert "ready_at" not in record
    log = destination / ".sandbox-setup-log.jsonl"
    assert [json.loads(line)["argv"] for line in log.read_text().splitlines()] == [
        ["setup"]
    ]
    assert retry.exit_code == 2
    assert "already exists" in retry.stderr


@pytest.mark.covers(work="doc/feat/evaluation-sandboxes/creation/README.md", ac="AC-2")
def test_clone_failure_retains_status_and_diagnostics(tmp_path: Path) -> None:
    """AC-2: Retain clone failure state and reject a retry of its partial name."""
    # Given
    source = sandbox_source(tmp_path / "source")
    managed = tmp_path / "managed"

    # When
    result = make_create(
        source,
        "clone-failed",
        managed,
        extra_environment={"SANDBOX_GIT_FAIL": "clone"},
    )
    retry = make_create(source, "clone-failed", managed)

    # Then
    metadata = json.loads((managed / ".clone-failed.ataraxia-sandbox.json").read_text())
    assert result.exit_code == 2
    assert metadata["state"] == "failed"
    assert metadata["failure_stage"] == "clone"
    assert metadata["failure_status"] == "23"
    assert metadata["failure_stderr"] == "simulated clone failure\n"
    assert not (managed / "clone-failed" / ".git").exists()
    assert "ready_at" not in metadata
    assert retry.exit_code == 2


@pytest.mark.covers(work="doc/feat/evaluation-sandboxes/creation/README.md", ac="AC-2")
def test_readiness_failure_retains_status_and_setup_artifacts(tmp_path: Path) -> None:
    """AC-2: Retain verify-setup failure state without marking the child ready."""
    # Given
    source = sandbox_source(tmp_path / "source")
    managed = tmp_path / "managed"

    # When
    result = make_create(source, "verify-failed", managed)

    # Then
    metadata = json.loads(
        (managed / ".verify-failed.ataraxia-sandbox.json").read_text()
    )
    assert result.exit_code == 2
    assert metadata["state"] == "failed"
    assert metadata["failure_stage"] == "readiness"
    assert metadata["failure_status"] == "19"
    assert metadata["failure_stderr"] == "simulated readiness failure\n"
    assert [
        json.loads(line)["argv"]
        for line in (managed / "verify-failed" / ".sandbox-setup-log.jsonl")
        .read_text()
        .splitlines()
    ] == [["setup"], ["verify-setup"]]
    assert "ready_at" not in metadata


@pytest.mark.covers(work="doc/feat/evaluation-sandboxes/creation/README.md", ac="AC-1")
def test_native_temp_root_uses_project_name_and_linked_worktrees_share_owner(
    tmp_path: Path,
) -> None:
    """AC-1: Resolve native temp and project identity across linked worktrees."""
    # Given
    source = sandbox_source(tmp_path / "checkout")
    source_path = source.sandbox.directory
    linked = tmp_path / "linked-checkout"
    native_temp = tmp_path / "native-temp"
    native_temp.mkdir(mode=0o700)
    managed = native_temp / "fixture-project" / "sandboxes"

    # When
    result = make_create(
        source, "native", None, extra_environment={"TMPDIR": str(native_temp)}
    )
    source.git("worktree", "add", "--detach", str(linked))
    linked_result = make_create(source, "linked", managed, cwd=linked)

    # Then
    assert result.exit_code == 0, result.output
    assert (managed / "native").is_dir()
    assert (managed / ".native.ataraxia-sandbox.json").is_file()
    assert linked_result.exit_code == 0, linked_result.output
    identity = json.loads((managed / ".linked.ataraxia-sandbox.json").read_text())
    assert identity["common_dir"] == str((source_path / ".git").resolve())


@pytest.mark.covers(work="doc/feat/evaluation-sandboxes/creation/README.md", ac="AC-1")
def test_unsafe_roots_and_dangling_destinations_are_refused(tmp_path: Path) -> None:
    """AC-1: Refuse unsafe roots and dangling destination links."""
    # Given
    source = sandbox_source(tmp_path / "checkout")
    source_path = source.sandbox.directory
    managed = tmp_path / "managed"
    managed.mkdir(mode=0o700)
    unsuitable = tmp_path / "unsuitable-root"
    unsuitable.mkdir(mode=0o755)
    dangling_root = tmp_path / "dangling-root"
    dangling_root.symlink_to(tmp_path / "missing-root")
    dangling = managed / "dangling"
    dangling.symlink_to(tmp_path / "missing")

    # When
    dangling_result = make_create(source, "dangling", managed)
    source_root_result = make_create(
        source, "source-root", source_path.parent / "missing" / ".." / source_path.name
    )
    permissions_result = make_create(source, "permissions", unsuitable)
    symlink_root_result = make_create(source, "root-link", dangling_root)
    fallback_result = make_create(
        source,
        "fallback",
        None,
        extra_environment={"TMPDIR": str(source_path)},
    )

    # Then
    assert (dangling_result.exit_code, dangling.is_symlink()) == (2, True)
    assert source_root_result.exit_code == 2
    assert not (source_path / "source-root").exists()
    assert permissions_result.exit_code == 2
    assert not (unsuitable / "permissions").exists()
    assert symlink_root_result.exit_code == 2
    assert dangling_root.is_symlink()
    assert fallback_result.exit_code == 2
    assert not (source_path / "fallback").exists()


@pytest.mark.covers(work="doc/feat/evaluation-sandboxes/creation/README.md", ac="AC-1")
def test_independent_checkout_cannot_claim_managed_root(tmp_path: Path) -> None:
    """AC-1: Refuse a managed root already owned by another checkout."""
    # Given
    source = sandbox_source(tmp_path / "checkout")
    managed = tmp_path / "managed"

    # When
    result = checkout_conflict_attempt(
        source, managed, tmp_path / "independent-checkout"
    )

    # Then
    assert result.exit_code == 2
    assert "another checkout" in result.stderr
    assert not (managed / "conflict").exists()
    assert not (managed / ".conflict.ataraxia-sandbox.json").exists()


@pytest.mark.covers(work="doc/feat/evaluation-sandboxes/creation/README.md", ac="AC-1")
def test_common_directory_and_unsafe_writable_ancestor_are_refused(
    tmp_path: Path,
) -> None:
    """AC-1: Reject roots inside shared Git metadata and writable ancestors."""
    # Given
    source = sandbox_source(tmp_path / "source")
    linked = tmp_path / "linked-checkout"
    source.git("worktree", "add", "--detach", str(linked))
    common_dir = (
        linked
        / source.git("-C", str(linked), "rev-parse", "--git-common-dir").stdout.strip()
    ).resolve()
    common_root = common_dir / "managed-sandboxes"
    assert common_root not in linked.parents and linked not in common_root.parents
    unsafe_ancestor = tmp_path / "world-writable"
    unsafe_ancestor.mkdir()
    unsafe_ancestor.chmod(0o777)

    # When
    common_result = make_create(source, "common-overlap", common_root, cwd=linked)
    ancestor_result = make_create(
        source, "unsafe-ancestor", unsafe_ancestor / "managed"
    )

    # Then
    assert common_result.exit_code == 2
    assert not common_root.exists()
    assert ancestor_result.exit_code == 2
    assert not (unsafe_ancestor / "managed").exists()


@pytest.mark.covers(work="doc/feat/evaluation-sandboxes/creation/README.md", ac="AC-2")
def test_preexisting_cache_symlink_fails_without_writing_external_target(
    tmp_path: Path,
) -> None:
    """AC-2: Reject a tracked .cache symlink before setup can follow it."""
    # Given
    external_cache = tmp_path / "external-cache"
    source = sandbox_source(tmp_path / "source", cache_target=external_cache)
    managed = tmp_path / "managed"

    # When
    result = make_create(source, "cache-link", managed)

    # Then
    destination = managed / "cache-link"
    metadata = json.loads((managed / ".cache-link.ataraxia-sandbox.json").read_text())
    assert result.exit_code == 2
    assert metadata["state"] == "failed"
    assert metadata["failure_stage"] == "setup"
    assert "pre-existing .cache path" in metadata["failure_stderr"]
    assert "ready_at" not in metadata
    assert (destination / ".cache").is_symlink()
    assert sorted(path.name for path in external_cache.iterdir()) == ["sentinel"]
    assert (external_cache / "sentinel").read_text() == "preserve me\n"
    assert not any((destination / path).exists() for path in (".venv", ".tmp", ".home"))


@pytest.mark.covers(work="doc/feat/evaluation-sandboxes/creation/README.md", ac="AC-2")
def test_changed_master_after_selection_fails_and_retains_clone(
    tmp_path: Path,
) -> None:
    """AC-2: Retain failure artifacts when master advances after base selection."""
    # Given
    source = sandbox_source(tmp_path / "source")
    managed = tmp_path / "managed"

    # When
    result = make_create(
        source,
        "moved-master",
        managed,
        extra_environment={"SANDBOX_ADVANCE_SOURCE": str(source.sandbox.directory)},
    )

    # Then
    destination = managed / "moved-master"
    metadata = json.loads((managed / ".moved-master.ataraxia-sandbox.json").read_text())
    current_master = source.git("rev-parse", "refs/heads/master").stdout.strip()
    cloned_head = source.git("-C", str(destination), "rev-parse", "HEAD").stdout.strip()
    assert result.exit_code == 2
    assert metadata["state"] == "failed"
    assert metadata["failure_stage"] == "readiness"
    assert "clone base changed" in metadata["failure_stderr"]
    assert current_master != metadata["base"]
    assert cloned_head == current_master
    assert (destination / ".git").is_dir()
    assert "ready_at" not in metadata
