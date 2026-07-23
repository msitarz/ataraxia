# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz

from ataraxia.source import SourceRunner


def test_source_runner():
    """Should return"""

    sr = SourceRunner[int]()

    sr.item = 1

    assert sr() == 1
