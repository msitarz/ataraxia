# SPDX-License-Identifier: Apache-2.0
"""Codex quota version acceptance boundaries."""

import pytest

from script.eval.runner.adapters.codex_version import supports_quota_version


@pytest.mark.parametrize(
    ("version", "supported"),
    [
        ("0.163.9", False),
        ("0.164.0", True),
        ("codex-cli 0.164.0", True),
        ("codex-cli 0.165.0", True),
        ("1.0.0", True),
        ("0.164.0-rc.1", False),
        ("codex-cli 0.164.0+build", False),
        ("0.164", False),
        ("0.0164.0", False),
        (" 0.164.0", False),
        (None, False),
    ],
)
def test_quota_version(version: str | None, supported: bool) -> None:
    assert supports_quota_version(version) is supported
