# SPDX-License-Identifier: Apache-2.0
"""Typed real-Git support for disposable Make worktree arrangements."""

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess

from test.make.support import ROOT, MakeSandbox, make_sandbox


@dataclass(frozen=True)
class GitState:
    """Exact ref and worktree registration observations for refusal checks."""

    refs: str
    registrations: str


@dataclass(frozen=True)
class CreationRepository:
    """Real committed repository with a fixture-file dependency setup boundary."""

    sandbox: MakeSandbox

    def git(
        self, *arguments: str, timeout: float = 30, cwd: Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        """Run Git under isolated configuration and capture diagnostics."""
        return subprocess.run(
            ["git", *arguments],
            cwd=self.sandbox.directory if cwd is None else cwd,
            env=self.sandbox.environment,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True,
        )

    def state(self) -> GitState:
        """Read complete refs and worktree registrations without mutation."""
        return GitState(
            self.git("show-ref").stdout,
            self.git("worktree", "list", "--porcelain").stdout,
        )


def creation_repository(directory: Path) -> CreationRepository:
    """Create a committed disposable Makefile and isolated setup executable."""
    sandbox = make_sandbox(directory)
    recorder = directory / "bin/uv"
    shutil.copyfile(ROOT / "test/make/fixtures/uv_setup.py", recorder)
    recorder.chmod(0o755)
    repository = CreationRepository(sandbox)
    repository.git("init", "-b", "master")
    repository.git("add", "Makefile")
    repository.git(
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.com",
        "-c",
        "commit.gpgsign=false",
        "-c",
        "core.hooksPath=/dev/null",
        "commit",
        "-m",
        "init",
    )
    return repository
