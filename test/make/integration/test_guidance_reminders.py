# SPDX-License-Identifier: Apache-2.0
"""Check optional outcome reminders at selected Make command boundaries."""

from pathlib import Path

import pytest

from test.make.support import MakeSandbox, make_sandbox


@pytest.fixture
def sandbox(tmp_path: Path) -> MakeSandbox:
    """Provide real Make with the existing recording uv boundary."""
    return make_sandbox(tmp_path)


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/work-context/guidance-reminders/README.md",
    ac="AC-1",
)
@pytest.mark.parametrize(
    ("target", "command", "anchor", "question"),
    [
        (
            "doc-format",
            (
                "run",
                "rumdl",
                "fmt",
                "--no-code-block-tools",
                "--config",
                "pyproject.toml",
                ".",
            ),
            "doc/work-definition.md#work-definition",
            "existing commands/APIs/helpers",
        ),
        (
            "doc-check",
            ("run", "rumdl", "check", "--only-code-block-tools", "--no-cache", "."),
            "doc/README.md#review",
            "whole affected section",
        ),
        (
            "ac-check",
            ("run", "python", "script/acceptance_coverage.py", "check"),
            "doc/orchestrator.md#review-and-return",
            "Independent orchestrator review",
        ),
        (
            "commit",
            ("run", "python", "script/commit_command.py"),
            "doc/change-rules.md#fix-the-underlying-problem",
            "fundamentally wrong approach",
        ),
    ],
    ids=["doc-format", "doc-check", "ac-check", "commit"],
)
def test_selected_top_level_targets_remind_after_success(
    sandbox: MakeSandbox,
    target: str,
    command: tuple[str, ...],
    anchor: str,
    question: str,
) -> None:
    """AC-1: Successful selected targets emit their owner question afterward."""
    # Given: the existing recorder returns success for the selected command.

    # When
    result = sandbox.run(target, stdout="command output\n")

    # Then
    assert result.exit_code == 0, result.output
    assert result.calls[-1].argv == command
    assert result.stdout.rindex("command output") < result.stdout.index(question)
    assert result.stdout.count(anchor) == 1
    assert result.stdout.count(question) == 1


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/work-context/guidance-reminders/README.md",
    ac="AC-2",
)
def test_recursive_doc_check_suppresses_only_the_reminder(sandbox: MakeSandbox) -> None:
    """AC-2: Nested static checks retain all three documentation commands."""
    # Given: the fixture supplies a successful recorder for every command.

    # When
    result = sandbox.run("verify-check", stdout="nested output\n")

    # Then
    assert result.exit_code == 0, result.output
    assert tuple(
        call.argv for call in result.calls if call.argv[:2] == ("run", "rumdl")
    ) == (
        ("run", "rumdl", "check", "--no-code-block-tools", "."),
        ("run", "rumdl", "fmt", "--check", "--no-code-block-tools", "."),
        ("run", "rumdl", "check", "--only-code-block-tools", "--no-cache", "."),
    )
    assert "nested output" in result.stdout
    assert "Was the whole affected section" not in result.stdout


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/work-context/guidance-reminders/README.md",
    ac="AC-2",
)
def test_mermaid_target_has_no_reminder(sandbox: MakeSandbox) -> None:
    """AC-2: The unselected Mermaid helper remains reminder-free."""
    # Given: a direct helper invocation reaches the recording command.

    # When
    result = sandbox.run("doc-check-mermaid")

    # Then
    assert result.exit_code == 0, result.output
    assert result.calls[0].argv == (
        "run",
        "rumdl",
        "check",
        "--only-code-block-tools",
        "--no-cache",
        ".",
    )
    assert "doc/README.md#review" not in result.stdout
