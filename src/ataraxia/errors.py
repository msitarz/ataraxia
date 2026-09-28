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


class ProviderError(AtaraxiaError):
    """Provider error."""

    pass


class FeatureError(AtaraxiaError, ValueError):
    """Feature error."""

    pass


class ModuleError(AtaraxiaError, ImportError):
    """Error while importing a module."""

    pass


class BacktestError(AtaraxiaError, ValueError):
    """Error while running a backtest."""

    pass


class DependencyError(AtaraxiaError, TypeError):
    """Dependency names do not match the runner call signature."""


class ShardTimeoutError(AtaraxiaError, TimeoutError):
    """A supervised shard assignment exceeded its wall-clock deadline."""


class WorkerFailureError(AtaraxiaError, RuntimeError):
    """An executor worker did not deliver a valid shard outcome."""


class SupervisorError(AtaraxiaError, RuntimeError):
    """The orchestrator could not preserve its lifecycle invariants."""
