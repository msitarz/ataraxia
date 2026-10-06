# SPDX-License-Identifier: Apache-2.0
"""Verify real nested pytest selection through disposable Make targets."""

from pathlib import Path
import shutil

import pytest

from test.make.acceptance_support import AcceptanceSandbox, acceptance_sandbox
from test.make.support import ROOT


@pytest.fixture
def selection_sandbox(tmp_path: Path) -> AcceptanceSandbox:
    """Install named fixture files in both acceptance discovery roots."""
    sandbox = acceptance_sandbox(tmp_path / "repo")
    selected = sandbox.directory / "test/selection"
    selected.mkdir(parents=True)
    (selected / "README.md").write_text("# Temporary acceptance contract\n")
    example = sandbox.directory / "example"
    example.mkdir()
    shutil.copyfile(
        ROOT / "test/make/fixtures/selection_test_root.py",
        selected / "test_selection_cases.py",
    )
    shutil.copyfile(
        ROOT / "test/make/fixtures/selection_example_root.py",
        example / "test_selection_cases.py",
    )
    return sandbox


@pytest.mark.parametrize(
    ("arguments", "selected", "excluded"),
    [
        (
            ("ac-collect",),
            (
                "test_work_first_criterion_test_root",
                "test_work_first_criterion_example_root",
                "test_work_second_criterion_example_root",
            ),
            ("test_other_work_is_excluded",),
        ),
        (
            ("ac-collect", "AC=AC-1"),
            (
                "test_work_first_criterion_test_root",
                "test_work_first_criterion_example_root",
            ),
            ("test_work_second_criterion_example_root", "test_other_work_is_excluded"),
        ),
        (("ac-test",), ("3 passed",), ("a different Work was selected",)),
        (
            ("ac-test", "AC=AC-1"),
            ("2 passed",),
            (
                "a different Work was selected",
                "test_work_second_criterion_example_root",
            ),
        ),
    ],
    ids=["collect-work", "collect-criterion", "execute-work", "execute-criterion"],
)
@pytest.mark.real_tool
@pytest.mark.covers(
    work="doc/feat/testing-conformance/make/acceptance-targets/selection/README.md",
    ac="AC-1",
)
def test_make_targets_select_work_and_optional_criterion(
    selection_sandbox: AcceptanceSandbox,
    arguments: tuple[str, ...],
    selected: tuple[str, ...],
    excluded: tuple[str, ...],
) -> None:
    """AC-1: Given marked cases in test and example roots, collect/test
    commands select all intended cases for a Work or only its requested criterion,
    exclude unrelated cases, and fail precisely when neither root has a match.

    This case covers successful selection and unrelated-case exclusion.
    """
    # Given: the fixture supplies actual scripts and both named discovery roots.

    # When
    result = selection_sandbox.run(*arguments, "WORK=test/selection/README.md")

    # Then
    assert result.exit_code == 0, result.output
    assert all(text in result.output for text in selected), result.output
    assert all(text not in result.output for text in excluded), result.output


@pytest.mark.parametrize(
    "target", ["ac-collect", "ac-test"], ids=["collect", "execute"]
)
@pytest.mark.real_tool
@pytest.mark.covers(
    work="doc/feat/testing-conformance/make/acceptance-targets/selection/README.md",
    ac="AC-1",
)
def test_make_targets_fail_when_no_criterion_matches(
    selection_sandbox: AcceptanceSandbox,
    target: str,
) -> None:
    """AC-1: Given marked cases in test and example roots, collect/test
    commands select all intended cases for a Work or only its requested criterion,
    exclude unrelated cases, and fail precisely when neither root has a match.

    This case covers precise failure for a criterion absent from both roots.
    """
    # Given: neither fixture root declares AC-9.

    # When
    result = selection_sandbox.run(target, "WORK=test/selection/README.md", "AC=AC-9")

    # Then
    assert result.exit_code == 2, result.output
    assert "4 deselected" in result.stdout
    assert "Error 5" in result.stderr
