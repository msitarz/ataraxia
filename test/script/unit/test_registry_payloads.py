# SPDX-License-Identifier: Apache-2.0
"""Check complete package payload values and precise inventory refusals."""

from dataclasses import replace
from typing import Literal

import pytest

from script.registry_selection import Package, PackagePayload
from test.script.selection_inputs import parameter_name
from test.script.support import package_payload

type InvalidPayloadVariant = Literal[
    "missing-payload",
    "multiple-metadata",
    "trace",
    "missing-http",
    "missing-metadata",
    "missing-basis",
]


def invalid_payload_variant(request: pytest.FixtureRequest) -> InvalidPayloadVariant:
    """Narrow the pytest parameter to supported incomplete payload observations."""
    value = parameter_name(request)
    match value:
        case (
            "missing-payload"
            | "multiple-metadata"
            | "trace"
            | "missing-http"
            | "missing-metadata"
            | "missing-basis"
        ):
            return value
        case _:
            raise ValueError(f"unknown invalid payload variant: {value}")


@pytest.fixture
def payload_files() -> dict[str, str]:
    """Provide independent literal archive, METADATA, and resolver entries."""
    return {
        "uv/archive-v0/dependency/payload.txt": "payload",
        "uv/archive-v0/dependency/dependency-1.0.dist-info/METADATA": "metadata",
        "uv/wheels-v6/pypi/dependency/1.0-py3-none-any.http": "http",
    }


@pytest.fixture
def invalid_payload(
    request: pytest.FixtureRequest,
    literal_package: Package,
    payload_files: dict[str, str],
) -> tuple[Package, dict[str, str]]:
    """Build one named missing or contradictory payload observation."""
    match invalid_payload_variant(request):
        case "missing-payload":
            return literal_package, {
                "uv/wheels-v6/pypi/dependency/1.0-py3-none-any.http": "http"
            }
        case "multiple-metadata":
            payload_files["uv/archive-v0/dependency/other-2.0.dist-info/METADATA"] = (
                "other"
            )
        case "trace":
            literal_package = replace(literal_package, trace="wrong/METADATA")
        case "missing-http":
            del payload_files["uv/wheels-v6/pypi/dependency/1.0-py3-none-any.http"]
        case "missing-metadata":
            del payload_files[
                "uv/archive-v0/dependency/dependency-1.0.dist-info/METADATA"
            ]
        case "missing-basis":
            literal_package = replace(literal_package, basis="")
    return literal_package, payload_files


@pytest.fixture
def payload_expected() -> PackagePayload:
    """Return a fully literal expected payload, metadata path, and trace."""
    return PackagePayload(
        frozenset({
            "uv/archive-v0/dependency/payload.txt",
            "uv/archive-v0/dependency/dependency-1.0.dist-info/METADATA",
            "uv/wheels-v6/pypi/dependency/1.0-py3-none-any.http",
        }),
        "uv/archive-v0/dependency/dependency-1.0.dist-info/METADATA",
        frozenset({
            "uv/archive-v0/dependency/payload.txt",
            "uv/archive-v0/dependency/dependency-1.0.dist-info/METADATA",
        }),
    )


@pytest.fixture
def vendored_payload_files(payload_files: dict[str, str]) -> dict[str, str]:
    """Add one literal nested vendored metadata entry to a fresh arrangement."""
    payload_files["uv/archive-v0/dependency/vendor/other-2.0.dist-info/METADATA"] = (
        "vendor"
    )
    return payload_files


@pytest.fixture
def vendored_payload_expected() -> PackagePayload:
    """Return the complete literal payload including nested vendor metadata."""
    return PackagePayload(
        frozenset({
            "uv/archive-v0/dependency/payload.txt",
            "uv/archive-v0/dependency/dependency-1.0.dist-info/METADATA",
            "uv/archive-v0/dependency/vendor/other-2.0.dist-info/METADATA",
            "uv/wheels-v6/pypi/dependency/1.0-py3-none-any.http",
        }),
        "uv/archive-v0/dependency/dependency-1.0.dist-info/METADATA",
        frozenset({
            "uv/archive-v0/dependency/payload.txt",
            "uv/archive-v0/dependency/dependency-1.0.dist-info/METADATA",
            "uv/archive-v0/dependency/vendor/other-2.0.dist-info/METADATA",
        }),
    )


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/payload-inventory/README.md",
    ac="AC-1",
)
def test_payload_inventory_retains_complete_entries(
    literal_package: Package,
    payload_files: dict[str, str],
    payload_expected: PackagePayload,
) -> None:
    """Return complete payload, resolver, and preparation-trace values.

    Covers AC-1: complete public payload values retain their declared entries.
    """
    # Given
    # The fixtures provide independent package and file literals.

    # When
    result = package_payload(literal_package, payload_files)

    # Then
    assert result == payload_expected


@pytest.mark.parametrize(
    ("invalid_payload", "message"),
    [
        pytest.param(
            "missing-payload",
            "missing payload or complete resolver metadata",
            id="missing-payload",
        ),
        pytest.param(
            "multiple-metadata", "expected one wheel METADATA", id="multiple-metadata"
        ),
        pytest.param(
            "trace", "missing package preparation derivation", id="trace-mismatch"
        ),
        pytest.param(
            "missing-http",
            "missing payload or complete resolver metadata",
            id="missing-resolver",
        ),
        pytest.param(
            "missing-metadata", "expected one wheel METADATA", id="missing-metadata"
        ),
        pytest.param(
            "missing-basis",
            "missing package preparation derivation",
            id="missing-basis",
        ),
    ],
    indirect=["invalid_payload"],
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-2",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/payload-inventory/README.md",
    ac="AC-1",
)
def test_incomplete_payload_inventory_is_rejected(
    invalid_payload: tuple[Package, dict[str, str]],
    message: str,
) -> None:
    """Reject missing or contradictory payload observations with exact errors.

    Covers AC-1: each missing or contradictory inventory fails precisely.
    """
    # Given
    package, files = invalid_payload

    # When
    with pytest.raises(ValueError) as error:
        package_payload(package, files)

    # Then
    assert error.type is ValueError
    assert error.value.args == (message,)
    assert error.value.__cause__ is None


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/payload-inventory/README.md",
    ac="AC-1",
)
def test_nested_vendored_metadata_is_retained_without_becoming_package_trace(
    literal_package: Package,
    vendored_payload_files: dict[str, str],
    vendored_payload_expected: PackagePayload,
) -> None:
    """Retain nested vendored METADATA without selecting it as package trace.

    Covers AC-1: complete public payload values retain vendored entries.
    """
    # Given
    # The fixtures provide an independent nested vendor file and full result.

    # When
    result = package_payload(literal_package, vendored_payload_files)

    # Then
    assert result == vendored_payload_expected
