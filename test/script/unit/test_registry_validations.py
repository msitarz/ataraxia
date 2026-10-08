# SPDX-License-Identifier: Apache-2.0
"""Exercise pure registry validation with independent literal values."""

import pytest

from test.script.support import (
    package_payload,
    validate_package_layout,
    validate_payload_metadata,
    validate_selected_inventory,
    validate_wheel_link,
)


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-1",
)
def test_supported_package_layout_is_accepted(literal_package, layout_links):
    result = validate_package_layout(literal_package, layout_links)

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
def test_unsupported_package_layout_is_rejected(layout_package, layout_links, message):
    with pytest.raises(ValueError) as error:
        validate_package_layout(layout_package, layout_links)

    assert error.type is ValueError
    assert error.value.args == (message,)
    assert error.value.__cause__ is None


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-1",
)
def test_payload_inventory_retains_complete_entries(
    literal_package, payload_files, payload_expected
):
    result = package_payload(literal_package, payload_files)

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
def test_incomplete_payload_inventory_is_rejected(invalid_payload, message):
    package, files = invalid_payload

    with pytest.raises(ValueError) as error:
        package_payload(package, files)

    assert error.type is ValueError
    assert error.value.args == (message,)
    assert error.value.__cause__ is None


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-1",
)
def test_matching_payload_metadata_is_accepted(literal_package):
    result = validate_payload_metadata(
        literal_package, "Name: Dependency\nVersion: 1.0\n", frozenset({"payload.txt"})
    )

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
def test_contradictory_payload_metadata_is_rejected(
    literal_package, metadata, payload, message
):
    with pytest.raises(ValueError) as error:
        validate_payload_metadata(literal_package, metadata, payload)

    assert error.type is ValueError
    assert error.value.args == (message,)
    assert error.value.__cause__ is None


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-1",
)
def test_declared_inventory_is_accepted(literal_package):
    result = validate_selected_inventory(
        {"payload": "sha"},
        {"uv/wheels-v6/pypi/dependency/1.0-py3-none-any": "target"},
        (literal_package,),
        {"payload"},
    )

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
def test_undeclared_inventory_is_rejected(literal_package, files, links):
    with pytest.raises(ValueError) as error:
        validate_selected_inventory(files, links, (literal_package,), {"payload"})

    assert error.type is ValueError
    assert error.value.args == ("inventory contains undeclared entries",)
    assert error.value.__cause__ is None


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-1",
)
def test_matching_contained_wheel_link_is_accepted():
    result = validate_wheel_link("wheel", "target", "target", False, True)

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
def test_unsafe_wheel_link_observation_is_rejected(
    actual, parent_linked, contained, message
):
    with pytest.raises(ValueError) as error:
        validate_wheel_link("wheel", "target", actual, parent_linked, contained)

    assert error.type is ValueError
    assert error.value.args == (message,)
    assert error.value.__cause__ is None


@pytest.mark.covers(
    work="doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/README.md",
    ac="AC-1",
)
def test_nested_vendored_metadata_is_retained_without_becoming_package_trace(
    literal_package,
    vendored_payload_files,
    vendored_payload_expected,
):
    result = package_payload(literal_package, vendored_payload_files)

    assert result == vendored_payload_expected
