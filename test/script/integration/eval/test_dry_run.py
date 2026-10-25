# SPDX-License-Identifier: Apache-2.0
"""Intent placeholder for the real dry-run preparation boundary."""

import pytest


@pytest.mark.xfail(
    run=False,
    strict=True,
    reason="not implemented: AC-1 dry run has estimates but no Codex or output effects",
)
def test_dry_run_reports_plan_and_estimates_without_cli_or_output_writes() -> None:
    """Use real Git inputs and observe the command's process and filesystem effects."""
    # Given
    # A disposable clean repository with context and an optional instruction file.

    # When
    # The actual Make entry point runs with --dry-run, with configured and omitted -i.

    # Then
    # It reports scheduled calls and separate known/unknown estimates without Codex
    # probes, model calls, output creation, or retained-evidence mutation.
    pass
