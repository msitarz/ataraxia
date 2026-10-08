# SPDX-License-Identifier: Apache-2.0
"""Check package metadata and declared inventory validation."""

import pytest

from script.registry_selection import Package
from test.script.support import (
    validate_payload_metadata,
    validate_selected_inventory,
)


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/payload-metadata/README.md",
    ac="AC-1",
)
def test_matching_payload_metadata_is_accepted(literal_package: Package) -> None:
    """Accept matching package metadata and an ordinary payload file."""
    # Given
    package = literal_package
    metadata = "Name: Dependency\nVersion: 1.0\n"
    payload = frozenset({"payload.txt"})

    # When
    result = validate_payload_metadata(package, metadata, payload)

    # Then
    assert result is None


@pytest.mark.parametrize(
    ("metadata", "payload", "message"),
    [
        pytest.param(
            "Name: other\nVersion: 1.0\n",
            frozenset({"payload.txt"}),
            "payload METADATA contradicts preparation",
            id="name",
        ),
        pytest.param(
            "Name: dependency\nVersion: 2.0\n",
            frozenset({"payload.txt"}),
            "payload METADATA contradicts preparation",
            id="version",
        ),
        pytest.param(
            "Name: dependency\nVersion: 1.0\n",
            frozenset({"dependency/direct_url.json"}),
            "local-source or environment payload",
            id="local-source",
        ),
        pytest.param(
            "Name: dependency\nVersion: 1.0\n",
            frozenset({"dependency/pyvenv.cfg"}),
            "local-source or environment payload",
            id="environment",
        ),
    ],
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-2",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/payload-metadata/README.md",
    ac="AC-1",
)
def test_contradictory_payload_metadata_is_rejected(
    literal_package: Package,
    metadata: str,
    payload: frozenset[str],
    message: str,
) -> None:
    """Reject name, version, local-source, and environment contradictions."""
    # Given
    # The cases provide literal metadata and payload observations.
    package = literal_package

    # When
    with pytest.raises(ValueError) as error:
        validate_payload_metadata(package, metadata, payload)

    # Then
    assert error.type is ValueError
    assert error.value.args == (message,)
    assert error.value.__cause__ is None


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/payload-metadata/README.md",
    ac="AC-1",
)
def test_declared_inventory_is_accepted(literal_package: Package) -> None:
    """Accept the declared files, wheel link, package, and selected entry."""
    # Given
    files = {"payload": "sha"}
    links = {"uv/wheels-v6/pypi/dependency/1.0-py3-none-any": "target"}
    packages = (literal_package,)
    selected = {"payload"}

    # When
    result = validate_selected_inventory(files, links, packages, selected)

    # Then
    assert result is None


@pytest.mark.parametrize(
    ("files", "links"),
    [
        pytest.param(
            {},
            {"uv/wheels-v6/pypi/dependency/1.0-py3-none-any": "target"},
            id="missing-file",
        ),
        pytest.param({"payload": "sha"}, {}, id="missing-link"),
        pytest.param(
            {"payload": "sha", "answer": "sha"},
            {"uv/wheels-v6/pypi/dependency/1.0-py3-none-any": "target"},
            id="undeclared-file",
        ),
        pytest.param(
            {"payload": "sha"},
            {
                "uv/wheels-v6/pypi/dependency/1.0-py3-none-any": "target",
                "extra-wheel": "target",
            },
            id="undeclared-link",
        ),
    ],
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-2",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/payload-metadata/README.md",
    ac="AC-1",
)
def test_undeclared_inventory_is_rejected(
    literal_package: Package,
    files: dict[str, str],
    links: dict[str, str],
) -> None:
    """Reject missing and undeclared file and wheel-link entries."""
    # Given
    # The cases provide literal file and link inventories.
    package = literal_package
    selected = {"payload"}

    # When
    with pytest.raises(ValueError) as error:
        validate_selected_inventory(files, links, (package,), selected)

    # Then
    assert error.type is ValueError
    assert error.value.args == ("inventory contains undeclared entries",)
    assert error.value.__cause__ is None
