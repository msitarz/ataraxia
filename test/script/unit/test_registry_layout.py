# SPDX-License-Identifier: Apache-2.0
"""Verify supported package layout and wheel-link observations."""

from dataclasses import replace
from typing import Literal

import pytest

from script.registry_selection import (
    Package,
    validate_package_layout,
    validate_wheel_link,
)
from test.script.selection_inputs import parameter_name

type PackageLayoutVariant = Literal[
    "accepted", "root", "origin", "name", "wheel", "archive"
]
type WheelLinkVariant = Literal["valid", "missing"]


def package_layout_variant(
    request: pytest.FixtureRequest,
) -> PackageLayoutVariant:
    """Narrow pytest's external variant to the supported package cases."""
    value = parameter_name(request)
    match value:
        case "accepted" | "root" | "origin" | "name" | "wheel" | "archive":
            return value
        case _:
            raise ValueError(f"unknown package layout variant: {value}")


@pytest.fixture
def layout_package(
    request: pytest.FixtureRequest,
    literal_package: Package,
) -> Package:
    """Change one canonical package field using a finite named variant."""
    match package_layout_variant(request):
        case "accepted":
            return literal_package
        case "root":
            return replace(literal_package, root="unsupported")
        case "origin":
            return replace(literal_package, origin="https://other")
        case "name":
            return replace(literal_package, name="Dependency")
        case "wheel":
            return replace(literal_package, version="2.0")
        case "archive":
            return replace(literal_package, archive="uv/other/dependency")


def wheel_link_variant(request: pytest.FixtureRequest) -> WheelLinkVariant:
    """Narrow an optional pytest parameter to the supported link variants."""
    value: object = getattr(request, "param", "valid")
    match value:
        case "valid" | "missing":
            return value
        case _:
            raise ValueError(f"unknown wheel link variant: {value}")


@pytest.fixture
def layout_links(request: pytest.FixtureRequest) -> dict[str, str]:
    """Provide a fresh valid or missing wheel-link mapping."""
    match wheel_link_variant(request):
        case "valid":
            return {
                "uv/wheels-v6/pypi/dependency/1.0-py3-none-any": (
                    "../../../archive-v0/dependency"
                )
            }
        case "missing":
            return {}


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/payload-layout/README.md",
    ac="AC-1",
)
def test_supported_package_layout_is_accepted(
    literal_package: Package,
    layout_links: dict[str, str],
) -> None:
    """Accept the canonical package and its relative wheel target."""
    # Given
    package = literal_package

    # When
    result = validate_package_layout(package, layout_links)

    # Then
    assert result is None


@pytest.mark.parametrize(
    ("layout_package", "layout_links", "message"),
    [
        pytest.param(
            "root",
            "valid",
            "unsupported registry root or origin",
            id="unsupported-root",
        ),
        pytest.param(
            "origin",
            "valid",
            "unsupported registry root or origin",
            id="unsupported-origin",
        ),
        pytest.param(
            "name", "valid", "noncanonical package name", id="noncanonical-name"
        ),
        pytest.param(
            "wheel", "valid", "wheel does not match declared package", id="wrong-wheel"
        ),
        pytest.param(
            "archive", "valid", "unsupported archive layout", id="wrong-archive"
        ),
        pytest.param(
            "accepted", "missing", "wheel/archive link mismatch", id="wrong-link"
        ),
    ],
    indirect=["layout_package", "layout_links"],
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-2",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/payload-layout/README.md",
    ac="AC-1",
)
def test_unsupported_package_layout_is_rejected(
    layout_package: Package,
    layout_links: dict[str, str],
    message: str,
) -> None:
    """Reject each unsupported package field or link with an exact error."""
    # Given
    package = layout_package

    # When
    with pytest.raises(ValueError) as error:
        validate_package_layout(package, layout_links)

    # Then
    assert error.type is ValueError
    assert error.value.args == (message,)
    assert error.value.__cause__ is None


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-1",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/payload-layout/README.md",
    ac="AC-1",
)
def test_matching_contained_wheel_link_is_accepted() -> None:
    """Accept a matching wheel target when its observed path is contained."""
    # Given
    name, target = "wheel", "target"

    # When
    result = validate_wheel_link(name, target, target, False, True)

    # Then
    assert result is None


@pytest.mark.parametrize(
    ("actual", "parent_linked", "contained", "message"),
    [
        pytest.param(None, False, True, "missing wheel link: wheel", id="missing"),
        pytest.param(
            "target", True, True, "missing wheel link: wheel", id="linked-parent"
        ),
        pytest.param(
            "changed", False, True, "external or changed link: wheel", id="changed"
        ),
        pytest.param(
            "target", False, False, "external or changed link: wheel", id="external"
        ),
    ],
)
@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-2",
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/scripts/registry/payload-layout/README.md",
    ac="AC-1",
)
def test_unsafe_wheel_link_observation_is_rejected(
    actual: str | None,
    parent_linked: bool,
    contained: bool,
    message: str,
) -> None:
    """Reject missing, linked-parent, changed and external wheel links."""
    # Given
    name, target = "wheel", "target"

    # When
    with pytest.raises(ValueError) as error:
        validate_wheel_link(name, target, actual, parent_linked, contained)

    # Then
    assert error.type is ValueError
    assert error.value.args == (message,)
    assert error.value.__cause__ is None
