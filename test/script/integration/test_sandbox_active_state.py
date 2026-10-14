# SPDX-License-Identifier: Apache-2.0
"""Exercise durable sandbox markers, stable locks, and observational probes."""

import fcntl
import json
import os
from pathlib import Path
import select
import shutil
import stat
import subprocess
import sys

import pytest

from script import sandbox


def managed_root(tmp_path: Path) -> Path:
    """Create a private disposable managed root."""
    root = tmp_path / "managed"
    root.mkdir(mode=0o700)
    return root


def reserve_sandbox(root: Path, name: str) -> str:
    """Create a reserved preparing marker through the shared host API."""
    owner: sandbox.SandboxOwner = {
        "common_dir": str(root / "source.git"),
        "project": "fixture-project",
        "base": "a" * 40,
    }
    with sandbox.locked_sandbox(root, name, None, create=True) as empty:
        scope = sandbox.reserve_destination(empty, owner)
    assert scope.generation is not None
    return scope.generation


def persistent_snapshot(root: Path) -> dict[str, tuple[bytes | None, int, int, int]]:
    """Capture bytes, mode, inode and modification time without Git internals."""
    snapshot = {}
    for path in sorted(root.rglob("*")):
        info = path.lstat()
        content = path.read_bytes() if stat.S_ISREG(info.st_mode) else None
        snapshot[path.relative_to(root).as_posix()] = (
            content,
            stat.S_IMODE(info.st_mode),
            info.st_ino,
            info.st_mtime_ns,
        )
    return snapshot


@pytest.mark.covers(
    work=(
        "doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/"
        "lock-and-marker/README.md"
    ),
    ac="AC-2",
)
def test_marker_updates_are_atomic_and_keep_future_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Preserve extension fields and the old complete record on update failure."""
    # Given
    root = managed_root(tmp_path)
    generation = reserve_sandbox(root, "marker")
    marker = root / ".marker.ataraxia-sandbox.json"
    before = json.loads(marker.read_text())

    # When
    with sandbox.locked_sandbox(root, "marker", generation) as scope:
        scope = sandbox.update_marker(scope, {"future_extension": {"run": 3}})
        extended = marker.read_bytes()
        with pytest.raises(ValueError, match="owned identity"):
            sandbox.update_marker(scope, {"generation": "0" * 32})

        def refuse_replace(source: Path, destination: Path) -> None:
            raise OSError("simulated interrupted replacement")

        monkeypatch.setattr(os, "replace", refuse_replace)
        with pytest.raises(OSError, match="simulated interrupted replacement"):
            sandbox.update_marker(scope, {"state": "ready"})

    # Then
    record = json.loads(marker.read_text())
    assert record == before | {"future_extension": {"run": 3}}
    assert record["state"] == "preparing"
    assert marker.read_bytes() == extended
    assert stat.S_IMODE(marker.stat().st_mode) == 0o600


@pytest.mark.covers(
    work=(
        "doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/"
        "lock-and-marker/README.md"
    ),
    ac="AC-2",
)
def test_failed_preparation_state_cannot_be_rewritten_as_ready(tmp_path: Path) -> None:
    """A terminal failed preparation record cannot regain ready status."""
    # Given
    root = managed_root(tmp_path)
    generation = reserve_sandbox(root, "failed")

    # When
    with sandbox.locked_sandbox(root, "failed", generation) as scope:
        failed = sandbox.update_marker(
            scope,
            {
                "state": "failed",
                "failure_stage": "setup",
                "failure_status": "1",
                "failure_stdout": "",
                "failure_stderr": "failed",
            },
        )
        with pytest.raises(ValueError, match="cannot be reassigned"):
            sandbox.update_marker(failed, {"state": "ready"})

    # Then
    record = json.loads((root / ".failed.ataraxia-sandbox.json").read_text())
    assert record["state"] == "failed"
    assert record["failure_stderr"] == "failed"


@pytest.mark.covers(
    work=(
        "doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/"
        "lock-and-marker/README.md"
    ),
    ac="AC-2",
)
def test_probe_reports_free_and_held_locks_without_persistent_writes(
    tmp_path: Path,
) -> None:
    """Probe inactivity or activity without changing marker, lock, or workspace."""
    # Given
    root = managed_root(tmp_path)
    generation = reserve_sandbox(root, "probe")
    before = persistent_snapshot(root)

    # When
    inactive = sandbox.probe_sandbox(root, "probe", generation)
    after_inactive = persistent_snapshot(root)
    with sandbox.locked_sandbox(root, "probe", generation):
        active = sandbox.probe_sandbox(root, "probe", generation)
        after_active = persistent_snapshot(root)

    # Then
    assert inactive.activity == "inactive"
    assert active.activity == "active"
    assert after_inactive == before
    assert after_active == before


def test_scope_cannot_update_after_context_even_when_descriptor_number_is_reused(
    tmp_path: Path,
) -> None:
    """A closed lease remains revoked after the OS reuses its descriptor."""
    root = managed_root(tmp_path)
    generation = reserve_sandbox(root, "lease")
    with sandbox.locked_sandbox(root, "lease", generation) as scope:
        stale = scope
    with sandbox.locked_sandbox(root, "empty-lease", None, create=True) as empty:
        stale_empty = empty
    replacement = os.open(root / ".lease.ataraxia-sandbox.lock", os.O_RDWR)
    try:
        assert replacement == stale.lease.descriptor
        with pytest.raises(ValueError, match="active lock scope"):
            sandbox.update_marker(stale, {"state": "ready"})
        with pytest.raises(ValueError, match="active lock scope"):
            sandbox.reserve_destination(
                stale_empty,
                {
                    "common_dir": str(root / "repo.git"),
                    "project": "fixture-project",
                    "base": "a" * 40,
                },
            )
    finally:
        os.close(replacement)


@pytest.mark.covers(
    work=(
        "doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/"
        "lock-and-marker/README.md"
    ),
    ac="AC-2",
)
@pytest.mark.parametrize(
    "broken_lock", ["missing", "symlink"], ids=["missing", "symlink"]
)
def test_probe_reports_unsafe_locks_as_unknown_without_repair(
    tmp_path: Path, broken_lock: str
) -> None:
    """An unavailable or linked lock never becomes an inactive observation."""
    # Given
    root = managed_root(tmp_path)
    generation = reserve_sandbox(root, "probe")
    lock = root / ".probe.ataraxia-sandbox.lock"
    if broken_lock == "missing":
        lock.unlink()
    else:
        retained = root / ".retained-lock"
        lock.rename(retained)
        lock.symlink_to(retained.name)
    before = persistent_snapshot(root)

    # When
    result = sandbox.probe_sandbox(root, "probe", generation)

    # Then
    assert result.activity == "unknown"
    assert persistent_snapshot(root) == before
    if broken_lock == "missing":
        existing_lock = sandbox.locked_sandbox(root, "probe", generation)
        with pytest.raises(ValueError, match="missing stable"), existing_lock:
            pytest.fail("an existing marker must not initialize a missing lock")


@pytest.mark.covers(
    work=(
        "doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/"
        "lock-and-marker/README.md"
    ),
    ac="AC-2",
)
@pytest.mark.parametrize(
    "legacy_record",
    [
        {"common_dir": "/source/.git", "project": "fixture", "base": "a" * 40},
        {
            "schema_version": 1,
            "generation": "bad",
            "common_dir": "/source/.git",
            "project": "fixture",
            "base": "a" * 40,
        },
    ],
    ids=["unsupported-schema", "malformed-generation"],
)
def test_create_rejects_old_or_malformed_markers_without_rewriting(
    tmp_path: Path, legacy_record: dict[str, object]
) -> None:
    """Old or malformed ownership records remain reserved and unchanged."""
    # Given
    root = managed_root(tmp_path)
    marker = root / ".legacy.ataraxia-sandbox.json"
    marker.write_text(json.dumps(legacy_record) + "\n")
    marker.chmod(0o600)
    before = marker.read_bytes()

    # When
    with (
        pytest.raises(ValueError, match="sandbox"),
        sandbox.locked_sandbox(root, "legacy", None, create=True),
    ):
        pytest.fail("unsupported metadata must not acquire creation authority")

    # Then
    assert marker.read_bytes() == before
    assert not (root / "legacy").exists()
    assert not (root / ".legacy.ataraxia-sandbox.lock").exists()


@pytest.mark.covers(
    work=(
        "doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/"
        "lock-and-marker/README.md"
    ),
    ac="AC-2",
)
@pytest.mark.parametrize("kind", ["fifo", "encoding"])
def test_unsafe_marker_fails_public_acquisition_and_probe_without_hanging(
    tmp_path: Path, kind: str
) -> None:
    """Special marker files and invalid UTF-8 fail closed in bounded calls."""
    root = managed_root(tmp_path)
    marker = root / ".unsafe.ataraxia-sandbox.json"
    if kind == "fifo":
        os.mkfifo(marker, 0o600)
    else:
        marker.write_bytes(b"\xff")
        marker.chmod(0o600)
    child = """
import sys
from pathlib import Path
from script import sandbox
root = Path(sys.argv[1])
assert sandbox.probe_sandbox(root, 'unsafe', '0' * 32).activity == 'unknown'
try:
    with sandbox.locked_sandbox(root, 'unsafe', None, create=True):
        raise AssertionError('accepted unsafe marker')
except ValueError:
    pass
"""
    result = subprocess.run(
        [sys.executable, "-c", child, str(root)],
        cwd=Path(__file__).resolve().parents[3],
        check=False,
        capture_output=True,
        text=True,
        timeout=3,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.covers(
    work=(
        "doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/"
        "lock-and-marker/README.md"
    ),
    ac="AC-3",
)
def test_missing_partial_destination_stays_reserved_and_old_generation_is_rejected(
    tmp_path: Path,
) -> None:
    """A marker reserves a missing partial tree and blocks stale name reuse."""
    # Given
    root = managed_root(tmp_path)
    generation = reserve_sandbox(root, "partial")
    lock = root / ".partial.ataraxia-sandbox.lock"
    lock_identity = (lock.stat().st_dev, lock.stat().st_ino)
    shutil.rmtree(root / "partial")

    # When
    with sandbox.locked_sandbox(root, "partial", generation) as retained:
        observed_missing = not retained.destination_present
        create_attempt = sandbox.locked_sandbox(root, "partial", None, create=True)
        with pytest.raises(FileExistsError, match="already exists"), create_attempt:
            pytest.fail("a retained marker must reserve its name")

    # Then
    assert observed_missing
    assert (lock.stat().st_dev, lock.stat().st_ino) == lock_identity
    assert (root / ".partial.ataraxia-sandbox.json").is_file()
    assert not (root / "partial").exists()


@pytest.mark.covers(
    work=(
        "doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/"
        "lock-and-marker/README.md"
    ),
    ac="AC-1",
)
@pytest.mark.covers(
    work=(
        "doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/"
        "lock-and-marker/README.md"
    ),
    ac="AC-3",
)
def test_failed_marker_reservation_keeps_the_destination_reserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed atomic marker reservation cannot enable same-name creation."""
    # Given
    root = managed_root(tmp_path)
    owner: sandbox.SandboxOwner = {
        "common_dir": str(root / "source.git"),
        "project": "fixture-project",
        "base": "a" * 40,
    }

    def refuse_link(source: Path, destination: Path, **kwargs: object) -> None:
        raise OSError("simulated marker reservation failure")

    # When
    monkeypatch.setattr(os, "link", refuse_link)
    with (
        sandbox.locked_sandbox(root, "reserve", None, create=True) as empty,
        pytest.raises(OSError, match="marker reservation failure"),
    ):
        sandbox.reserve_destination(empty, owner)

    # Then
    assert (root / "reserve").is_dir()
    assert not (root / ".reserve.ataraxia-sandbox.json").exists()
    assert (root / ".reserve.ataraxia-sandbox.lock").is_file()
    with (
        pytest.raises(FileExistsError, match="reserved"),
        sandbox.locked_sandbox(root, "reserve", None, create=True),
    ):
        pytest.fail("an orphan destination must remain reserved")


@pytest.mark.covers(
    work=(
        "doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/"
        "lock-and-marker/README.md"
    ),
    ac="AC-2",
)
def test_lock_replacement_after_open_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Revalidate the opened lock inode after the OS lock is acquired."""
    # Given
    root = managed_root(tmp_path)
    generation = reserve_sandbox(root, "replace")
    lock = root / ".replace.ataraxia-sandbox.lock"
    retained = root / ".retained-lock"
    real_flock = fcntl.flock

    def replace_during_acquire(descriptor: int, operation: int) -> None:
        if operation == fcntl.LOCK_EX:
            lock.rename(retained)
            replacement = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
            os.close(replacement)
        real_flock(descriptor, operation)

    # When
    monkeypatch.setattr(fcntl, "flock", replace_during_acquire)
    with (
        pytest.raises(ValueError, match="lock was replaced"),
        sandbox.locked_sandbox(root, "replace", generation),
    ):
        pytest.fail("the replaced lock path must not acquire authority")

    # Then
    assert retained.is_file()
    assert lock.is_file()
    assert (root / ".replace.ataraxia-sandbox.json").is_file()


@pytest.mark.covers(
    work=(
        "doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/"
        "lock-and-marker/README.md"
    ),
    ac="AC-2",
)
def test_probe_replacement_during_acquire_is_unknown_without_marker_repair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = managed_root(tmp_path)
    generation = reserve_sandbox(root, "probe-replace")
    marker = root / ".probe-replace.ataraxia-sandbox.json"
    marker_before = marker.read_bytes()
    lock = root / ".probe-replace.ataraxia-sandbox.lock"
    retained = root / ".retained-probe-lock"
    real_flock = fcntl.flock

    def replace_on_probe(descriptor: int, operation: int) -> None:
        if operation == fcntl.LOCK_EX | fcntl.LOCK_NB:
            lock.rename(retained)
            replacement = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
            os.close(replacement)
        real_flock(descriptor, operation)

    monkeypatch.setattr(fcntl, "flock", replace_on_probe)
    result = sandbox.probe_sandbox(root, "probe-replace", generation)
    assert result.activity == "unknown"
    assert marker.read_bytes() == marker_before
    assert retained.is_file() and lock.is_file()


@pytest.mark.covers(
    work=(
        "doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/"
        "lock-and-marker/README.md"
    ),
    ac="AC-3",
)
def test_same_name_recreation_keeps_lock_inode_and_changes_generation(
    tmp_path: Path,
) -> None:
    """Model removal under lock and ensure reuse creates a fresh generation."""
    # Given
    root = managed_root(tmp_path)
    old_generation = reserve_sandbox(root, "cycle")
    marker = root / ".cycle.ataraxia-sandbox.json"
    destination = root / "cycle"
    lock = root / ".cycle.ataraxia-sandbox.lock"
    lock_identity = (lock.stat().st_dev, lock.stat().st_ino)

    # When
    with sandbox.locked_sandbox(root, "cycle", old_generation):
        shutil.rmtree(destination)
        marker.unlink()
    owner: sandbox.SandboxOwner = {
        "common_dir": str(root / "source.git"),
        "project": "fixture-project",
        "base": "a" * 40,
    }
    with sandbox.locked_sandbox(root, "cycle", None, create=True) as empty:
        fresh = sandbox.reserve_destination(empty, owner)
    new_generation = fresh.generation

    # Then
    assert new_generation is not None
    assert new_generation != old_generation
    assert (lock.stat().st_dev, lock.stat().st_ino) == lock_identity
    with (
        pytest.raises(ValueError, match="generation changed"),
        sandbox.locked_sandbox(root, "cycle", old_generation),
    ):
        pytest.fail("a stale generation must not act on the reused name")


@pytest.mark.covers(
    work=(
        "doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/"
        "lock-and-marker/README.md"
    ),
    ac="AC-3",
)
def test_waiter_captured_before_recreation_refuses_the_new_generation(
    tmp_path: Path,
) -> None:
    """A process waiting on generation A cannot enter recreated generation B."""
    # Given
    root = managed_root(tmp_path)
    old_generation = reserve_sandbox(root, "stale")
    marker = root / ".stale.ataraxia-sandbox.json"
    destination = root / "stale"
    lock = root / ".stale.ataraxia-sandbox.lock"
    lock_identity = (lock.stat().st_dev, lock.stat().st_ino)
    waiter_script = (
        Path(__file__).resolve().parents[3]
        / "test/make/fixtures/sandbox_stale_waiter.py"
    )
    owner: sandbox.SandboxOwner = {
        "common_dir": str(root / "source.git"),
        "project": "fixture-project",
        "base": "a" * 40,
    }

    # When
    waiter: subprocess.Popen[str] | None = None
    try:
        with sandbox.locked_sandbox(root, "stale", old_generation) as original:
            waiter = subprocess.Popen(
                [
                    sys.executable,
                    str(waiter_script),
                    str(root),
                    "stale",
                    old_generation,
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            assert waiter.stdout is not None
            ready, _, _ = select.select([waiter.stdout], (), (), 5)
            assert ready, "waiter did not reach the lock syscall"
            assert waiter.stdout.readline() == "captured\n"
            acquired_early = select.select([waiter.stdout], (), (), 0.2)[0]
            shutil.rmtree(destination)
            marker.unlink()
            empty = sandbox.SandboxScope(
                root, "stale", None, None, None, False, original.lease
            )
            recreated = sandbox.reserve_destination(empty, owner)
        waiter_stdout, waiter_stderr = waiter.communicate(timeout=30)
    finally:
        if waiter is not None and waiter.poll() is None:
            waiter.kill()
            waiter.communicate(timeout=5)

    # Then
    assert not acquired_early
    assert recreated.generation is not None
    assert recreated.generation != old_generation
    assert (lock.stat().st_dev, lock.stat().st_ino) == lock_identity
    assert waiter.returncode == 1
    assert "generation changed" in waiter_stderr
    assert waiter_stdout == ""
