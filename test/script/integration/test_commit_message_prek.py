# SPDX-License-Identifier: Apache-2.0
"""Exercise commit-message filename forwarding through prepared-project prek."""

from pathlib import Path

import pytest

from test.script.commit_message_prek import (
    prepare_project,
    project_input_snapshot,
    run_commit_message_hook,
)
from test.script.commit_message_support import (
    create_message_file,
    observe_git_state,
)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/commit-message/prek/README.md",
    ac="AC-1",
)
def test_prek_forwards_valid_message_filename(tmp_path: Path) -> None:
    """Pass a valid named message through the configured real hook."""
    # Given
    project = prepare_project(tmp_path / "project")
    message_bytes = b"fix: change"
    message_file = create_message_file(tmp_path, message_bytes)

    # When
    result = run_commit_message_hook(project, message_file)

    # Then
    assert result.exit_code == 0
    assert "commit message format" in result.combined
    assert "Passed" in result.combined
    assert message_file.read_bytes() == message_bytes
    assert project_input_snapshot(project.root) == project.inputs
    assert observe_git_state(project.root, project.env) == project.git_state


@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/commit-message/prek/README.md",
    ac="AC-1",
)
def test_prek_refuses_unformatted_message_filename(tmp_path: Path) -> None:
    """Refuse the named malformed message without changing project inputs or refs."""
    # Given
    project = prepare_project(tmp_path / "project")
    message_bytes = b"fix: change\nNo gap"
    message_file = create_message_file(tmp_path, message_bytes)

    # When
    result = run_commit_message_hook(project, message_file)

    # Then
    assert result.exit_code == 1
    assert "commit message format" in result.combined
    assert "Failed" in result.combined
    assert (
        "commit message format: Separate the subject and body with a blank line.\n"
        in result.combined
    )
    assert message_file.read_bytes() == message_bytes
    assert project_input_snapshot(project.root) == project.inputs
    assert observe_git_state(project.root, project.env) == project.git_state
