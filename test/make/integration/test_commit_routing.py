# SPDX-License-Identifier: Apache-2.0
"""Check literal commit input routing through real Make."""

from pathlib import Path

import pytest

from test.make.support import MakeSandbox, make_sandbox


@pytest.fixture
def sandbox(tmp_path: Path) -> MakeSandbox:
    """Provide a disposable Makefile and recording uv executable."""
    return make_sandbox(tmp_path)


@pytest.mark.covers(work="doc/feat/commit-command/README.md", ac="AC-2")
def test_commit_target_transports_literal_inputs(sandbox: MakeSandbox) -> None:
    """Preserve shell and Make-looking content as environment data."""
    # Given
    subject = "fix: literal 'quotes' `ticks` $HOME"
    body = (
        'first line\n$(shell touch sentinel) ${HOME} `touch sentinel` "double quotes"'
    )

    # When
    result = sandbox.run(
        "commit",
        f"SUBJECT={subject}",
        f"BODY={body}",
        environment={"STUB_NESTED_MAKE": "1"},
    )

    # Then
    assert result.exit_code == 0, result.output
    assert result.calls[0].argv == ("run", "python", "script/commit_command.py")
    assert result.calls[0].environment["ATARAXIA_COMMIT_SUBJECT"] == subject
    assert result.calls[0].environment["ATARAXIA_COMMIT_BODY"] == body
    assert result.calls[0].environment["MAKE_NESTED_EXIT"] == "0"
    assert "touch sentinel" not in (result.calls[0].environment["MAKEFLAGS"] or "")
    assert not (sandbox.directory / "sentinel").exists()
