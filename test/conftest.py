# SPDX-License-Identifier: Apache-2.0
"""Shared temporary arrangements for registry process tests."""

import pytest

from test.support import copy_registry_project, registry_case


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
