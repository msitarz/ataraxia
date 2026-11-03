# SPDX-License-Identifier: Apache-2.0
"""Synthetic retained evidence for command acceptance tests."""

from pathlib import Path

import pytest

from test.script.integration.reviewer_eval.support import create_run


@pytest.fixture
async def saved_run(tmp_path: Path) -> Path:
    """Create a synthetic harness run with a real evidence store."""
    root = tmp_path / "run"
    await create_run(root)
    return root
