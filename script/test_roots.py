# SPDX-License-Identifier: Apache-2.0
"""Shared pytest roots used by acceptance tooling."""

from pathlib import Path

TEST_ROOTS = ("test", "example")


def existing_test_roots(root: Path) -> list[str]:
    """Return configured test roots that exist beneath the repository root."""
    return [name for name in TEST_ROOTS if (root / name).is_dir()]
