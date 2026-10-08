# SPDX-License-Identifier: Apache-2.0
"""Exercise commit-message formatting through the real checker CLI."""

from pathlib import Path
import sys

import pytest

from test.script.commit_message_support import (
    CHECKER,
    create_message_file,
    isolated_environment,
    run_process,
)

LONG_TOKEN = "https://example.com/" + "a" * 80


@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/commit-message/checker/README.md",
    ac="AC-1",
)
@pytest.mark.parametrize(
    ("message",),
    [
        pytest.param("", id="empty-message"),
        pytest.param("# Abort this commit\n", id="comment-only-message"),
        pytest.param("fix: short subject\n", id="ordinary-subject"),
        pytest.param("fix: " + "long subject " * 10, id="unrestricted-long-subject"),
        pytest.param("fix: change\n\nA short explanation.\n", id="short-body"),
        pytest.param("fix: change\n\n" + "a " * 35 + "ab\n", id="exactly-72-columns"),
        pytest.param(
            "fix: change\n\n- A short bullet.\n  Its continuation.\n",
            id="bullet-and-continuation",
        ),
        pytest.param(
            "fix: change\n\nWhy: Motivation.\n\nWhat: Behavior.\n\nHow: Approach.\n",
            id="labeled-sections",
        ),
        pytest.param("fix: change\n\n" + LONG_TOKEN, id="standalone-long-token"),
        pytest.param("fix: change\n\n  - " + LONG_TOKEN, id="indented-list-token"),
        pytest.param("fix: change\n\n1. " + LONG_TOKEN, id="numbered-token"),
        pytest.param("fix: change\n\nSigned-off-by: " + "a" * 80, id="long-trailer"),
        pytest.param(
            "fix!: change\n\nBREAKING CHANGE: " + LONG_TOKEN,
            id="breaking-change-token",
        ),
        pytest.param(
            "fix: change\n\nBody.\n# " + "comment " * 30,
            id="ignored-comment-lines",
        ),
        pytest.param("fix: change\r\n\r\nBody.\r\n", id="crlf"),
        pytest.param("Merge branch 'topic'\n", id="merge-subject"),
        pytest.param("fixup! fix: original\n", id="fixup-subject"),
        pytest.param(
            'Revert "fix: original"\n\nThis reverts commit abc123.\n',
            id="revert-subject",
        ),
    ],
)
def test_accept_formatted_or_absent_body(tmp_path: Path, message: str) -> None:
    """Accept retained valid inputs and preserve their exact message bytes."""
    # Given
    message_bytes = message.encode("utf-8")
    path = create_message_file(tmp_path, message_bytes)
    env = isolated_environment(tmp_path)

    # When
    result = run_process((sys.executable, CHECKER, path), cwd=tmp_path, env=env)

    # Then
    assert result.exit_code == 0
    assert result.stdout == ""
    assert result.stderr == ""
    assert path.read_bytes() == message_bytes


@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/commit-message/checker/README.md",
    ac="AC-1",
)
@pytest.mark.parametrize(
    ("message", "expected_stderr"),
    [
        pytest.param(
            "fix: change\nBody without separator.",
            "commit message format: Separate the subject and body with a blank line.\n",
            id="missing-body-separator",
        ),
        pytest.param(
            "fix: change\n\n" + "a " * 36 + "b",
            "commit message format: Wrap body prose at 72 columns: "
            + "a " * 36
            + "b\n",
            id="over-width-plain-prose",
        ),
        pytest.param(
            "fix: change\n\n- " + "word " * 20,
            "commit message format: Wrap body prose at 72 columns: - "
            + "word " * 19
            + "word"
            + "\n",
            id="over-width-bullet",
        ),
        pytest.param(
            "fix: change\n\n  " + "word " * 20,
            "commit message format: Wrap body prose at 72 columns:   "
            + "word " * 19
            + "word"
            + "\n",
            id="over-width-indented-prose",
        ),
        pytest.param(
            "fix: change\n\n\t" + "a " * 32 + "b",
            "commit message format: Wrap body prose at 72 columns: \t"
            + "a " * 32
            + "b\n",
            id="over-width-tab-indented-prose",
        ),
        pytest.param(
            "fix: change\n\nRead this reference: " + LONG_TOKEN,
            "commit message format: Wrap body prose at 72 columns: "
            "Read this reference: " + LONG_TOKEN + "\n",
            id="long-token-with-prose-prefix",
        ),
        pytest.param(
            "fix: change\n\n" + LONG_TOKEN + " trailing prose",
            "commit message format: Wrap body prose at 72 columns: "
            + LONG_TOKEN
            + " trailing prose\n",
            id="long-token-with-trailing-prose",
        ),
    ],
)
def test_reject_unformatted_body(
    tmp_path: Path, message: str, expected_stderr: str
) -> None:
    """Reject retained separator and wrapping violations with exact diagnostics."""
    # Given
    message_bytes = message.encode("utf-8")
    path = create_message_file(tmp_path, message_bytes)
    env = isolated_environment(tmp_path)

    # When
    result = run_process((sys.executable, CHECKER, path), cwd=tmp_path, env=env)

    # Then
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr == expected_stderr
    assert path.read_bytes() == message_bytes
