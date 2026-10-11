# SPDX-License-Identifier: Apache-2.0
"""Verify Mermaid rendering in a fresh offline worktree of this revision."""

from contextlib import suppress
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
TIMEOUT_SECONDS = 300


class ProcessGroupStillRunning(RuntimeError):
    """A timed-out command could not be stopped before cleanup."""


def offline_environment() -> dict[str, str]:
    """Prepare a child environment for offline verification.

    Returns:
        The inherited environment with offline and no-sync modes enforced.
    """
    environment = os.environ.copy()
    for name in (
        "UV_PROJECT_ENVIRONMENT",
        "VIRTUAL_ENV",
        "MAKEFLAGS",
        "MAKEOVERRIDES",
        "MFLAGS",
    ):
        environment.pop(name, None)
    environment.update(UV_OFFLINE="true", UV_NO_SYNC="true")
    return environment


def run(arguments: list[str], *, cwd: Path = ROOT) -> int:
    """Run a bounded command and stop its process group after timeout.

    Returns:
        The child status, or 124 after timeout cleanup.

    Raises:
        ProcessGroupStillRunning: If a timed-out process group remains active.
    """
    process = subprocess.Popen(
        arguments,
        cwd=cwd,
        env=offline_environment(),
        start_new_session=True,
    )
    try:
        return process.wait(timeout=TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGTERM)
        with suppress(subprocess.TimeoutExpired):
            process.wait(timeout=3)
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired as error:
            raise ProcessGroupStillRunning(
                "Timed-out command leader did not exit after SIGKILL"
            ) from error
        deadline = time.monotonic() + 5
        while True:
            try:
                os.killpg(process.pid, 0)
            except ProcessLookupError:
                break
            if time.monotonic() >= deadline:
                raise ProcessGroupStillRunning(
                    "Timed-out command process group did not terminate"
                ) from None
            time.sleep(0.05)
        sys.stderr.write(f"Timed out after {TIMEOUT_SECONDS}s: {arguments!r}\n")
        return 124


def git(arguments: list[str], *, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    """Run a bounded Git command and capture its output.

    Returns:
        The completed process result.
    """
    return subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
        check=False,
    )


def cleanup(destination: Path, parent: Path, branch: str, owns_branch: bool) -> bool:
    """Remove the route cache and worktree before its owned branch and parent.

    Returns:
        Whether all route-owned resources were removed.
    """
    if destination.exists():
        if run(["git", "clean", "-fdx", "--", ".cache"], cwd=destination):
            return False
        if run(["make", "worktree-remove", f"WORKTREE={destination}"]):
            return False
    if owns_branch:
        ref = git(["show-ref", "--verify", "--quiet", f"refs/heads/{branch}"])
        if ref.returncode == 0:
            if run(["git", "branch", "-D", "--", branch]):
                return False
        elif ref.returncode != 1:
            sys.stderr.write(ref.stderr)
            return False
    try:
        parent.rmdir()
    except OSError as error:
        sys.stderr.write(f"Could not remove empty route directory {parent}: {error}\n")
        return False
    return True


def verify_worktree(destination: Path, revision: str) -> int:
    """Confirm the new worktree revision and run the existing renderer test.

    Returns:
        The revision check or smoke-test status.
    """
    result = git(["-C", str(destination), "rev-parse", "HEAD"])
    if result.returncode:
        sys.stderr.write(result.stderr)
        return result.returncode
    actual = result.stdout.strip()
    sys.stdout.write(f"Fresh worktree revision: {actual}\n")
    if actual != revision:
        sys.stderr.write("Fresh worktree does not match the selected revision\n")
        return 1
    return run(
        ["make", "test", "ARGS=test/script/integration/test_mermaid_backend.py"],
        cwd=destination,
    )


def create_and_verify(destination: Path, branch: str, revision: str) -> int:
    """Create the selected worktree and run its existing smoke test.

    Returns:
        The creation or smoke-test status.
    """
    status = run([
        "make",
        "worktree-create",
        f"WORKTREE={destination}",
        f"BRANCH={branch}",
        f"BASE={revision}",
    ])
    return verify_worktree(destination, revision) if status == 0 else status


def finish_route(
    status: int,
    destination: Path,
    parent: Path,
    branch: str,
    owns_branch: bool,
    cleanup_allowed: bool,
) -> int:
    """Clean route state and report both verification and cleanup outcomes.

    Returns:
        The verification status, or one when cleanup alone failed.
    """
    cleaned = False
    if cleanup_allowed:
        try:
            cleaned = cleanup(destination, parent, branch, owns_branch)
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
            sys.stderr.write(f"Cleanup failed: {error}\n")
    if status:
        sys.stderr.write(f"Mermaid worktree verification failed with status {status}\n")
    if not cleaned:
        sys.stderr.write(
            f"Cleanup failed; retained unsafe worktree residue at {destination}\n"
        )
        return status or 1
    if not status:
        sys.stdout.write(f"Disposable worktree and branch cleaned: {branch}\n")
    return status


def execute_route(parent: Path, revision: str) -> int:
    """Create, verify and safely remove one private disposable worktree.

    Returns:
        The verification status, or one when cleanup alone fails.

    Raises:
        RuntimeError: Internally signals a route branch collision or Git failure.
    """
    destination = parent / "worktree"
    branch = f"verify/{parent.name}"
    status = 1
    owns_branch = False
    safe_to_cleanup = True
    cleaned_status = 1
    try:
        existing = git(["show-ref", "--verify", "--quiet", f"refs/heads/{branch}"])
        if existing.returncode == 0:
            raise RuntimeError(f"Route branch already exists: {branch}")
        if existing.returncode != 1:
            raise RuntimeError(existing.stderr)
        # The checked-absent ref is reserved by this private temp name.
        owns_branch = True
        status = create_and_verify(destination, branch, revision)
    except ProcessGroupStillRunning as error:
        sys.stderr.write(f"Active route process group; leaving residue: {error}\n")
        safe_to_cleanup = False
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        sys.stderr.write(f"Verification command failed: {error}\n")
        status = status or 1
    finally:
        cleaned_status = finish_route(
            status,
            destination,
            parent,
            branch,
            owns_branch,
            safe_to_cleanup,
        )
    return cleaned_status


def main() -> int:
    """Select the committed revision and run the disposable verification.

    Returns:
        The verification status, or the Git selection failure status.
    """
    selected = git(["rev-parse", "HEAD"])
    if selected.returncode:
        sys.stderr.write(selected.stderr)
        return selected.returncode
    revision = selected.stdout.strip()
    sys.stdout.write(f"Selected committed revision: {revision}\n")
    parent = Path(tempfile.mkdtemp(prefix="ataraxia-mermaid-"))
    return execute_route(parent, revision)


if __name__ == "__main__":
    raise SystemExit(main())
