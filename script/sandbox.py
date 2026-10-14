# SPDX-License-Identifier: Apache-2.0
"""Create and validate project-owned evaluation sandbox locations."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import json
import math
import os
from pathlib import Path
import re
import secrets
import stat
import subprocess
import sys
import tempfile
from typing import Literal, NotRequired, TypedDict, cast

NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
METADATA = ".ataraxia-sandbox.json"
SCHEMA_VERSION = 1

type JsonValue = (
    str | int | float | bool | list[JsonValue] | dict[str, JsonValue] | None
)


class SandboxOwner(TypedDict):
    """Stable source ownership fields stored in a sandbox marker."""

    common_dir: str
    project: str
    base: str


class SandboxRecord(SandboxOwner):
    """Validated schema fields owned by the lifecycle implementation."""

    schema_version: int
    generation: str
    destination_device: int
    destination_inode: int
    state: Literal["preparing", "ready", "failed"]
    failure_stage: NotRequired[str]
    failure_status: NotRequired[str]
    failure_stdout: NotRequired[str]
    failure_stderr: NotRequired[str]


class SandboxChanges(TypedDict, total=False):
    """Supported mutable marker fields for preparation updates."""

    state: Literal["preparing", "ready", "failed"]
    failure_stage: str
    failure_status: str
    failure_stdout: str
    failure_stderr: str


type SandboxExtensions = dict[str, JsonValue]


@dataclass
class LockLease:
    """Revocable authority tied to one held lock context."""

    descriptor: int
    active: bool = True


@dataclass
class Marker:
    """Validated owned fields separated from forward-compatible extensions."""

    owned: SandboxRecord
    extensions: SandboxExtensions

    def serialized(self) -> dict[str, JsonValue]:
        """Combine validated owned data and preserved extension fields.

        Returns:
            The complete JSON marker mapping.
        """
        return cast(dict[str, JsonValue], self.extensions | self.owned)


@dataclass(frozen=True)
class DestinationIdentity:
    """Native identity of a reserved destination directory."""

    device: int
    inode: int


@dataclass(frozen=True)
class SandboxScope:
    """Validated sandbox identity held under its per-name OS lock."""

    root: Path
    name: str
    generation: str | None
    record: Marker | None
    destination_identity: DestinationIdentity | None
    destination_present: bool
    lease: LockLease


@dataclass(frozen=True)
class ProbeResult:
    """Momentary lock observation; never cleanup authority."""

    activity: Literal["active", "inactive", "unknown"]
    generation: str | None
    destination_identity: DestinationIdentity | None


class CommandFailure(RuntimeError):
    """Retain process status and diagnostics when a preparation command fails."""

    def __init__(
        self,
        command: list[str],
        status: int,
        stdout: str,
        stderr: str,
    ) -> None:
        super().__init__(f"{command[0]} failed with status {status}")
        self.status = status
        self.stdout = stdout
        self.stderr = stderr


def run(command: list[str], *, cwd: Path | None = None) -> str:
    """Run a command and return standard output.

    Returns:
        The stripped standard output.

    Raises:
        CommandFailure: If the process exits unsuccessfully.
    """
    environment = os.environ.copy()
    for key in tuple(environment):
        if key.startswith("GIT_"):
            environment.pop(key)
    environment.update({
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
    })
    result = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        check=False,
        text=True,
        capture_output=True,
        timeout=30,
    )
    if result.returncode:
        raise CommandFailure(command, result.returncode, result.stdout, result.stderr)
    return result.stdout.strip()


def project_name(source: Path) -> str:
    """Read and validate the source project's declared name.

    Returns:
        The validated project name.

    Raises:
        ValueError: If the project name is missing or unsafe.
    """
    import tomllib

    data = tomllib.loads((source / "pyproject.toml").read_text())
    name = data.get("project", {}).get("name")
    if not isinstance(name, str) or not NAME_RE.fullmatch(name):
        raise ValueError("pyproject.toml has no safe [project].name")
    return name


def resolve_root_path(
    source: Path, common_dir: Path, name: str, override: str | None
) -> Path:
    """Select and normalize a root that does not overlap repository paths.

    Returns:
        The absolute selected managed root.

    Raises:
        ValueError: If selection is relative, falls back to cwd, or overlaps Git.
    """
    if override:
        requested = Path(override).expanduser()
        if not requested.is_absolute():
            raise ValueError("SANDBOX_ROOT must be absolute")
        root = requested
    else:
        native = Path(tempfile.gettempdir()).resolve(strict=True)
        if native.resolve() == Path.cwd().resolve():
            raise ValueError(
                "system temporary directory falls back to current directory"
            )
        root = native / name / "sandboxes"
    root = Path(os.path.abspath(root))
    if any(
        root == repository or repository in root.parents or root in repository.parents
        for repository in (source, common_dir)
    ):
        raise ValueError(
            "managed root cannot overlap source checkout or Git common directory"
        )
    return root


def safe_root(source: Path, common_dir: Path, name: str, override: str | None) -> Path:
    """Validate ownership and permissions before creating the managed root.

    Returns:
        The validated managed root.

    Raises:
        ValueError: If the root or an existing ancestor is unsafe.
    """
    root = resolve_root_path(source, common_dir, name, override)
    # The final managed root and child must not traverse a symlink. Native temp
    # aliases such as /var/folders are canonicalized before this check.
    cursor = Path(root.anchor)
    existing: list[Path] = []
    for component in root.parts[1:]:
        cursor /= component
        if cursor.is_symlink():
            raise ValueError(f"managed root contains symlink: {cursor}")
        if cursor.exists():
            existing.append(cursor)
    validate_ancestors(existing)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    validate_ancestors([*root.parents, root])
    info = root.stat()
    if (
        info.st_uid != os.getuid()
        or info.st_mode & 0o077
        or info.st_mode & 0o700 != 0o700
    ):
        raise ValueError(f"managed root has unsuitable owner or permissions: {root}")
    return root


def validate_existing_root(root: Path) -> None:
    """Check the established managed root without creating or repairing it.

    Raises:
        ValueError: If the root or one of its existing ancestors is unsafe.
    """
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise ValueError(f"managed root is missing or unsafe: {root}")
    cursor = Path(root.anchor)
    existing: list[Path] = []
    for component in root.parts[1:]:
        cursor /= component
        if cursor.is_symlink():
            raise ValueError(f"managed root contains symlink: {cursor}")
        existing.append(cursor)
    validate_ancestors(existing)
    info = root.stat()
    if (
        info.st_uid != os.getuid()
        or info.st_mode & 0o077
        or info.st_mode & 0o700 != 0o700
    ):
        raise ValueError(f"managed root has unsuitable owner or permissions: {root}")


def validate_ancestors(paths: list[Path]) -> None:
    """Reject unsafe owner and writable-mode combinations in existing ancestors.

    Raises:
        ValueError: If an ancestor has an unsafe owner or writable mode.
    """
    user_id = os.getuid()
    for path in paths:
        info = path.stat()
        writable_by_others = info.st_mode & (0o020 | 0o002)
        sticky = info.st_mode & 0o1000
        if info.st_uid not in (0, user_id) or (writable_by_others and not sticky):
            raise ValueError(f"managed root has an unsafe ancestor: {path}")


def ownership(common_dir: Path, name: str, base: str) -> SandboxOwner:
    """Build the identity record shared by sandbox lifecycle commands.

    Returns:
        The canonical Git common directory, project name, and selected base.
    """
    return {
        "common_dir": str(common_dir),
        "project": name,
        "base": base,
    }


def marker_path(root: Path, name: str) -> Path:
    """Return the private marker path for a validated sandbox name.

    Raises:
        ValueError: If the name is unsafe.
    """
    if not NAME_RE.fullmatch(name):
        raise ValueError("unsafe sandbox name")
    return root / f".{name}{METADATA}"


def lock_path(root: Path, name: str) -> Path:
    """Return the stable private lock path for a validated sandbox name.

    Raises:
        ValueError: If the name is unsafe.
    """
    if not NAME_RE.fullmatch(name):
        raise ValueError("unsafe sandbox name")
    return root / f".{name}.ataraxia-sandbox.lock"


def _private_regular(path: Path, info: os.stat_result, label: str) -> None:
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_uid != os.getuid()
        or stat.S_IMODE(info.st_mode) != 0o600
    ):
        raise ValueError(f"unsafe {label}: {path}")


def _open_stable_lock(root: Path, name: str) -> int:
    """Open or atomically initialize the stable root-private lock file.

    Returns:
        An open descriptor for the existing or newly created lock.

    Raises:
        ValueError: If the lock path is unsafe or missing for a reserved name.
    """
    path = lock_path(root, name)
    destination = root / name
    metadata = marker_path(root, name)
    try:
        info = path.lstat()
    except FileNotFoundError:
        if any(
            candidate.exists() or candidate.is_symlink()
            for candidate in (destination, metadata)
        ):
            raise ValueError(f"missing stable sandbox lock: {path}") from None
        try:
            created = os.open(
                path,
                os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                0o600,
            )
        except FileExistsError:
            pass
        else:
            try:
                _private_regular(path, os.fstat(created), "sandbox lock")
                os.fsync(created)
                _fsync_directory(root)
            finally:
                os.close(created)
        info = path.lstat()
    _private_regular(path, info, "sandbox lock")
    descriptor = os.open(path, os.O_RDWR | getattr(os, "O_NOFOLLOW", 0))
    try:
        _private_regular(path, os.fstat(descriptor), "sandbox lock")
    except Exception:
        os.close(descriptor)
        raise
    return descriptor


def _validate_lock_path(root: Path, name: str, descriptor: int) -> None:
    """Reject a lock inode whose stable path was replaced while waiting.

    Raises:
        ValueError: If the descriptor or path is unsafe or no longer matches.
    """
    path = lock_path(root, name)
    opened = os.fstat(descriptor)
    current = path.lstat()
    _private_regular(path, current, "sandbox lock")
    if (opened.st_dev, opened.st_ino) != (current.st_dev, current.st_ino):
        raise ValueError(f"sandbox lock was replaced: {path}")


def _require_active_scope(scope: SandboxScope) -> None:
    if not scope.lease.active:
        raise ValueError("sandbox operation requires an active lock scope")
    _validate_lock_path(scope.root, scope.name, scope.lease.descriptor)


def _validated_scope(
    root: Path,
    name: str,
    expected_generation: str | None,
    expected_destination: DestinationIdentity | None,
    create: bool,
    lease: LockLease,
) -> SandboxScope:
    """Compare the waited-on generation and destination with their snapshots.

    Returns:
        A validated scope bound to the held lock descriptor.

    Raises:
        ValueError: If identity changed while waiting.
        FileExistsError: If create finds an occupied name.
    """
    record = _read_marker(root, name)
    generation = None if record is None else record.owned["generation"]
    if generation != expected_generation:
        raise ValueError("sandbox generation changed while waiting for lock")
    if create and record is not None:
        raise FileExistsError(f"sandbox name is reserved: {name}")
    if not create and record is None:
        raise ValueError("sandbox ownership metadata is missing")
    identity = None if record is None else _record_identity(record.owned)
    actual = _destination_identity(root / name)
    if actual != expected_destination:
        raise ValueError("sandbox destination changed while waiting for lock")
    if actual is not None and actual != identity:
        raise ValueError("sandbox destination identity changed")
    if create and actual is not None:
        raise FileExistsError(f"sandbox name is reserved: {name}")
    return SandboxScope(
        root,
        name,
        expected_generation,
        record,
        identity,
        actual is not None,
        lease,
    )


def _destination_identity(path: Path) -> DestinationIdentity | None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISDIR(info.st_mode):
        raise ValueError(f"sandbox destination is not a directory: {path}")
    return DestinationIdentity(info.st_dev, info.st_ino)


def _validate_record(raw: object, path: Path) -> Marker:
    if not isinstance(raw, dict) or any(not isinstance(key, str) for key in raw):
        raise ValueError(f"malformed sandbox metadata: {path}")
    if not all(_is_json_value(value) for value in raw.values()):
        raise ValueError(f"malformed sandbox metadata: {path}")
    values = raw
    schema = values.get("schema_version")
    if (
        not isinstance(schema, int)
        or isinstance(schema, bool)
        or schema != SCHEMA_VERSION
    ):
        raise ValueError(f"unsupported sandbox metadata: {path}")
    generation = values.get("generation")
    if not isinstance(generation, str) or not re.fullmatch(r"[0-9a-f]{32}", generation):
        raise ValueError(f"malformed sandbox generation: {path}")
    if (
        not isinstance(values.get("common_dir"), str)
        or not isinstance(values.get("project"), str)
        or not isinstance(values.get("base"), str)
    ):
        raise ValueError(f"malformed sandbox ownership: {path}")
    if values.get("state") not in ("preparing", "ready", "failed"):
        raise ValueError(f"malformed sandbox state: {path}")
    for field in (
        "failure_stage",
        "failure_status",
        "failure_stdout",
        "failure_stderr",
    ):
        value = values.get(field)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"malformed sandbox diagnostics: {path}")
    if values.get("state") == "failed" and not all(
        isinstance(values.get(field), str)
        for field in (
            "failure_stage",
            "failure_status",
            "failure_stdout",
            "failure_stderr",
        )
    ):
        raise ValueError(f"incomplete sandbox failure diagnostics: {path}")
    if values.get("state") != "failed" and any(
        field in values
        for field in (
            "failure_stage",
            "failure_status",
            "failure_stdout",
            "failure_stderr",
        )
    ):
        raise ValueError(f"unexpected sandbox failure diagnostics: {path}")
    device, inode = values.get("destination_device"), values.get("destination_inode")
    if (
        not isinstance(device, int)
        or isinstance(device, bool)
        or not isinstance(inode, int)
        or isinstance(inode, bool)
        or device < 0
        or inode < 0
    ):
        raise ValueError(f"malformed sandbox destination identity: {path}")
    owned: SandboxRecord = {
        "schema_version": schema,
        "generation": generation,
        "common_dir": values["common_dir"],
        "project": values["project"],
        "base": values["base"],
        "destination_device": device,
        "destination_inode": inode,
        "state": values["state"],
    }
    for field in (
        "failure_stage",
        "failure_status",
        "failure_stdout",
        "failure_stderr",
    ):
        value = values.get(field)
        if isinstance(value, str):
            owned[field] = value
    extensions = {key: value for key, value in values.items() if key not in owned}
    return Marker(owned, extensions)


def _is_json_value(value: object) -> bool:
    if value is None or isinstance(value, (str, bool, int)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(_is_json_value(item) for item in value)
    if isinstance(value, dict):
        return all(
            isinstance(key, str) and _is_json_value(item) for key, item in value.items()
        )
    return False


def _read_marker(root: Path, name: str) -> Marker | None:
    path = marker_path(root, name)
    try:
        before = path.lstat()
    except FileNotFoundError:
        return None
    _private_regular(path, before, "sandbox metadata")
    descriptor = -1
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0),
        )
        info = os.fstat(descriptor)
        _private_regular(path, info, "sandbox metadata")
        path_info = path.lstat()
        if (info.st_dev, info.st_ino) != (path_info.st_dev, path_info.st_ino):
            raise ValueError(f"sandbox metadata was replaced: {path}")
        with os.fdopen(descriptor, encoding="utf-8") as stream:
            descriptor = -1
            raw: object = json.load(stream)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(f"malformed sandbox metadata: {path}") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    return _validate_record(raw, path)


def _record_identity(record: SandboxRecord) -> DestinationIdentity:
    device, inode = record["destination_device"], record["destination_inode"]
    return DestinationIdentity(device, inode)


def _fsync_directory(root: Path) -> None:
    descriptor = os.open(root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic_record(
    root: Path, name: str, record: dict[str, JsonValue], *, create: bool
) -> None:
    path = marker_path(root, name)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{name}.marker-", dir=root)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(json.dumps(record, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        if create:
            os.link(temporary, path, follow_symlinks=False)
            temporary.unlink()
        else:
            current = _read_marker(root, name)
            if current is None:
                raise ValueError(f"sandbox metadata disappeared: {path}")
            os.replace(temporary, path)
        _fsync_directory(root)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def locked_sandbox(
    root: Path,
    name: str,
    expected_generation: str | None,
    *,
    create: bool = False,
) -> Iterator[SandboxScope]:
    """Hold and revalidate one stable per-name lock for lifecycle operations.

    A ``None`` generation is the explicit create reservation state. Existing
    records with a missing destination still reserve their generation.

    Yields:
        A validated sandbox scope while the exclusive OS lock is held.

    Raises:
        ValueError: If ownership, lock, generation, or destination is unsafe.
        FileExistsError: If create finds a reserved or occupied name.
    """
    if not NAME_RE.fullmatch(name):
        raise ValueError("unsafe sandbox name")
    validate_existing_root(root)
    if expected_generation is None and not create:
        raise ValueError("existing sandbox operations require a generation")
    before = _read_marker(root, name)
    before_generation = None if before is None else before.owned["generation"]
    if create and before is not None:
        raise FileExistsError(f"sandbox destination already exists: {root / name}")
    if before_generation != expected_generation:
        raise ValueError("sandbox generation changed before lock acquisition")
    destination = root / name
    before_identity = _destination_identity(destination)
    if before is not None and before_identity not in (
        None,
        _record_identity(before.owned),
    ):
        raise ValueError("sandbox destination identity changed before lock acquisition")
    if create and before_identity is not None:
        raise FileExistsError(f"sandbox name is reserved: {name}")
    descriptor = _open_stable_lock(root, name)
    lease = LockLease(descriptor)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        _validate_lock_path(root, name, descriptor)
        yield _validated_scope(
            root, name, expected_generation, before_identity, create, lease
        )
    finally:
        lease.active = False
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def update_marker(
    scope: SandboxScope, changes: SandboxChanges | SandboxExtensions
) -> SandboxScope:
    """Durably update supported fields while preserving future extensions.

    Returns:
        The updated scope, still valid only while its lock context is active.

    Raises:
        ValueError: If the lock or persisted identity is no longer valid.
    """
    if scope.generation is None or scope.record is None:
        raise ValueError("cannot update an unreserved sandbox")
    _require_active_scope(scope)
    current = _read_marker(scope.root, scope.name)
    if current is None or current.owned["generation"] != scope.generation:
        raise ValueError("sandbox generation changed before marker update")
    immutable = (
        "schema_version",
        "generation",
        "common_dir",
        "project",
        "base",
        "destination_device",
        "destination_inode",
    )
    if any(
        changes.get(field, current.owned[field]) != current.owned[field]
        for field in immutable
    ):
        raise ValueError("sandbox marker update cannot change owned identity")
    if "state" in changes and (
        current.owned["state"] != "preparing"
        or changes["state"] not in ("ready", "failed")
    ):
        raise ValueError("sandbox preparation state cannot be reassigned")
    identity = _record_identity(current.owned)
    actual = _destination_identity(scope.root / scope.name)
    if actual is not None and actual != identity:
        raise ValueError("sandbox destination identity changed before marker update")
    updated = _validate_record(
        current.serialized() | changes, marker_path(scope.root, scope.name)
    )
    _atomic_record(scope.root, scope.name, updated.serialized(), create=False)
    return SandboxScope(
        scope.root,
        scope.name,
        scope.generation,
        updated,
        identity,
        actual is not None,
        scope.lease,
    )


def refresh_scope(scope: SandboxScope) -> SandboxScope:
    """Refresh a held scope from durable marker state.

    Returns:
        The latest validated generation and marker while the same lease is held.

    Raises:
        ValueError: If the lease, generation, marker, or destination changed.
    """
    _require_active_scope(scope)
    validate_existing_root(scope.root)
    if scope.generation is None:
        raise ValueError("refresh requires a reserved sandbox")
    marker = _read_marker(scope.root, scope.name)
    if marker is None or marker.owned["generation"] != scope.generation:
        raise ValueError("sandbox generation changed before scope refresh")
    identity = _record_identity(marker.owned)
    if identity != scope.destination_identity:
        raise ValueError("sandbox destination identity changed before scope refresh")
    actual = _destination_identity(scope.root / scope.name)
    if actual not in (None, identity):
        raise ValueError("sandbox destination identity changed before scope refresh")
    return SandboxScope(
        scope.root,
        scope.name,
        scope.generation,
        marker,
        identity,
        actual is not None,
        scope.lease,
    )


def _observation_matches(
    root: Path, name: str, generation: str, identity: DestinationIdentity
) -> bool:
    """Check that a probe's generation and destination still match its sample.

    Returns:
        Whether the previously observed identity is still current.
    """
    record = _read_marker(root, name)
    if record is None or record.owned["generation"] != generation:
        return False
    return _record_identity(record.owned) == identity and _destination_identity(
        root / name
    ) in (None, identity)


def probe_sandbox(root: Path, name: str, expected_generation: str) -> ProbeResult:
    """Probe an existing lock without creating or changing persistent state.

    Returns:
        Activity, ``unknown`` on any unsafe or inconsistent observation.
    """
    try:
        validate_existing_root(root)
        before = _read_marker(root, name)
        if before is None or before.owned["generation"] != expected_generation:
            return ProbeResult("unknown", None, None)
        identity = _record_identity(before.owned)
        actual = _destination_identity(root / name)
        if actual is not None and actual != identity:
            return ProbeResult("unknown", expected_generation, identity)
        lock = lock_path(root, name)
        info = lock.lstat()
        _private_regular(lock, info, "sandbox lock")
        descriptor = os.open(lock, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            opened = os.fstat(descriptor)
            _private_regular(lock, opened, "sandbox lock")
            current_path = lock.lstat()
            if (opened.st_dev, opened.st_ino) != (
                current_path.st_dev,
                current_path.st_ino,
            ):
                return ProbeResult("unknown", expected_generation, identity)
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                _validate_lock_path(root, name, descriptor)
                if not _observation_matches(root, name, expected_generation, identity):
                    return ProbeResult("unknown", None, None)
                return ProbeResult("active", expected_generation, identity)
            _validate_lock_path(root, name, descriptor)
            if not _observation_matches(root, name, expected_generation, identity):
                return ProbeResult("unknown", None, None)
            return ProbeResult("inactive", expected_generation, identity)
        finally:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally:
                os.close(descriptor)
    except OSError, ValueError:
        return ProbeResult("unknown", None, None)


def failed_record(stage: str, error: Exception) -> SandboxChanges:
    """Capture a concise failure stage, process status, and diagnostics.

    Returns:
        Failed state and retained process diagnostics.
    """
    if isinstance(error, CommandFailure):
        status = str(error.status)
        stdout = error.stdout
        stderr = error.stderr
    else:
        status = "1"
        stdout = ""
        stderr = str(error)
    return {
        "state": "failed",
        "failure_stage": stage,
        "failure_status": status,
        "failure_stdout": stdout,
        "failure_stderr": stderr,
    }


def reserve_destination(scope: SandboxScope, owner: SandboxOwner) -> SandboxScope:
    """Atomically reserve an absent child and its private ownership record.

    Returns:
        The new marker and destination identity within the held lock scope.

    Raises:
        ValueError: If the supplied scope is already reserved or identity fails.
        FileExistsError: If the marker or destination already reserves the name.
    """
    if scope.generation is not None or scope.record is not None:
        raise ValueError("sandbox name is already reserved")
    _require_active_scope(scope)
    if _read_marker(scope.root, scope.name) is not None:
        raise FileExistsError(f"sandbox name is reserved: {scope.name}")
    destination = scope.root / scope.name
    if _destination_identity(destination) is not None:
        raise FileExistsError(f"sandbox name is reserved: {scope.name}")
    destination.mkdir(mode=0o700)
    _fsync_directory(scope.root)
    identity = _destination_identity(destination)
    if identity is None:
        raise ValueError("sandbox destination disappeared during reservation")
    generation = secrets.token_hex(16)
    record = owner | {
        "schema_version": SCHEMA_VERSION,
        "generation": generation,
        "destination_device": identity.device,
        "destination_inode": identity.inode,
        "state": "preparing",
    }
    validated = _validate_record(record, marker_path(scope.root, scope.name))
    _atomic_record(scope.root, scope.name, validated.serialized(), create=True)
    return SandboxScope(
        scope.root,
        scope.name,
        generation,
        validated,
        identity,
        True,
        scope.lease,
    )


def verify_clone(source: Path, destination: Path, name: str, base: str) -> None:
    """Check the clone's depth, selected commit, refs, remotes, and alternates.

    Raises:
        RuntimeError: If clone state differs from the selected input.
    """
    actual = run(["git", "-C", str(destination), "rev-parse", "HEAD"])
    if actual != base:
        raise RuntimeError(f"clone base changed: expected {base}, got {actual}")
    if run(["git", "-C", str(source), "rev-parse", "refs/heads/master"]) != base:
        raise RuntimeError("selected source base changed during clone")
    shallow = run([
        "git",
        "-C",
        str(destination),
        "rev-parse",
        "--is-shallow-repository",
    ])
    count = run(["git", "-C", str(destination), "rev-list", "--count", "HEAD"])
    remotes = run(["git", "-C", str(destination), "remote", "-v"])
    refs = run(["git", "-C", str(destination), "show-ref"]).splitlines()
    expected_ref = f"refs/heads/work/sandbox-{name}"
    if shallow != "true" or count != "1" or remotes:
        raise RuntimeError("clone does not satisfy depth-one isolation")
    if len(refs) != 1 or not refs[0].endswith(expected_ref):
        raise RuntimeError(f"clone has unexpected refs: {refs}")
    if (destination / ".git/objects/info/alternates").exists():
        raise RuntimeError("clone uses an object alternate")


def prepare_clone(destination: Path) -> dict[str, str]:
    """Create fresh final-location setup paths and return their environment.

    Returns:
        Environment for setup and readiness commands.

    Raises:
        RuntimeError: If environment paths already exist in the clone.
    """
    cache = destination / ".cache"
    if cache.exists() or cache.is_symlink():
        raise RuntimeError("clone contains a pre-existing .cache path")
    fresh_paths = (
        cache / "uv",
        cache / "prek",
        destination / ".venv",
        destination / ".tmp",
        destination / ".home",
    )
    if any(path.exists() or path.is_symlink() for path in fresh_paths):
        raise RuntimeError("clone contains pre-existing environment or cache paths")
    for path in fresh_paths:
        path.mkdir(parents=True)
    home = destination / ".home"
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(home),
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
        "UV_CACHE_DIR": str(cache / "uv"),
        "PREK_HOME": str(cache / "prek"),
        "UV_PROJECT_ENVIRONMENT": str(destination / ".venv"),
        "TMPDIR": str(destination / ".tmp"),
    }
    return env


def run_make_stage(destination: Path, target: str, env: dict[str, str]) -> None:
    """Run one setup target and retain complete process diagnostics on failure.

    Raises:
        CommandFailure: If the target exits unsuccessfully.
    """
    command = ["make", target]
    result = subprocess.run(
        command,
        cwd=destination,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=1800,
    )
    if result.returncode:
        raise CommandFailure(command, result.returncode, result.stdout, result.stderr)
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)


def check_root_owner(root: Path, common_dir: str) -> None:
    """Refuse root metadata associated with another Git common directory.

    Raises:
        ValueError: If ownership metadata is unsafe or conflicts.
    """
    for entry in root.iterdir():
        if entry.is_symlink():
            if entry.name.endswith(METADATA):
                raise ValueError(f"managed ownership metadata is a symlink: {entry}")
            continue
        if entry.name.endswith(METADATA):
            metadata = entry
        elif entry.is_dir():
            metadata = entry / METADATA
        else:
            continue
        if metadata.is_symlink():
            raise ValueError(f"managed ownership metadata is a symlink: {metadata}")
        if metadata.is_file():
            record = _validate_record(json.loads(metadata.read_text()), metadata)
            if record.owned["common_dir"] != common_dir:
                raise ValueError(f"managed root belongs to another checkout: {root}")


def clone_and_prepare(
    source: Path,
    destination: Path,
    name: str,
    base: str,
    branch: str,
    scope: SandboxScope,
) -> None:
    """Run preparation stages and persist the terminal state and diagnostics."""

    def clone() -> None:
        run([
            "git",
            "-c",
            "core.hooksPath=/dev/null",
            "clone",
            "--no-local",
            "--depth",
            "1",
            "--single-branch",
            "--branch",
            "master",
            "--no-tags",
            str(source),
            str(destination),
        ])
        run(["git", "-C", str(destination), "remote", "remove", "origin"])
        run(["git", "-C", str(destination), "branch", "-m", branch])

    environment: dict[str, str] = {}

    def setup() -> None:
        environment.update(prepare_clone(destination))
        run_make_stage(destination, "setup", environment)

    scope = run_recorded_stage(scope, "clone", clone)
    scope = run_recorded_stage(
        scope,
        "readiness",
        lambda: verify_clone(source, destination, name, base),
    )
    scope = run_recorded_stage(scope, "setup", setup)
    scope = run_recorded_stage(
        scope,
        "readiness",
        lambda: run_make_stage(destination, "verify-setup", environment),
    )
    update_marker(scope, {"state": "ready"})


def run_recorded_stage(
    scope: SandboxScope,
    stage: str,
    operation: Callable[[], None],
) -> SandboxScope:
    """Run a stage and persist its failure before propagating the error.

    Returns:
        The unchanged scope after a successful stage.
    """
    try:
        operation()
    except Exception as error:
        update_marker(scope, failed_record(stage, error))
        raise
    return scope


def create(source: Path, sandbox_name: str, override: str | None) -> Path:
    """Create an independent shallow clone and run canonical online setup.

    Returns:
        The successfully prepared sandbox path.

    Raises:
        ValueError: If the name, root, or ownership is unsafe.
    """
    if not NAME_RE.fullmatch(sandbox_name):
        raise ValueError(
            "NAME must contain 1-64 safe ASCII letters, digits, dot, _ or -"
        )
    source = source.resolve(strict=True)
    name = project_name(source)
    common = Path(run(["git", "-C", str(source), "rev-parse", "--git-common-dir"]))
    if not common.is_absolute():
        common = source / common
    common = common.resolve(strict=True)
    root = safe_root(source, common, name, override)
    base_ref = "refs/heads/master"
    base = run([
        "git",
        "-C",
        str(source),
        "rev-parse",
        "--verify",
        f"{base_ref}^{{commit}}",
    ])
    owner = ownership(common, name, base)
    branch = f"work/sandbox-{sandbox_name}"
    run(["git", "check-ref-format", "--branch", branch])
    check_root_owner(root, owner["common_dir"])
    with locked_sandbox(root, sandbox_name, None, create=True) as empty_scope:
        check_root_owner(root, owner["common_dir"])
        scope = reserve_destination(empty_scope, owner)
        destination = root / sandbox_name
        try:
            clone_and_prepare(source, destination, sandbox_name, base, branch, scope)
        except Exception:
            sys.stderr.write(
                "Sandbox preparation failed; owned partial state retained at "
                f"{destination}\n"
            )
            raise
    sys.stdout.write(f"Sandbox ready: {destination}\n")
    return destination


def main() -> int:
    """Parse the Make-facing command line.

    Returns:
        A process status suitable for ``sys.exit``.
    """
    if len(sys.argv) != 5 or sys.argv[1] != "create":
        sys.stderr.write(
            "Usage: python script/sandbox.py create NAME SOURCE SANDBOX_ROOT\n"
        )
        return 2
    try:
        create(Path(sys.argv[3]), sys.argv[2], sys.argv[4] or None)
    except Exception as exc:
        if isinstance(exc, CommandFailure):
            sys.stdout.write(exc.stdout)
            sys.stderr.write(exc.stderr)
        sys.stderr.write(f"sandbox-create: {exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
