# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Minimal import-file fixture exposing one literal Bar."""

from ataraxia.bar import Bar


def new_bar() -> Bar:
    """Return a Bar whose six fields are all one."""
    return Bar(timestamp=1, open=1, high=1, low=1, close=1, volume=1)
