# SPDX-License-Identifier: Apache-2.0
"""Exercise pure registry validation with independent literal values."""

import pytest

from test.script.support import (
    validate_payload_metadata,
    validate_selected_inventory,
)


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
