# SPDX-License-Identifier: Apache-2.0
"""Exploratory quota recovery and probe lifecycle input design.

Pure transitions consume explicit time and observations; the async owner polls.
Private helper signatures are intentionally left open for implementation.
"""

from dataclasses import dataclass
from typing import Literal

from script.eval.model import QuotaProbeRequest

@dataclass(frozen=True)
class ProbePrepared:
    """Durable intent before the final dispatch gate; no process is claimed."""

    request: QuotaProbeRequest

@dataclass(frozen=True)
class ProbeNotDispatched:
    """Close a prepared probe without a process or probe-budget charge."""

    request: QuotaProbeRequest
    cause: Literal["bound", "stop", "cancelled"]

@dataclass(frozen=True)
class ProbeDispatched:
    """Record an actual poll invocation, never preparation alone."""

    request: QuotaProbeRequest

type ProbeDispatchEvent = ProbePrepared | ProbeNotDispatched | ProbeDispatched
