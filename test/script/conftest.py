# SPDX-License-Identifier: Apache-2.0
"""Shared temporary arrangements for registry process tests."""

from dataclasses import replace

import pytest

from test.script.registry_layout import literal_package as literal_package
from test.script.selection_inputs import (
    changed_selection,
    cli_cache_destination,
    cli_existing_destination,
    cli_missing_record,
    prepared_selection,
    unsupported_selection,
)
from test.script.selection_manifest import manifest_expected, selection_expected
from test.script.support import (
    PackagePayload,
)

__all__ = [
    "changed_selection",
    "cli_cache_destination",
    "cli_existing_destination",
    "cli_missing_record",
    "literal_package",
    "manifest_expected",
    "prepared_selection",
    "selection_expected",
    "unsupported_selection",
]


@pytest.fixture
def payload_files():
    return {
        "uv/archive-v0/dependency/payload.txt": "payload",
        "uv/archive-v0/dependency/dependency-1.0.dist-info/METADATA": "metadata",
        "uv/wheels-v6/pypi/dependency/1.0-py3-none-any.http": "http",
    }


@pytest.fixture
def invalid_payload(request, literal_package, payload_files):
    if request.param == "missing-payload":
        payload_files = {"uv/wheels-v6/pypi/dependency/1.0-py3-none-any.http": "http"}
    elif request.param == "multiple-metadata":
        payload_files["uv/archive-v0/dependency/other-2.0.dist-info/METADATA"] = "other"
    elif request.param == "trace":
        literal_package = replace(literal_package, trace="wrong/METADATA")
    elif request.param == "missing-http":
        del payload_files["uv/wheels-v6/pypi/dependency/1.0-py3-none-any.http"]
    elif request.param == "missing-metadata":
        del payload_files["uv/archive-v0/dependency/dependency-1.0.dist-info/METADATA"]
    elif request.param == "missing-basis":
        literal_package = replace(literal_package, basis="")
    return literal_package, payload_files


@pytest.fixture
def payload_expected():
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
def vendored_payload_files(payload_files):
    payload_files["uv/archive-v0/dependency/vendor/other-2.0.dist-info/METADATA"] = (
        "vendor"
    )
    return payload_files


@pytest.fixture
def vendored_payload_expected():
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
