# SPDX-License-Identifier: Apache-2.0
"""Exercise the registry target's literal arguments and recoverable failures."""

from pathlib import Path
import string
import tempfile

from hypothesis import example, given, settings
from hypothesis import strategies as st
import pytest

from test.script.registry_transport import (
    RegistryCase,
    RegistryInputs,
    copy_registry_project,
    registry_case,
    run_registry_target,
)

_ARGUMENT_CHARACTERS = string.ascii_letters + string.digits + " '\"$()`;&|\\#=*?[]{}"
_ARGUMENT_TAIL = st.text(alphabet=_ARGUMENT_CHARACTERS, min_size=0, max_size=64)


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


@pytest.mark.covers(
    work="doc/feat/testing-conformance/hypothesis/makearguments/README.md", ac="AC-1"
)
@settings(max_examples=25, deadline=None)
@given(
    cache_tail=_ARGUMENT_TAIL,
    record_tail=_ARGUMENT_TAIL,
    preparation_tail=_ARGUMENT_TAIL,
    destination_tail=_ARGUMENT_TAIL,
)
@example(
    cache_tail="$(shell touch MAKE_PWNED)",
    record_tail="",
    preparation_tail="",
    destination_tail="",
)
@example(
    cache_tail="",
    record_tail="$(touch SHELL_PWNED)",
    preparation_tail="",
    destination_tail="",
)
@example(
    cache_tail="",
    record_tail="",
    preparation_tail="`touch TICK_PWNED`",
    destination_tail="",
)
@example(
    cache_tail=" '$(shell touch MAKE_PWNED) cache arg' ",
    record_tail="",
    preparation_tail="",
    destination_tail="",
)
@example(
    cache_tail="",
    record_tail=' "$(touch SHELL_PWNED) record arg" ',
    preparation_tail="",
    destination_tail="",
)
@example(
    cache_tail="",
    record_tail="",
    preparation_tail=" `touch TICK_PWNED` preparation arg ",
    destination_tail="",
)
@example(
    cache_tail="'$(shell touch MAKE_PWNED) cache space'",
    record_tail='$(touch SHELL_PWNED) "record space"',
    preparation_tail="`touch TICK_PWNED` preparation space",
    destination_tail="destination with 'quotes' and *glob? [chars]",
)
def test_registry_target_transports_generated_literal_values(
    cache_tail: str,
    record_tail: str,
    preparation_tail: str,
    destination_tail: str,
) -> None:
    """Check exact four-value transport for bounded hostile generated tails."""
    # Given
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        project = root / "project"
        project.mkdir()
        copy_registry_project(project)
        prepared = registry_case(project, "record")
        expected = RegistryInputs(
            f"cache-prefix-{cache_tail}",
            f"record-prefix-{record_tail}",
            f"preparation-prefix-{preparation_tail}",
            f"destination-prefix-{destination_tail}",
        )
        assignments = (
            f"CACHE={expected.cache}",
            f"RECORD={expected.record}",
            f"PREPARATION_SHA256={expected.expected}",
            f"DESTINATION={expected.destination}",
        )
        case = RegistryCase(prepared.directory, prepared.environment, assignments)

        # When
        result = run_registry_target(case)

        # Then
        assert result.exit_code == 0, result.output
        assert result.inputs == expected
        assert result.markers == ()
