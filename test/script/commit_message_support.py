# SPDX-License-Identifier: Apache-2.0
"""Typed disposable-process and Git support for commit-message tests."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "script" / "check_commit_message.py"
HOOK_FIXTURE = ROOT / "test" / "script" / "fixtures" / "commit_message_hook.py"
HOOK_PYTHON_ENV = "ATARAXIA_COMMIT_MESSAGE_PYTHON"
HOOK_CHECKER_ENV = "ATARAXIA_COMMIT_MESSAGE_CHECKER"
PROCESS_TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class ProcessResult:
    """Captured outcome for one bounded external process."""

    exit_code: int
    stdout: str
    stderr: str

    @property
    def combined(self) -> str:
        """Return both captured streams for diagnostic assertions."""
        return self.stdout + self.stderr


@dataclass(frozen=True)
class GitState:
    """Complete ref listing and symbolic/resolved HEAD observations."""

    refs: tuple[str, ...]
    head_ref: ProcessResult
    head_commit: ProcessResult


def run_process(
    argv: Sequence[str | Path], *, cwd: Path, env: Mapping[str, str]
) -> ProcessResult:
    """Run one process with captured output and the shared timeout."""
    result = subprocess.run(
        list(argv),
        cwd=cwd,
        env=dict(env),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=PROCESS_TIMEOUT_SECONDS,
    )
    return ProcessResult(result.returncode, result.stdout, result.stderr)


def isolated_environment(
    root: Path, *, tool_paths: Sequence[Path] = ()
) -> dict[str, str]:
    """Build HOME, TMPDIR, PATH, and Git configuration isolated under ``root``."""
    home = root / "home"
    temporary = root / "tmp"
    home.mkdir(parents=True, exist_ok=True)
    temporary.mkdir(parents=True, exist_ok=True)

    env = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    path_entries = (
        *tool_paths,
        Path(sys.executable).parent,
        Path("/usr/bin"),
        Path("/bin"),
    )
    env.update({
        "HOME": str(home),
        "TMPDIR": str(temporary),
        "TMP": str(temporary),
        "TEMP": str(temporary),
        "PATH": os.pathsep.join(str(path) for path in path_entries),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_CONFIG_GLOBAL": os.devnull,
        HOOK_PYTHON_ENV: sys.executable,
        HOOK_CHECKER_ENV: str(CHECKER),
    })
    return env


def create_message_file(root: Path, message: bytes) -> Path:
    """Write exact message bytes to a disposable ``message`` file."""
    root.mkdir(parents=True, exist_ok=True)
    path = root / "message"
    path.write_bytes(message)
    return path


def git(repository: Path, env: Mapping[str, str], *args: str) -> ProcessResult:
    """Run real Git in ``repository`` with an explicit environment."""
    return run_process(("git", *args), cwd=repository, env=env)


def create_repository(repository: Path, env: Mapping[str, str]) -> None:
    """Initialize a disposable repo, local identity, signing, and named hook."""
    repository.mkdir(parents=True, exist_ok=True)
    hooks = repository / ".test-hooks"
    hooks.mkdir()
    hook = hooks / "commit-msg"
    shutil.copyfile(HOOK_FIXTURE, hook)
    hook.chmod(0o755)

    commands = (
        ("init", "--quiet"),
        ("config", "--local", "user.name", "Commit Message Test"),
        ("config", "--local", "user.email", "commit-message@example.invalid"),
        ("config", "--local", "commit.gpgsign", "false"),
        ("config", "--local", "core.hooksPath", str(hooks)),
    )
    for command in commands:
        result = git(repository, env, *command)
        if result.exit_code != 0:
            raise RuntimeError(f"git {' '.join(command)} failed: {result.combined}")


def observe_git_state(repository: Path, env: Mapping[str, str]) -> GitState:
    """Capture every ref and both symbolic and resolved HEAD outcomes."""
    refs = git(repository, env, "for-each-ref", "--format=%(refname) %(objectname)")
    if refs.exit_code != 0:
        raise RuntimeError(f"git for-each-ref failed: {refs.combined}")
    head_ref = git(repository, env, "symbolic-ref", "--quiet", "HEAD")
    head_commit = git(repository, env, "rev-parse", "--verify", "HEAD")
    return GitState(tuple(refs.stdout.splitlines()), head_ref, head_commit)
