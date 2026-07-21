# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 by Michal Sitarz
"""Errors module."""

import graphlib


class AtaraxiaError(Exception):
    """Root exception class for ataraxia."""

    pass


class CycleError(AtaraxiaError, graphlib.CycleError):
    """Dependency graph cycle error."""

    pass


class PositionError(AtaraxiaError):
    """Error in Position."""

    pass
