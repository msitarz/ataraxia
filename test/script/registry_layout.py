# SPDX-License-Identifier: Apache-2.0
"""Own the literal package arrangement shared by registry layout consumers."""

import pytest

from script.registry_selection import Package


@pytest.fixture
def literal_package() -> Package:
    """Provide the canonical package value shared with payload consumers."""
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
