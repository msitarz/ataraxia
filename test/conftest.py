# SPDX-License-Identifier: Apache-2.0
"""Shared temporary arrangements for registry process tests."""

from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from test.support import (
    ROOT,
    ChangingRecordRead,
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
        ROOT / "test/fixtures/registry_selection/unapproved.json",
        Path.read_bytes,
    )
    with patch.object(Path, "read_bytes", autospec=True, side_effect=edge.read):
        yield edge
