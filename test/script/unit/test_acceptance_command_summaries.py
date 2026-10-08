# SPDX-License-Identifier: Apache-2.0
"""Test missing-WORK output and pytest selection summaries."""

import sys

import pytest

from test.script.acceptance_support import (
    SCRIPT as SCRIPT,
)
from test.script.acceptance_support import (
    acceptance_tests as acceptance_tests,
)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/acceptance/command-summaries/README.md",
    ac="AC-1",
)
def test_main_reports_missing_work_before_starting_pytest(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Report the missing-WORK refusal through the public entry point."""
    # Given
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "collect"])
    monkeypatch.setenv("WORK", "")
    monkeypatch.delenv("AC", raising=False)

    # When
    result = acceptance_tests.main()

    # Then
    captured = capsys.readouterr()
    assert result == 2
    assert captured.out == ""
    assert captured.err == (
        "WORK is required; provide a repo-relative README.md or spec.md path\n"
    )


@pytest.mark.parametrize(
    "output",
    [
        "no tests collected (2 deselected)\n",
        "2 deselected in 0.04s\n",
        "no tests ran in 0.04s\n",
    ],
    ids=["collection-empty", "all-deselected", "no-tests-ran"],
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/acceptance/command-summaries/README.md",
    ac="AC-1",
)
def test_recognizes_empty_pytest_summaries(output: str) -> None:
    """Recognize each supported pytest empty-selection summary."""
    # Given
    # `output` is an exact pytest summary variant.

    # When
    result = acceptance_tests.has_no_selected_tests(output)

    # Then
    assert result is True


@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/acceptance/command-summaries/README.md",
    ac="AC-1",
)
def test_selected_pytest_summary_is_not_empty() -> None:
    """Keep a pytest summary with a passing selected test classified as nonempty."""
    # Given
    output = "1 passed, 2 deselected in 0.04s\n"

    # When
    result = acceptance_tests.has_no_selected_tests(output)

    # Then
    assert result is False
