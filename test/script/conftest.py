# SPDX-License-Identifier: Apache-2.0
"""Shared temporary arrangements for registry process tests."""

from dataclasses import replace
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from test.script.support import (
    ROOT,
    ChangingRecordRead,
    Package,
    PackagePayload,
    arrange_changed_input,
    arrange_cli_collision,
    copy_registry_project,
    copy_selection_fixture,
    expected_manifest,
    expected_selection,
    registry_case,
)


@pytest.fixture
def registry_project(tmp_path):
    """Copy the unchanged actual production boundary into tmp_path."""
    copy_registry_project(tmp_path)
    return tmp_path


@pytest.fixture
def registry_literal_case(registry_project):
    """Arrange literal inputs for the external uv delegation boundary."""
    return registry_case(registry_project, "record")


@pytest.fixture
def registry_missing_case(registry_project):
    """Arrange omitted inputs for the actual repository CLI."""
    return registry_case(registry_project, "delegate")


@pytest.fixture
def prepared_selection(tmp_path):
    return copy_selection_fixture(tmp_path, "accepted")


@pytest.fixture
def selection_expected():
    return expected_selection()


@pytest.fixture
def manifest_expected():
    return expected_manifest()


@pytest.fixture
def changed_selection(request, prepared_selection):
    arrange_changed_input(prepared_selection, request.param)
    return prepared_selection


@pytest.fixture
def unsupported_selection(request, tmp_path):
    return copy_selection_fixture(tmp_path, request.param)


@pytest.fixture
def cli_missing_record(prepared_selection):
    return replace(
        prepared_selection, record=prepared_selection.directory / "absent.json"
    )


@pytest.fixture
def cli_existing_destination(prepared_selection):
    arrange_cli_collision(prepared_selection)
    return prepared_selection


@pytest.fixture
def cli_cache_destination(prepared_selection):
    return replace(
        prepared_selection, destination=prepared_selection.cache / "forbidden"
    )


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
