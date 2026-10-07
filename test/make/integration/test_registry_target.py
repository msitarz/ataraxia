# SPDX-License-Identifier: Apache-2.0
"""Exercise the registry target's literal arguments and recoverable failures."""

import pytest

from test.script.registry_transport import (
    RegistryCase,
    RegistryInputs,
    run_registry_target,
)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/transport/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-2",
)
def test_registry_target_preserves_literal_named_cli_values(
    registry_literal_case: RegistryCase,
) -> None:
    """Given isolated literal and missing-input arrangements, real Make
    transports named arguments safely and preserves marker/destination refusal
    effects.

    Absent artifacts, stale dependency declarations and unsupported
    tool/index/platform/layout conditions fail with recoverable diagnostics and
    retained evidence, without online fallback or destination overwrite.

    Covers literal argument transport; refusal and shell safety are separate cases.
    Historical AC-2 coverage is limited to Make delegation/refusal, not all
    selector validation conditions.
    """
    # Given
    case = registry_literal_case
    expected = RegistryInputs(
        "cache space's $(shell touch MAKE_PWNED)$(touch SHELL_PWNED)`touch TICK_PWNED`",
        "rec space's $(shell touch MAKE_PWNED)$(touch SHELL_PWNED)`touch TICK_PWNED`",
        "sha space's $(shell touch MAKE_PWNED)$(touch SHELL_PWNED)`touch TICK_PWNED`",
        "dest space's $(shell touch MAKE_PWNED)$(touch SHELL_PWNED)`touch TICK_PWNED`",
    )

    # When
    result = run_registry_target(case)

    # Then
    assert result.exit_code == 0, result.output
    assert result.inputs == expected


@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/transport/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-2",
)
def test_registry_target_does_not_execute_caller_expressions(
    registry_literal_case: RegistryCase,
) -> None:
    """Given isolated literal and missing-input arrangements, real Make
    transports named arguments safely and preserves marker/destination refusal
    effects.

    Absent artifacts, stale dependency declarations and unsupported
    tool/index/platform/layout conditions fail with recoverable diagnostics and
    retained evidence, without online fallback or destination overwrite.

    Covers shell safety; argument transport and refusal are separate cases.
    Historical AC-2 coverage is limited to Make delegation/refusal, not all
    selector validation conditions.
    """
    # Given
    case = registry_literal_case

    # When
    result = run_registry_target(case)

    # Then
    assert result.exit_code == 0, result.output
    assert result.markers == ()


@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/transport/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-2",
)
def test_registry_target_rejects_missing_inputs_without_creating_destination(
    registry_missing_case: RegistryCase,
) -> None:
    """Given isolated literal and missing-input arrangements, real Make
    transports named arguments safely and preserves marker/destination refusal
    effects.

    Absent artifacts, stale dependency declarations and unsupported
    tool/index/platform/layout conditions fail with recoverable diagnostics and
    retained evidence, without online fallback or destination overwrite.

    Covers missing-input refusal and destination absence; other cases cover transport.
    Historical AC-2 coverage is limited to Make delegation/refusal, not all
    selector validation conditions.
    """
    # Given
    case = registry_missing_case

    # When
    result = run_registry_target(case)

    # Then
    assert result.exit_code == 2, result.output
    assert "must be nonempty" in result.stderr
    assert result.destination_exists is False
