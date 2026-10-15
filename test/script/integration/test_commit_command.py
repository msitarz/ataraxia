# SPDX-License-Identifier: Apache-2.0
"""Exercise the explicit Make commit adapter at its process and Git boundaries."""

from collections.abc import Mapping
from pathlib import Path
import shutil
import sys

import pytest

from script.check_commit_message import check_message
from script.commit_command import format_body
from test.script.commit_message_prek import PreparedProject, prepare_project
from test.script.commit_message_support import (
    GitState,
    ProcessResult,
    create_repository,
    git,
    isolated_environment,
    observe_git_state,
    run_process,
)

ROOT = Path(__file__).resolve().parents[3]
ADAPTER = ROOT / "script" / "commit_command.py"
RUMDL_FAILURE = ROOT / "test" / "script" / "fixtures" / "rumdl_failure.py"


def adapter_process(
    repository: Path,
    environment: Mapping[str, str],
    *,
    subject: str,
    body: str,
) -> ProcessResult:
    """Run the real adapter with explicit literal message inputs."""
    env = dict(environment)
    env.update({
        "ATARAXIA_COMMIT_SUBJECT": subject,
        "ATARAXIA_COMMIT_BODY": body,
    })
    return run_process((sys.executable, ADAPTER), cwd=repository, env=env)


def prepare_commit_project(root: Path) -> tuple[PreparedProject, dict[str, str]]:
    """Prepare real project hooks and a process environment for Git commits."""
    project = prepare_project(root)
    env = dict(project.env)
    env["PATH"] = f"{project.prek.parent}:{env['PATH']}"
    installed = run_process(
        (project.prek, "install", "--hook-type", "commit-msg"),
        cwd=project.root,
        env=env,
    )
    if installed.exit_code:
        raise RuntimeError(f"prek install failed: {installed.combined}")
    return project, env


def prepare_staged_repository(
    root: Path, *, tool_paths: tuple[Path, ...] = ()
) -> tuple[Path, dict[str, str], GitState]:
    """Create a disposable repository with one staged path and its initial refs."""
    env = isolated_environment(
        root, tool_paths=(*tool_paths, Path(sys.executable).parent)
    )
    repository = root / "repository"
    create_repository(repository, env)
    (repository / "staged.txt").write_text("staged\n")
    staged = git(repository, env, "add", "staged.txt")
    if staged.exit_code:
        raise RuntimeError(f"git add failed: {staged.combined}")
    return repository, env, observe_git_state(repository, env)


def test_body_formatting_preserves_expected_prose_list_and_token() -> None:
    """Reflow a paragraph and retain list structure and an unbreakable token."""
    # Given
    token = "https://example.invalid/" + "x" * 80
    body = (
        "Paragraph starts here and keeps each word in its original order while "
        "rumdl wraps this prose across lines.\n\n"
        "- Keep this bullet lead.\n"
        "  And retain its indented continuation.\n\n"
        f"{token}\n"
    )
    expected = (
        "Paragraph starts here and keeps each word in its original order while\n"
        "rumdl wraps this prose across lines.\n\n"
        "- Keep this bullet lead.\n"
        "  And retain its indented continuation.\n\n"
        f"{token}\n"
    )

    # When
    formatted = format_body(body)

    # Then
    assert formatted == expected
    assert check_message("fix: title\n\n" + formatted) == []


@pytest.mark.parametrize(
    ("body", "expected_errors"),
    [
        pytest.param(
            "```sh\n    echo x " + "y" * 61 + "\n```\n",
            (),
            id="marked-command-within-width",
        ),
        pytest.param(
            "```sh\n    echo x " + "y" * 62 + "\n```\n",
            ("Wrap body prose at 72 columns: " + "    echo x " + "y" * 62,),
            id="marked-command-over-width",
        ),
    ],
)
def test_marked_command_uses_existing_checker(
    body: str, expected_errors: tuple[str, ...]
) -> None:
    """Preserve marked commands and apply the unchanged body checker."""
    # Given: ``body`` is the complete formatted-input case.

    # When
    formatted = format_body(body)

    # Then
    assert formatted == body
    assert check_message("fix: title\n\n" + formatted) == list(expected_errors)


def test_formatter_failure_refuses_before_advancing_head(tmp_path: Path) -> None:
    """Refuse a commit when the real formatter process exits unsuccessfully."""
    # Given
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_rumdl = fake_bin / "rumdl"
    shutil.copyfile(RUMDL_FAILURE, fake_rumdl)
    fake_rumdl.chmod(0o755)
    repository, env, before = prepare_staged_repository(
        tmp_path, tool_paths=(fake_bin,)
    )

    # When
    result = adapter_process(repository, env, subject="fix: title", body="valid body")

    # Then
    assert result.exit_code == 1
    assert "rumdl unavailable" in result.stderr
    assert observe_git_state(repository, env) == before


@pytest.mark.parametrize(
    ("body", "expected_message"),
    [
        pytest.param("", "fix: staged change", id="subject-only"),
        pytest.param(
            "The change preserves the staged file for the next operation.",
            (
                "fix: staged change\n\n"
                "The change preserves the staged file for the next operation."
            ),
            id="formatted-prose-body",
        ),
    ],
)
def test_commit_stores_message_through_hooks_and_preserves_unstaged_file(
    tmp_path: Path, body: str, expected_message: str
) -> None:
    """Commit the supplied subject and body through installed project hooks."""
    # Given
    project, env = prepare_commit_project(tmp_path / "project")
    (project.root / "staged.txt").write_text("staged\n")
    (project.root / "unstaged.txt").write_text("unstaged\n")
    assert git(project.root, env, "add", "staged.txt").exit_code == 0
    before = observe_git_state(project.root, env)

    # When
    result = adapter_process(project.root, env, subject="fix: staged change", body=body)

    # Then
    after = observe_git_state(project.root, env)
    assert result.exit_code == 0, result.combined
    assert after.head_commit.stdout != before.head_commit.stdout
    stored_message = git(
        project.root, env, "show", "--no-patch", "--format=%B", "HEAD"
    ).stdout.rstrip("\n")
    assert stored_message == expected_message
    assert git(project.root, env, "status", "--short", "--", "unstaged.txt").stdout == (
        "?? unstaged.txt\n"
    )


def test_commitizen_rejects_nonconventional_subject_without_moving_head(
    tmp_path: Path,
) -> None:
    """Preserve Git state when the installed Conventional Commit hook refuses."""
    # Given
    project, env = prepare_commit_project(tmp_path / "project")
    (project.root / "staged.txt").write_text("staged\n")
    assert git(project.root, env, "add", "staged.txt").exit_code == 0
    before = observe_git_state(project.root, env)

    # When
    result = adapter_process(project.root, env, subject="not conventional", body="")

    # Then
    assert result.exit_code == 1
    assert "commitizen" in result.combined.lower()
    assert observe_git_state(project.root, env) == before
    assert git(project.root, env, "diff", "--cached", "--name-only").stdout == (
        "staged.txt\n"
    )


@pytest.mark.parametrize(
    ("subject", "body", "expected_exit", "diagnostic"),
    [
        pytest.param("", "", 2, "SUBJECT must be a non-empty", id="missing-subject"),
        pytest.param(
            "fix: first\nfix: second",
            "",
            2,
            "SUBJECT must be a non-empty",
            id="multiline-subject",
        ),
        pytest.param(
            "fix: title",
            "```sh\n    echo x " + "y" * 62 + "\n```\n",
            1,
            "Wrap body prose at 72 columns",
            id="marked-command-over-width",
        ),
    ],
)
def test_invalid_inputs_refuse_without_advancing_head(
    tmp_path: Path,
    subject: str,
    body: str,
    expected_exit: int,
    diagnostic: str,
) -> None:
    """Refuse invalid explicit input while preserving the staged commit state."""
    # Given
    repository, env, before = prepare_staged_repository(tmp_path)

    # When
    result = adapter_process(repository, env, subject=subject, body=body)

    # Then
    assert result.exit_code == expected_exit
    assert diagnostic in result.stderr
    assert observe_git_state(repository, env) == before
    assert git(repository, env, "diff", "--cached", "--name-only").stdout == (
        "staged.txt\n"
    )
