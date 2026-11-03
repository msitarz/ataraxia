# SPDX-License-Identifier: Apache-2.0
"""Workspace validation and owned versus borrowed lifecycle."""

import asyncio
from pathlib import Path
import stat

import pytest

from script.eval.model import HarnessConfig
from script.eval.options import parse_config
from script.eval.workspace import acquire_workspace, validate_workspace_selection


def config(*extra: str) -> HarnessConfig:
    """Provide a minimal dry-run configuration."""
    return parse_config(["-d", "context", "-m", "model", "-e", "low", "-n", *extra])


def test_defaults_and_custom_options() -> None:
    # Given
    default = config()
    selected = config(
        "--working-directory",
        "clone",
        "--sandbox-mode",
        "workspace-write",
        "--enable-tools",
    )

    # When
    values = (default.working_directory, default.sandbox_mode, default.enable_tools)

    # Then
    assert values == (None, "read-only", False)
    assert (
        selected.working_directory,
        selected.sandbox_mode,
        selected.enable_tools,
    ) == (Path("clone"), "workspace-write", True)


def test_writable_workspace_rejects_concurrency_even_without_tools(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Given
    args = ("--sandbox-mode", "workspace-write", "-c", "2")

    # When
    with pytest.raises(SystemExit) as error:
        config(*args)

    # Then
    assert error.value.code == 2
    assert "--concurrency 1" in capsys.readouterr().err


def test_relative_nonempty_workspace_is_resolved_and_untouched(tmp_path: Path) -> None:
    # Given
    workspace = tmp_path / "clone"
    workspace.mkdir()
    (workspace / "file").write_text("keep")
    selected = config("--working-directory", "clone")

    # When
    resolved = validate_workspace_selection(selected, tmp_path)

    # Then
    assert resolved == workspace.resolve()
    assert (workspace / "file").read_text() == "keep"


def test_missing_workspace_is_rejected(tmp_path: Path) -> None:
    # Given
    selected = config("--working-directory", "missing")

    # When / Then
    with pytest.raises(ValueError, match="--working-directory"):
        validate_workspace_selection(selected, tmp_path)


def test_output_through_symlink_inside_writable_workspace_is_rejected(
    tmp_path: Path,
) -> None:
    # Given
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (tmp_path / "alias").symlink_to(workspace, target_is_directory=True)
    selected = config(
        "--working-directory",
        "workspace",
        "--sandbox-mode",
        "workspace-write",
        "-o",
        "alias/new/output",
    )

    # When / Then
    with pytest.raises(ValueError, match="--output-directory"):
        validate_workspace_selection(selected, tmp_path)


async def test_borrowed_workspace_retains_contents_and_permissions(
    tmp_path: Path,
) -> None:
    # Given
    workspace = tmp_path / "borrowed"
    workspace.mkdir(mode=0o750)
    (workspace / "file").write_text("keep")
    selected = config("--working-directory", str(workspace))
    permissions = stat.S_IMODE(workspace.stat().st_mode)

    # When
    async with acquire_workspace(selected, workspace) as acquired:
        assert acquired.cwd == workspace
        assert not acquired.owned

    # Then
    assert (workspace / "file").read_text() == "keep"
    assert stat.S_IMODE(workspace.stat().st_mode) == permissions


async def test_owned_workspace_is_removed_on_cancellation() -> None:
    # Given
    selected = config()
    path: Path | None = None

    # When
    with pytest.raises(asyncio.CancelledError):
        async with acquire_workspace(selected, None) as acquired:
            path = acquired.cwd
            assert stat.S_IMODE(path.stat().st_mode) == 0o555
            raise asyncio.CancelledError

    # Then
    assert path is not None
    assert not path.exists()


def test_read_only_workspace_allows_output_overlap(tmp_path: Path) -> None:
    # Given
    selected = config(
        "--working-directory", str(tmp_path), "-o", str(tmp_path / "output")
    )

    # When
    resolved = validate_workspace_selection(selected, tmp_path)

    # Then
    assert resolved == tmp_path.resolve()
    assert not (tmp_path / "output").exists()


async def test_owned_writable_workspace_is_removed_on_success() -> None:
    # Given
    selected = config("--sandbox-mode", "workspace-write")

    # When
    async with acquire_workspace(selected, None) as acquired:
        path = acquired.cwd
        assert stat.S_IMODE(path.stat().st_mode) & stat.S_IWUSR
        (path / "file").write_text("temporary")

    # Then
    assert not path.exists()


def test_existing_regular_file_is_not_a_workspace(tmp_path: Path) -> None:
    # Given
    file = tmp_path / "file"
    file.write_text("keep")
    selected = config("--working-directory", str(file))

    # When / Then
    with pytest.raises(
        ValueError, match="--working-directory must be an existing directory"
    ):
        validate_workspace_selection(selected, tmp_path)


async def test_borrowed_workspace_is_preserved_on_error(tmp_path: Path) -> None:
    # Given
    workspace = tmp_path / "borrowed"
    workspace.mkdir(mode=0o750)
    marker = workspace / "file"
    marker.write_text("keep")
    permissions = stat.S_IMODE(workspace.stat().st_mode)
    selected = config("--working-directory", str(workspace))

    # When
    with pytest.raises(RuntimeError, match="failure"):
        async with acquire_workspace(selected, workspace):
            raise RuntimeError("failure")

    # Then
    assert workspace.is_dir()
    assert marker.read_text() == "keep"
    assert stat.S_IMODE(workspace.stat().st_mode) == permissions


async def test_borrowed_workspace_is_preserved_on_cancellation(tmp_path: Path) -> None:
    # Given
    workspace = tmp_path / "borrowed"
    workspace.mkdir(mode=0o750)
    marker = workspace / "file"
    marker.write_text("keep")
    permissions = stat.S_IMODE(workspace.stat().st_mode)
    selected = config("--working-directory", str(workspace))

    # When
    with pytest.raises(asyncio.CancelledError):
        async with acquire_workspace(selected, workspace):
            raise asyncio.CancelledError

    # Then
    assert workspace.is_dir()
    assert marker.read_text() == "keep"
    assert stat.S_IMODE(workspace.stat().st_mode) == permissions
