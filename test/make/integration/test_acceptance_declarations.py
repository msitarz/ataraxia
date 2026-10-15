# SPDX-License-Identifier: Apache-2.0
"""Observe static declaration validation through disposable real Make commands."""

from pathlib import Path

import pytest

from test.make.acceptance_support import AcceptanceSandbox, acceptance_sandbox


@pytest.fixture
def declaration_sandbox(tmp_path: Path) -> AcceptanceSandbox:
    """Provide criteria for the real declaration command."""
    sandbox = acceptance_sandbox(tmp_path / "repo")
    selected = sandbox.directory / "test/declarations"
    selected.mkdir(parents=True)
    (selected / "README.md").write_text(
        "# Temporary acceptance contract\n\n"
        "- **AC-1 DONE** Output remains stable.\n"
        "- **AC-2 TODO** A later behavior.\n\n"
        "```markdown\n- **AC-99 DONE** This is only an example.\n```\n"
    )
    return sandbox


def input_files(sandbox: AcceptanceSandbox) -> dict[str, bytes]:
    """Snapshot copied scripts/configuration and contract inputs."""
    return {
        path.relative_to(sandbox.directory).as_posix(): path.read_bytes()
        for path in sandbox.directory.rglob("*")
        if path.is_file()
        and (path.suffix in {".py", ".toml"} or path.name in {"Makefile", "README.md"})
    }


@pytest.mark.real_tool
def test_make_ac_check_reports_complete_neutral_summaries_without_execution(
    declaration_sandbox: AcceptanceSandbox,
) -> None:
    """Report TODO/DONE method summaries without changing input files."""
    # Given
    before = input_files(declaration_sandbox)

    # When
    result = declaration_sandbox.run("ac-check", "WORK=test/declarations/README.md")

    # Then
    assert result.exit_code == 0, result.output
    assert tuple(
        line for line in result.stdout.splitlines() if line.startswith("AC-")
    ) == (
        "AC-1 DONE: no Validation method declared",
        "AC-2 TODO: no Validation method declared",
    )
    assert input_files(declaration_sandbox) == before


@pytest.mark.parametrize(
    ("arguments", "reason"),
    [
        ((), "WORK is required"),
        (("WORK=doc/absent/README.md",), "existing repository file"),
        (("WORK=test/declarations/README.md", "AC=AC-1"), "AC is not supported"),
    ],
    ids=["missing-work", "absent-file", "unsupported-criterion-selector"],
)
@pytest.mark.real_tool
def test_make_ac_check_refuses_independent_invalid_inputs(
    declaration_sandbox: AcceptanceSandbox,
    arguments: tuple[str, ...],
    reason: str,
) -> None:
    """Reject missing WORK, absent files, and unsupported criterion selectors."""
    # Given
    before = input_files(declaration_sandbox)

    # When
    result = declaration_sandbox.run("ac-check", *arguments)

    # Then
    assert result.exit_code == 2, result.output
    assert reason in result.stderr
    assert input_files(declaration_sandbox) == before


@pytest.mark.parametrize(
    ("contract", "reason"),
    [
        ("# Empty Work\n", "no AC declarations"),
        ("# Work\n\n- **AC-0 TODO** Invalid criterion.\n", "malformed AC declaration"),
    ],
    ids=["missing-criteria", "malformed-criterion"],
)
@pytest.mark.real_tool
def test_make_ac_check_refuses_missing_or_malformed_criteria(
    declaration_sandbox: AcceptanceSandbox,
    contract: str,
    reason: str,
) -> None:
    """Reject contracts with missing or malformed criterion declarations."""
    # Given
    (declaration_sandbox.directory / "test/declarations/README.md").write_text(contract)
    before = input_files(declaration_sandbox)

    # When
    result = declaration_sandbox.run("ac-check", "WORK=test/declarations/README.md")

    # Then
    assert result.exit_code == 2, result.output
    assert reason in result.stderr
    assert input_files(declaration_sandbox) == before


@pytest.mark.parametrize(
    ("annotations", "exit_code", "reason", "summaries"),
    [
        (
            "  Validation: inspect generated output.\n",
            0,
            "Validation method declared",
            (
                "AC-1 DONE: no Validation method declared",
                "AC-2 TODO: Validation method declared",
            ),
        ),
        (
            "  Validation:\n",
            2,
            "Validation annotation needs a method",
            (
                "AC-1 DONE: no Validation method declared",
                "AC-2 TODO: no Validation method declared",
            ),
        ),
        (
            "  Validation: inspect output.\n  Validation: compare output.\n",
            2,
            "multiple Validation annotations",
            (
                "AC-1 DONE: no Validation method declared",
                "AC-2 TODO: Validation method declared",
            ),
        ),
        (
            "Validation: inspect generated output.\n",
            0,
            "no Validation method declared",
            (
                "AC-1 DONE: no Validation method declared",
                "AC-2 TODO: no Validation method declared",
            ),
        ),
    ],
    ids=["canonical", "empty-method", "duplicate-methods", "unindented-text"],
)
@pytest.mark.real_tool
def test_make_ac_check_uses_canonical_validation_annotation(
    declaration_sandbox: AcceptanceSandbox,
    annotations: str,
    exit_code: int,
    reason: str,
    summaries: tuple[str, ...],
) -> None:
    """Report methods and reject malformed annotations without mutation."""
    # Given
    (declaration_sandbox.directory / "test/declarations/README.md").write_text(
        "# Work\n\n- **AC-1 DONE** Covered output stays stable.\n"
        "- **AC-2 TODO** Output stays stable.\n" + annotations
    )
    before = input_files(declaration_sandbox)

    # When
    result = declaration_sandbox.run("ac-check", "WORK=test/declarations/README.md")

    # Then
    assert result.exit_code == exit_code, result.output
    assert reason in result.output
    assert (
        tuple(line for line in result.stdout.splitlines() if line.startswith("AC-"))
        == summaries
    )
    assert input_files(declaration_sandbox) == before
