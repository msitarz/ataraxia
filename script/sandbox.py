# SPDX-License-Identifier: Apache-2.0
"""Create and validate project-owned evaluation sandbox locations."""

from collections.abc import Callable
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
METADATA = ".ataraxia-sandbox.json"


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


def ownership(common_dir: Path, name: str, base: str) -> dict[str, str]:
    """Build the identity record shared by sandbox lifecycle commands.

    Returns:
        The canonical Git common directory, project name, and selected base.
    """
    return {
        "common_dir": str(common_dir),
        "project": name,
        "base": base,
    }


def write_owner_file(path: Path, owner: dict[str, str]) -> None:
    """Create private ownership metadata without following or replacing paths."""
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        stream.write(json.dumps(owner, sort_keys=True) + "\n")


def update_state(path: Path, record: dict[str, str]) -> None:
    """Replace a root-private state record without following a symlink."""
    flags = os.O_WRONLY | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    with os.fdopen(descriptor, "w") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")


def failed_record(
    owner: dict[str, str], stage: str, error: Exception
) -> dict[str, str]:
    """Capture a concise failure stage, process status, and diagnostics.

    Returns:
        Ownership fields plus failed state and retained process diagnostics.
    """
    if isinstance(error, CommandFailure):
        status = str(error.status)
        stdout = error.stdout
        stderr = error.stderr
    else:
        status = "1"
        stdout = ""
        stderr = str(error)
    return owner | {
        "state": "failed",
        "failure_stage": stage,
        "failure_status": status,
        "failure_stdout": stdout,
        "failure_stderr": stderr,
    }


def reserve_destination(
    root: Path, name: str, owner: dict[str, str]
) -> tuple[Path, Path]:
    """Atomically reserve an absent child and its private ownership record.

    Returns:
        The sandbox destination and its ownership metadata path.

    Raises:
        FileExistsError: If the child or ownership path already exists.
    """
    destination = root / name
    sidecar = root / f".{name}{METADATA}"
    if (
        destination.exists()
        or destination.is_symlink()
        or sidecar.exists()
        or sidecar.is_symlink()
    ):
        raise FileExistsError(f"sandbox destination already exists: {destination}")
    write_owner_file(sidecar, owner | {"state": "preparing"})
    try:
        destination.mkdir(mode=0o700)
    except Exception:
        sidecar.unlink(missing_ok=True)
        raise
    return destination, sidecar


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
    """  # ruff: ignore[docstring-extraneous-exception]
    for entry in root.iterdir():
        _check_root_entry_owner(root, entry, common_dir)


def _check_root_entry_owner(root: Path, entry: Path, common_dir: str) -> None:
    """Check one root entry's ownership record and reject observed metadata links.

    Raises:
        ValueError: If metadata is a symlink or belongs to another checkout.
    """
    if entry.is_symlink():
        if entry.name.endswith(METADATA):
            raise ValueError(f"managed ownership metadata is a symlink: {entry}")
        return
    if entry.name.endswith(METADATA):
        metadata = entry
    elif entry.is_dir():
        metadata = entry / METADATA
    else:
        return
    if metadata.is_symlink():
        raise ValueError(f"managed ownership metadata is a symlink: {metadata}")
    if metadata.is_file():
        record = json.loads(metadata.read_text())
        if record.get("common_dir") != common_dir:
            raise ValueError(f"managed root belongs to another checkout: {root}")


def clone_and_prepare(
    source: Path,
    destination: Path,
    name: str,
    base: str,
    branch: str,
    sidecar: Path,
    owner: dict[str, str],
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

    run_recorded_stage(sidecar, owner, "clone", clone)
    run_recorded_stage(
        sidecar,
        owner,
        "readiness",
        lambda: verify_clone(source, destination, name, base),
    )
    run_recorded_stage(sidecar, owner, "setup", setup)
    run_recorded_stage(
        sidecar,
        owner,
        "readiness",
        lambda: run_make_stage(destination, "verify-setup", environment),
    )
    update_state(sidecar, owner | {"state": "ready"})


def run_recorded_stage(
    sidecar: Path,
    owner: dict[str, str],
    stage: str,
    operation: Callable[[], None],
) -> None:
    """Run a stage and persist its failure before propagating the error."""
    try:
        operation()
    except Exception as error:
        update_state(sidecar, failed_record(owner, stage, error))
        raise


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
    destination, sidecar = reserve_destination(root, sandbox_name, owner)
    try:
        clone_and_prepare(
            source, destination, sandbox_name, base, branch, sidecar, owner
        )
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
