# SPDX-License-Identifier: Apache-2.0
"""Marker declarations for a selected and a different Work."""

import pytest


@pytest.mark.covers(work="doc/example/README.md", ac="AC-1")
def test_declares_selected_work_marker() -> None:
    pass


@pytest.mark.covers(work="doc/other/README.md", ac="AC-99")
def test_declares_other_work_marker() -> None:
    pass
