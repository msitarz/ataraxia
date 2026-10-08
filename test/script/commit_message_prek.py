# SPDX-License-Identifier: Apache-2.0
"""Arrange isolated projects for prepared-project commit-message hook tests."""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
import shutil
import sys

from test.script.commit_message_support import (
    GitState,
    ProcessResult,
    git,
    isolated_environment,
    observe_git_state,
    run_process,
)

ROOT = Path(__file__).resolve().parents[2]
PREK = Path(sys.executable).with_name("prek")
PROJECT_INPUTS = (
    Path(".pre-commit-config.yaml"),
    Path("pyproject.toml"),
    Path("uv.lock"),
    Path("script/check_commit_message.py"),
    Path("project-input.txt"),
)


@dataclass(frozen=True)
class PreparedProject:
    """Disposable project, prepared tool paths, and retained input snapshot."""

    root: Path
    env: Mapping[str, str]
    prek: Path
    inputs: tuple[tuple[Path, bytes], ...]
    git_state: GitState


def project_input_snapshot(root: Path) -> tuple[tuple[Path, bytes], ...]:
    """Capture exact bytes of the configuration, checker, and sentinel input."""
    return tuple(
        (relative, (root / relative).read_bytes()) for relative in PROJECT_INPUTS
    )


def prepare_project(root: Path) -> PreparedProject:
    """Copy the real hook project and configure prepared offline executables."""
    uv_executable = shutil.which("uv")
    if uv_executable is None:
        raise RuntimeError("uv must be available for the configured local hook")
    if not PREK.is_file():
        raise RuntimeError(f"prepared prek executable is unavailable: {PREK}")

    root.mkdir(parents=True)
    (root / "script").mkdir()
    for relative in PROJECT_INPUTS[:-1]:
        shutil.copyfile(ROOT / relative, root / relative)
    sentinel = root / "project-input.txt"
    sentinel.write_bytes(b"retain this unrelated project input\n")

    env = isolated_environment(root, tool_paths=(Path(uv_executable).parent,))
    for name in tuple(env):
        if name.startswith(("PREK_", "UV_")) or name in ("PYTHONPATH", "VIRTUAL_ENV"):
            del env[name]
    env.update({
        "PREK_HOME": str(root / ".cache" / "prek"),
        "UV_CACHE_DIR": str(root / ".cache" / "uv"),
        "UV_NO_SYNC": "1",
        "UV_OFFLINE": "1",
        "UV_PROJECT_ENVIRONMENT": str(ROOT / ".venv"),
    })

    git_commands = (
        ("init", "--quiet"),
        ("config", "--local", "user.name", "Prek Test"),
        ("config", "--local", "user.email", "prek@example.invalid"),
        ("config", "--local", "commit.gpgsign", "false"),
        ("add", "--all"),
        (
            "commit",
            "--no-verify",
            "--quiet",
            "-m",
            "chore: prepare disposable hook project",
        ),
    )
    for command in git_commands:
        result = git(root, env, *command)
        if result.exit_code != 0:
            raise RuntimeError(f"git {' '.join(command)} failed: {result.combined}")

    return PreparedProject(
        root=root,
        env=env,
        prek=PREK,
        inputs=project_input_snapshot(root),
        git_state=observe_git_state(root, env),
    )


def run_commit_message_hook(
    project: PreparedProject, message_file: Path
) -> ProcessResult:
    """Run the prepared project's real commit-message-format prek hook."""
    return run_process(
        (
            project.prek,
            "run",
            "commit-message-format",
            "--all-files",
            "--hook-stage",
            "commit-msg",
            "--commit-msg-filename",
            message_file,
        ),
        cwd=project.root,
        env=project.env,
    )
