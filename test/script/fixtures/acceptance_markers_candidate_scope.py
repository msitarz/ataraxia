# SPDX-License-Identifier: Apache-2.0
"""Marker declarations in supported and unsupported static candidates."""

import pytest

unused_marker = pytest.mark.covers(work="doc/example/README.md", ac="AC-2")


@pytest.mark.covers(work="doc/example/README.md", ac="AC-2")
def helper_with_marker() -> None:
    pass


def test_declares_body_marker_call() -> None:
    pytest.mark.covers(work="doc/example/README.md", ac="AC-2")


class TestMarkerMethods:
    @pytest.mark.covers(work="doc/example/README.md", ac="AC-2")
    def helper_with_marker(self) -> None:
        pass


@pytest.mark.covers(work="doc/example/README.md", ac="AC-1")
def test_declares_supported_marker_candidate() -> None:
    pass
