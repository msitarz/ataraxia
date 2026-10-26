# SPDX-License-Identifier: Apache-2.0
"""Historical package-export proposal; the active API is ``script.eval.runner``.

These sketch exports record the future composition boundary. The declared
``Coordinator`` remains planned and is not part of the current runtime package;
the actual ``script/eval/runner/__init__.py`` exports only implemented APIs.
"""

from .coordinator import Coordinator
from .ports import (
    AttemptCall,
    AttemptRequestBuilder,
    BoundRun,
    CliBinding,
    CliBindingResolver,
    EffectiveCall,
    OutcomeClassifier,
    ProgressSink,
    QuotaStatusReader,
    Runtime,
)

__all__ = (
    "AttemptCall",
    "AttemptRequestBuilder",
    "BoundRun",
    "CliBinding",
    "CliBindingResolver",
    "Coordinator",
    "EffectiveCall",
    "OutcomeClassifier",
    "ProgressSink",
    "QuotaStatusReader",
    "Runtime",
)
