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
    assert "Documentation formatting failed" not in result.stdout
    assert "Documentation checks failed" not in result.stdout
    assert "declarations failed" not in result.stdout
    assert "Commit failed" not in result.stdout


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/work-context/guidance-reminders/README.md",
    ac="AC-1",
)
@pytest.mark.parametrize(
    ("target", "command", "anchor", "notice"),
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
            "doc/README.md#review",
            "Documentation formatting failed",
        ),
        (
            "doc-check",
            ("run", "rumdl", "check", "--no-code-block-tools", "."),
            "doc/README.md#review",
            "Documentation checks failed",
        ),
        (
            "ac-check",
            ("run", "python", "script/acceptance_coverage.py", "check"),
            "doc/orchestrator.md#review-and-return",
            "affected criteria remain unresolved",
        ),
        (
            "commit",
            ("run", "python", "script/commit_command.py"),
            "CONTRIBUTING.md#commits-and-pull-requests",
            "Commit failed",
        ),
    ],
    ids=["doc-format", "doc-check", "ac-check", "commit"],
)
def test_selected_top_level_targets_preserve_failures_and_remind_after_output(
    sandbox: MakeSandbox,
    target: str,
    command: tuple[str, ...],
    anchor: str,
    notice: str,
) -> None:
    """AC-1: Failed commands retain diagnostics/status and emit failure guidance."""
    # Given
    diagnostic = "fixture diagnostic\n"

    # When
    result = sandbox.run(
        target,
        fail_args=command,
        exit_code=7,
        stdout=diagnostic,
        stderr="fixture error\n",
    )

    # Then
    assert result.exit_code == 2, result.output
    assert result.calls[-1].argv == command
    assert result.stdout.index("fixture diagnostic") < result.stdout.index(notice)
    assert anchor in result.stdout
    assert "Error 7" in result.stderr
    assert "fixture error" in result.stderr
    assert "Independent orchestrator review:" not in result.stdout
    assert "If defining a Work:" not in result.stdout
    assert "Was the whole affected section" not in result.stdout
    assert "If a fundamentally wrong approach" not in result.stdout


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/work-context/guidance-reminders/README.md",
    ac="AC-1",
)
@pytest.mark.parametrize(
    ("step", "reached"),
    [
        (
            ("run", "rumdl", "check", "--no-code-block-tools", "."),
            (("run", "rumdl", "check", "--no-code-block-tools", "."),),
        ),
        (
            ("run", "rumdl", "fmt", "--check", "--no-code-block-tools", "."),
            (
                ("run", "rumdl", "check", "--no-code-block-tools", "."),
                ("run", "rumdl", "fmt", "--check", "--no-code-block-tools", "."),
            ),
        ),
        (
            ("run", "rumdl", "check", "--only-code-block-tools", "--no-cache", "."),
            (
                ("run", "rumdl", "check", "--no-code-block-tools", "."),
                ("run", "rumdl", "fmt", "--check", "--no-code-block-tools", "."),
                ("run", "rumdl", "check", "--only-code-block-tools", "--no-cache", "."),
            ),
        ),
    ],
    ids=["links", "format", "mermaid"],
)
def test_doc_check_reports_each_stage_failure_once_and_stops(
    sandbox: MakeSandbox,
    step: tuple[str, ...],
    reached: tuple[tuple[str, ...], ...],
) -> None:
    """AC-1: Every doc-check stage reports failure after diagnostics and stops."""
    # Given
    diagnostic = "stage diagnostic\n"

    # When
    result = sandbox.run(
        "doc-check",
        fail_args=step,
        exit_code=7,
        stdout=diagnostic,
        stderr="stage error\n",
    )

    # Then
    assert result.exit_code == 2, result.output
    assert tuple(call.argv for call in result.calls) == reached
    assert result.stdout.rindex("stage diagnostic") < result.stdout.index(
        "Documentation checks failed"
    )
    assert result.stdout.count("Documentation checks failed") == 1
    assert "whole affected section" not in result.stdout
    assert "Error 7" in result.stderr


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/work-context/guidance-reminders/README.md",
    ac="AC-2",
)
@pytest.mark.parametrize(
    (
        "fail_args",
        "exit_code",
        "stdout",
        "stderr",
        "expected_exit",
        "expected_stdout",
        "expected_stderr",
    ),
    [
        pytest.param(
            (), 0, "nested output\n", "", 0, ("nested output",), (), id="success"
        ),
        pytest.param(
            ("run", "rumdl", "check", "--only-code-block-tools", "--no-cache", "."),
            7,
            "Mermaid diagnostic\n",
            "Mermaid error\n",
            2,
            ("Mermaid diagnostic",),
            ("Mermaid error", "Error 7"),
            id="mermaid-failure",
        ),
    ],
)
def test_recursive_doc_check_suppresses_reminders_and_preserves_outcome(
    sandbox: MakeSandbox,
    fail_args: tuple[str, ...],
    exit_code: int,
    stdout: str,
    stderr: str,
    expected_exit: int,
    expected_stdout: tuple[str, ...],
    expected_stderr: tuple[str, ...],
) -> None:
    """AC-2: Recursive checks preserve all stages and outcomes without reminders."""
    # Given: the parametrized case defines the final Mermaid outcome/diagnostics.

    # When
    result = sandbox.run(
        "verify-check",
        fail_args=fail_args,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
    )

    # Then
    assert result.exit_code == expected_exit, result.output
    assert tuple(
        call.argv for call in result.calls if call.argv[:2] == ("run", "rumdl")
    ) == (
        ("run", "rumdl", "check", "--no-code-block-tools", "."),
        ("run", "rumdl", "fmt", "--check", "--no-code-block-tools", "."),
        ("run", "rumdl", "check", "--only-code-block-tools", "--no-cache", "."),
    )
    assert all(diagnostic in result.stdout for diagnostic in expected_stdout)
    assert all(diagnostic in result.stderr for diagnostic in expected_stderr)
    assert "Was the whole affected section" not in result.stdout
    assert "Documentation checks failed" not in result.stdout


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
