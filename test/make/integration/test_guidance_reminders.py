# SPDX-License-Identifier: Apache-2.0
"""Check optional outcome reminders at selected Make command boundaries."""

from pathlib import Path

import pytest

from test.make.support import MakeSandbox, make_sandbox


@pytest.fixture
def sandbox(tmp_path: Path) -> MakeSandbox:
    """Provide real Make with the existing recording uv boundary."""
    return make_sandbox(tmp_path)


@pytest.mark.parametrize(
    ("target", "command", "anchor", "question", "other_question"),
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
            "doc/change-rules.md#fix-the-underlying-problem",
            "existing commands/APIs/helpers",
            "For meaningful changes",
        ),
        (
            "doc-check",
            ("run", "rumdl", "check", "--only-code-block-tools", "--no-cache", "."),
            "doc/README.md#review",
            "whole affected section",
            "For meaningful changes",
        ),
        (
            "doc-check-mermaid",
            ("run", "rumdl", "check", "--only-code-block-tools", "--no-cache", "."),
            "doc/work-contract-template.md#visuals",
            "would a Mermaid diagram or before/after visual clarify what changes?",
            "whole affected section",
        ),
        (
            "ac-check",
            ("run", "python", "script/acceptance_coverage.py", "check"),
            "doc/orchestrator.md#review-and-return",
            "Independent orchestrator review",
            "For meaningful changes",
        ),
        (
            "commit",
            ("run", "python", "script/commit_command.py"),
            "doc/change-rules.md#fix-the-underlying-problem",
            "fundamentally wrong approach",
            "For meaningful changes",
        ),
    ],
    ids=["doc-format", "doc-check", "doc-check-mermaid", "ac-check", "commit"],
)
def test_selected_top_level_targets_remind_after_success(
    sandbox: MakeSandbox,
    target: str,
    command: tuple[str, ...],
    anchor: str,
    question: str,
    other_question: str,
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
    assert other_question not in result.stdout


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
    assert "For meaningful changes:" not in result.stdout


@pytest.mark.parametrize(
    ("arguments", "expected_calls"),
    [
        (("test",), (("run", "pytest", "--cov"),)),
        (
            ("test", "ARGS=test/make/integration/test_guidance_reminders.py"),
            (("run", "pytest", "test/make/integration/test_guidance_reminders.py"),),
        ),
        (("verify-test",), (("run", "pytest", "--cov"),)),
        (("verify-examples",), (("run", "pytest", "example/"),)),
        (
            ("ci-test",),
            (
                ("sync", "--locked", "--group", "dev"),
                ("sync", "--locked", "--group", "dev", "--check", "--offline"),
                ("run", "pytest", "--cov"),
            ),
        ),
        (
            ("ci-examples",),
            (("sync", "--locked", "--group", "dev"), ("run", "pytest", "example/")),
        ),
    ],
    ids=[
        "test-full",
        "test-args",
        "verify-test",
        "verify-examples",
        "ci-test",
        "ci-examples",
    ],
)
def test_selected_test_targets_remind_once_after_success(
    sandbox: MakeSandbox,
    arguments: tuple[str, ...],
    expected_calls: tuple[tuple[str, ...], ...],
) -> None:
    """AC-1/AC-2: successful test targets emit one optional owner reminder."""
    # Given: the recorder returns success and reports output for every command.

    # When
    result = sandbox.run(*arguments, stdout="command output\n")

    # Then
    assert result.exit_code == 0, result.output
    assert tuple(call.argv for call in result.calls) == expected_calls
    assert result.stdout.rindex("command output") < result.stdout.index(
        "Are tests in the right layer/layout?"
    )
    assert (
        tuple(
            result.stdout.count(fragment)
            for fragment in (
                "At Work closure",
                "reviewed static fixtures",
                "independent expectations at the real boundary",
                "doc/testing.md#layout-ownership-and-adoption",
                "doc/test-ownership.md#test-ownership",
                "doc/testing.md#treat-test-data-as-data",
                "doc/testing.md#what-a-test-proves",
                "doc/testing.md#make-expectations-independent",
            )
        )
        == (1,) * 8
    )


def test_help_discloses_the_prepublication_work_review_checkpoint(
    sandbox: MakeSandbox,
) -> None:
    """Lists work-review with a description that places it before publication."""
    # Given: the disposable checkout contains the repository Makefile.

    # When
    result = sandbox.run("help")

    # Then
    assert result.exit_code == 0, result.output
    assert "make work-review" in result.stdout
    assert "deliver PR" in result.stdout
    assert "Work review" in result.stdout
    assert result.stdout.index("Work review") < result.stdout.index("make work-review")


def test_work_review_prompts_concise_delivery_and_keeps_ac_check_focused(
    sandbox: MakeSandbox,
) -> None:
    """Prompts concise review and delivery while ac-check keeps its own role."""
    # Given: both targets run in the existing disposable Make sandbox.

    # When
    review = sandbox.run("work-review")
    acceptance = sandbox.run("ac-check", "WORK=unused/README.md")

    # Then
    assert review.exit_code == 0, review.output
    assert "After Work cleanup" in review.stdout
    assert "complete leaf diff" in review.stdout
    assert "about five minutes" in review.stdout
    assert "pause and ask the maintainer" in review.stdout
    assert "normal publisher flow" in review.stdout
    assert "return the PR to the maintainer" in review.stdout
    assert "doc/workflow.md#scope-and-sizing" in review.stdout
    assert "doc/workflow.md#decisions-and-new-splits" in review.stdout
    assert "doc/orchestrator.md#review-and-return" in review.stdout
    assert all(
        inventory not in review.stdout
        for inventory in (
            "acceptance evidence",
            "commands run",
            "unrun checks",
            "unresolved criteria",
        )
    )
    assert acceptance.exit_code == 0, acceptance.output
    assert "Independent orchestrator review:" in acceptance.stdout
    assert "artifact and revision" not in acceptance.stdout
    assert "acceptance evidence" not in acceptance.stdout
    assert "unrun checks" not in acceptance.stdout
