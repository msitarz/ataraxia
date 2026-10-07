# SPDX-License-Identifier: Apache-2.0
"""Shared temporary arrangements for registry process tests."""

from dataclasses import replace
import json
from pathlib import Path
from unittest.mock import patch

import pytest

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
    ROOT,
    ChangingRecordRead,
    Package,
    PackagePayload,
)

__all__ = [
    "changed_selection",
    "cli_cache_destination",
    "cli_existing_destination",
    "cli_missing_record",
    "manifest_expected",
    "prepared_selection",
    "selection_expected",
    "unsupported_selection",
]


@pytest.fixture
def changing_record(prepared_selection):
    edge = ChangingRecordRead(
        prepared_selection.record,
        ROOT / "test/script/fixtures/registry_selection/unapproved.json",
        Path.read_bytes,
    )
    with patch.object(Path, "read_bytes", autospec=True, side_effect=edge.read):
        yield edge


@pytest.fixture
def preparation_bytes():
    return (
        ROOT / "test/script/fixtures/registry_selection/records/accepted.json"
    ).read_bytes()


@pytest.fixture
def preparation_expected():
    return json.loads(
        (
            ROOT / "test/script/fixtures/registry_selection/records/accepted.json"
        ).read_text()
    )


@pytest.fixture
def literal_package():
    return Package(
        "uv",
        "dependency",
        "1.0",
        "https://pypi.org/simple",
        "uv/wheels-v6/pypi/dependency/1.0-py3-none-any",
        "uv/archive-v0/dependency",
        "reviewed fixture dependency",
        "uv/archive-v0/dependency/dependency-1.0.dist-info/METADATA",
    )


@pytest.fixture
def layout_package(request, literal_package):
    variants = {
        "root": {"root": "unsupported"},
        "origin": {"origin": "https://other"},
        "name": {"name": "Dependency"},
        "wheel": {"version": "2.0"},
        "archive": {"archive": "uv/other/dependency"},
        "accepted": {},
    }
    return replace(literal_package, **variants[request.param])


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
def layout_links(request):
    variants = {
        "valid": {
            "uv/wheels-v6/pypi/dependency/1.0-py3-none-any": (
                "../../../archive-v0/dependency"
            )
        },
        "missing": {},
    }
    return variants[getattr(request, "param", "valid")]


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
