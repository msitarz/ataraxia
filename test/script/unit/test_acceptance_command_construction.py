# SPDX-License-Identifier: Apache-2.0
"""Test complete argument construction and selection input refusals."""

from pathlib import Path
import sys
from unittest.mock import patch

import pytest

from test.script.acceptance_support import acceptance_tests as acceptance_tests

# The standalone public function has no root argument and reads module ROOT.
# These scoped overrides redirect only filesystem lookup so its real Work-path
# validation and test-root discovery run against disposable files.


def make_work_fixture(root: Path) -> str:
    """Create an owning README and both selector roots beneath a temporary root."""
    work_file = root / "work" / "README.md"
    work_file.parent.mkdir(parents=True)
    work_file.write_text("# Temporary test Work\n", encoding="utf-8")
    (root / "test").mkdir()
    (root / "example").mkdir()
    return work_file.relative_to(root).as_posix()


@pytest.mark.parametrize(
    ("action", "ac", "expected"),
    [
        (
            "collect",
            "",
            (
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "--collect-only",
                "test",
                "example",
                "-m",
                "covers(work='work/README.md')",
            ),
        ),
        (
            "test",
            "AC-8",
            (
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "test",
                "example",
                "-m",
                "covers(work='work/README.md', ac='AC-8')",
            ),
        ),
    ],
    ids=["collect-work", "test-one-criterion"],
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/acceptance/command-construction/README.md",
    ac="AC-1",
)
def test_build_command_returns_complete_scoped_pytest_argv(
    tmp_path: Path, action: str, ac: str, expected: tuple[str, ...]
) -> None:
    """Check complete argv for both roots, Work selection, and optional AC."""
    # Given
    work = make_work_fixture(tmp_path)

    # When
    with patch.object(acceptance_tests, "ROOT", tmp_path):
        command = acceptance_tests.build_command(action, work, ac)

    # Then
    assert command == list(expected)


@pytest.mark.parametrize(
    ("work", "message"),
    [
        (
            "",
            "WORK is required; provide a repo-relative README.md or spec.md path",
        ),
        (
            "../README.md",
            "WORK must be a normalized repo-relative path",
        ),
        (
            "/tmp/README.md",
            "WORK must be a repo-relative README.md or spec.md path",
        ),
        (
            "work.txt",
            "WORK must name an owning README.md or spec.md",
        ),
        (
            "absent/README.md",
            "WORK does not identify an existing repository file: absent/README.md",
        ),
    ],
    ids=["missing", "escaping", "absolute", "wrong-suffix", "absent"],
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/acceptance/command-construction/README.md",
    ac="AC-1",
)
def test_build_command_rejects_invalid_work_paths_with_exact_errors(
    tmp_path: Path, work: str, message: str
) -> None:
    """Reject invalid Work paths with their exact ValueError arguments."""
    # Given
    # The temporary repository contains no Work files.

    # When
    with (
        patch.object(acceptance_tests, "ROOT", tmp_path),
        pytest.raises(ValueError) as raised,
    ):
        acceptance_tests.build_command("test", work)

    # Then
    assert type(raised.value) is ValueError
    assert raised.value.args == (message,)
    assert raised.value.__cause__ is None


@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/acceptance/command-construction/README.md",
    ac="AC-1",
)
def test_build_command_rejects_invalid_criterion_for_existing_work(
    tmp_path: Path,
) -> None:
    """Reject a noncanonical criterion ID after the Work path is valid."""
    # Given
    work = make_work_fixture(tmp_path)

    # When
    with (
        patch.object(acceptance_tests, "ROOT", tmp_path),
        pytest.raises(ValueError) as raised,
    ):
        acceptance_tests.build_command("test", work, "AC-0")

    # Then
    assert type(raised.value) is ValueError
    assert raised.value.args == ("AC must be a criterion ID such as AC-8",)
    assert raised.value.__cause__ is None
