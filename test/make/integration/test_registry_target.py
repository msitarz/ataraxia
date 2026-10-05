# SPDX-License-Identifier: Apache-2.0
"""Exercise the registry target's literal arguments and recoverable failures."""

import pytest

from test.script.support import RegistryInputs, run_registry_target


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-2",
)
def test_registry_target_preserves_literal_named_cli_values(registry_literal_case):
    case = registry_literal_case
    expected = RegistryInputs(
        "cache space's $(shell touch MAKE_PWNED)$(touch SHELL_PWNED)`touch TICK_PWNED`",
        "rec space's $(shell touch MAKE_PWNED)$(touch SHELL_PWNED)`touch TICK_PWNED`",
        "sha space's $(shell touch MAKE_PWNED)$(touch SHELL_PWNED)`touch TICK_PWNED`",
        "dest space's $(shell touch MAKE_PWNED)$(touch SHELL_PWNED)`touch TICK_PWNED`",
    )

    result = run_registry_target(case)

    assert result.exit_code == 0, result.output
    assert result.inputs == expected


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-2",
)
def test_registry_target_does_not_execute_caller_expressions(registry_literal_case):
    case = registry_literal_case

    result = run_registry_target(case)

    assert result.exit_code == 0, result.output
    assert result.markers == ()


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-2",
)
def test_registry_target_rejects_missing_inputs_without_creating_destination(
    registry_missing_case,
):
    case = registry_missing_case

    result = run_registry_target(case)

    assert result.exit_code == 2, result.output
    assert "must be nonempty" in result.stderr
    assert result.destination_exists is False
