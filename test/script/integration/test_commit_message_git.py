# SPDX-License-Identifier: Apache-2.0
"""Exercise configured comments and commit-hook effects through real Git."""

from pathlib import Path
import sys

import pytest

from test.script.commit_message_support import (
    CHECKER,
    create_message_file,
    create_repository,
    git,
    isolated_environment,
    observe_git_state,
    run_process,
)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/commit-message/git/README.md",
    ac="AC-1",
)
@pytest.mark.parametrize(
    ("comment_prefix", "body", "expected_exit", "expected_stderr"),
    [
        pytest.param("#", "Body.", 0, "", id="hash-short-accepted"),
        pytest.param(
            "#",
            "word " * 20,
            1,
            "commit message format: Wrap body prose at 72 columns: "
            + "word " * 19
            + "word\n",
            id="hash-over-width-refused",
        ),
        pytest.param(";", "Body.", 0, "", id="semicolon-short-accepted"),
        pytest.param(
            ";",
            "word " * 20,
            1,
            "commit message format: Wrap body prose at 72 columns: "
            + "word " * 19
            + "word\n",
            id="semicolon-over-width-refused",
        ),
        pytest.param("//", "Body.", 0, "", id="slash-short-accepted"),
        pytest.param(
            "//",
            "word " * 20,
            1,
            "commit message format: Wrap body prose at 72 columns: "
            + "word " * 19
            + "word\n",
            id="slash-over-width-refused",
        ),
    ],
)
def test_verbose_diff_below_scissors(
    tmp_path: Path,
    comment_prefix: str,
    body: str,
    expected_exit: int,
    expected_stderr: str,
) -> None:
    """Keep configured comments and verbose diff below the checker boundary."""
    # Given
    repository = tmp_path / "repository"
    env = isolated_environment(tmp_path)
    create_repository(repository, env)
    configured = git(
        repository, env, "config", "--local", "core.commentString", comment_prefix
    )
    assert configured.exit_code == 0
    message = (
        f"fix: change\n\n{body}\n\n"
        f"{comment_prefix} Changes to be committed:\n"
        f"{comment_prefix} ------------------------ >8 ------------------------\n"
        f"{comment_prefix} Everything below it will be ignored.\n"
        "diff --git a/example.txt b/example.txt\n"
        "--- a/example.txt\n+++ b/example.txt\n@@ -1 +1 @@\n"
        "+" + "long diff content " * 20 + "\n"
    )
    message_bytes = message.encode("utf-8")
    path = create_message_file(tmp_path, message_bytes)

    # When
    result = run_process((sys.executable, CHECKER, path), cwd=repository, env=env)

    # Then
    assert result.exit_code == expected_exit
    assert result.stdout == ""
    assert result.stderr == expected_stderr
    assert path.read_bytes() == message_bytes


@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/commit-message/git/README.md",
    ac="AC-1",
)
def test_commit_hook_preserves_refs_on_refusal_and_stores_stripped_message(
    tmp_path: Path,
) -> None:
    """Refuse malformed commits and store accepted comment-stripped text."""
    # Given
    repository = tmp_path / "repository"
    env = isolated_environment(tmp_path)
    create_repository(repository, env)
    configured = git(repository, env, "config", "--local", "core.commentChar", ";")
    assert configured.exit_code == 0
    initial = observe_git_state(repository, env)
    assert (
        initial.refs,
        initial.head_ref.exit_code == 0,
        initial.head_commit.exit_code != 0,
    ) == ((), True, True)
    refused_bytes = b"fix: change\nNo gap"
    refused_message = create_message_file(tmp_path / "refused", refused_bytes)

    # When
    rejected = git(
        repository,
        env,
        "commit",
        "--allow-empty",
        "-F",
        str(refused_message),
    )

    # Then
    after_refusal = observe_git_state(repository, env)
    assert (rejected.exit_code, rejected.stdout) == (1, "")
    assert (
        "commit message format: Separate the subject and body with a blank line.\n"
        in rejected.stderr
    )
    assert (after_refusal, refused_message.read_bytes()) == (initial, refused_bytes)

    # Given
    accepted_bytes = ("fix: change\n\nBody.\n; " + "comment " * 30).encode("utf-8")
    accepted_message = create_message_file(tmp_path / "accepted", accepted_bytes)

    # When
    accepted = git(
        repository,
        env,
        "commit",
        "--allow-empty",
        "--cleanup=strip",
        "-F",
        str(accepted_message),
    )

    # Then
    stored = git(repository, env, "log", "-1", "--format=%B")
    final_state = observe_git_state(repository, env)
    assert (accepted.exit_code, accepted.stderr) == (0, "")
    assert final_state.refs == (
        f"{final_state.head_ref.stdout.strip()} "
        f"{final_state.head_commit.stdout.strip()}",
    )
    assert (final_state.head_commit.exit_code, stored.exit_code, stored.stdout) == (
        0,
        0,
        "fix: change\n\nBody.\n\n",
    )
    assert accepted_message.read_bytes() == accepted_bytes
