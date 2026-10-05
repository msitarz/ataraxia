# SPDX-License-Identifier: Apache-2.0
"""Prove the reusable recorder boundary through actual Make."""

from pathlib import Path

import pytest

from test.make.support import make_sandbox


@pytest.mark.covers(
    work="doc/feat/testing-conformance/make/stub-environment/helper/README.md",
    ac="AC-1",
)
def test_make_records_literal_arguments_in_an_isolated_environment(
    tmp_path: Path,
) -> None:
    """AC-1: Given fresh temporary arrangements, real Make launches the
    recorder, preserves arguments/flags, and exposes configured failure and
    diagnostics.

    This case covers argument transport and the isolated environment.
    """
    # Given
    sandbox = make_sandbox(tmp_path)

    # When
    result = sandbox.run("format-check", "ARGS=src/example's.py")

    # Then
    assert result.exit_code == 0, result.output
    assert tuple(call.argv for call in result.calls) == (
        ("run", "ruff", "format", "--check", "src/example's.py"),
    )
    assert result.calls[0].environment == {
        "UV_OFFLINE": None,
        "UV_NO_SYNC": None,
        "UV_CACHE_DIR": str(tmp_path / ".cache/uv"),
        "PREK_HOME": str(tmp_path / ".cache/prek"),
        "UV_PROJECT_ENVIRONMENT": None,
        "VIRTUAL_ENV": None,
        "HOME": str(tmp_path / "home"),
        "TMPDIR": str(tmp_path / "tmp"),
    }


@pytest.mark.covers(
    work="doc/feat/testing-conformance/make/stub-environment/helper/README.md",
    ac="AC-1",
)
def test_make_exposes_configured_failure_and_stops_later_commands(
    tmp_path: Path,
) -> None:
    """AC-1: Given fresh temporary arrangements, real Make launches the
    recorder, preserves arguments/flags, and exposes configured failure and
    diagnostics.

    This case covers configured failure, diagnostics, and stopping later commands.
    """
    # Given
    sandbox = make_sandbox(tmp_path)

    # When
    result = sandbox.run(
        "doc-check",
        fail_args=("run", "rumdl", "check", "."),
        exit_code=7,
        stdout="fixture output\n",
        stderr="fixture error\n",
    )

    # Then
    assert result.exit_code == 2, result.output
    assert tuple(call.argv for call in result.calls) == (
        ("run", "rumdl", "check", "."),
    )
    assert result.calls[0].environment["UV_OFFLINE"] == "true"
    assert result.calls[0].environment["UV_NO_SYNC"] == "true"
    assert "fixture output\n" in result.stdout
    assert "fixture error\n" in result.stderr
    assert "Error 7" in result.stderr
