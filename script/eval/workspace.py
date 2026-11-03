# SPDX-License-Identifier: Apache-2.0
"""Validate and own the evaluation working directory."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
import tempfile

from script.eval.model import HarnessConfig


@dataclass(frozen=True)
class PreparedWorkspace:
    """An absolute working directory and whether the harness owns it."""

    cwd: Path
    owned: bool


def validate_workspace_selection(
    config: HarnessConfig, launch_cwd: Path, /
) -> Path | None:
    """Resolve a supplied directory and protect output from writable workspaces.

    Returns:
        The resolved supplied path, or None for a future owned empty directory.

    Raises:
        ValueError: The directory or its relationship to output is invalid.
    """
    if config.working_directory is None:
        return None
    try:
        workspace = (launch_cwd / config.working_directory).resolve(strict=True)
        output = (
            (launch_cwd / config.output_directory).resolve()
            if config.output_directory
            else None
        )
    except (OSError, RuntimeError) as error:
        raise ValueError(
            f"invalid --working-directory or --output-directory: {error}"
        ) from error
    if not workspace.is_dir():
        raise ValueError("--working-directory must be an existing directory")
    if (
        config.sandbox_mode == "workspace-write"
        and output is not None
        and output.is_relative_to(workspace)
    ):
        raise ValueError(
            "--output-directory must be outside a workspace-write workspace"
        )
    return workspace


@asynccontextmanager
async def acquire_workspace(
    config: HarnessConfig, resolved_path: Path | None, /
) -> AsyncGenerator[PreparedWorkspace]:
    """Borrow a supplied directory or clean up an owned directory on exit.

    Yields:
        The workspace path and ownership.
    """
    if resolved_path is not None:
        yield PreparedWorkspace(resolved_path, False)
        return
    with tempfile.TemporaryDirectory(prefix="ataraxia-eval-") as directory:
        cwd = Path(directory).resolve() / "empty"
        cwd.mkdir(mode=0o555 if config.sandbox_mode == "read-only" else 0o700)
        yield PreparedWorkspace(cwd, True)


def require_supported_execution(config: HarnessConfig, /) -> None:
    """Refuse controls the current request builder cannot yet apply.

    Raises:
        ValueError: The requested controls require the future request builder.
    """
    if (
        config.working_directory is not None
        or config.sandbox_mode != "read-only"
        or config.enable_tools
    ):
        raise ValueError(
            "nondefault workspace, sandbox, and tool controls are available "
            "only with --dry-run; execution currently supports defaults only"
        )
