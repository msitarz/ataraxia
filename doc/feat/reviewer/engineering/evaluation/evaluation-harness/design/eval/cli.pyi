# SPDX-License-Identifier: Apache-2.0
"""CLI options, help text, and one-time adapter composition root.

Help explains that ``--instructions-file`` maps to the native Codex setting
``-c model_instructions_file=PATH``.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from .evidence import EvidenceStore
from .inputs import RepositoryReader
from .model import DryRunReport, HarnessConfig, RunRecord
from .plan import PlanBuilder
from .runner import (
    AttemptRequestBuilder,
    CliBindingResolver,
    Coordinator,
)
from .tokens import TokenEstimator

def parse_config(argv: Sequence[str], /) -> HarnessConfig:
    """Parse ordered CLI options and validate settings without side effects."""
    ...

@dataclass(frozen=True)
class Composition:
    """Concrete adapters assembled once by the CLI entry point."""

    repository: RepositoryReader
    planner: PlanBuilder
    estimator: TokenEstimator
    binding_resolver: CliBindingResolver
    request_builder: AttemptRequestBuilder
    coordinator: Coordinator
    evidence: EvidenceStore

    async def execute(self, config: HarnessConfig, /) -> DryRunReport | RunRecord:
        """Plan and estimate, or persist frozen inputs before execution."""
        ...

async def main(argv: Sequence[str] | None = None, /) -> int:
    """Parse, assemble, and execute once without interactive approval prompts.

    The public command documents a stable mapping for complete success, run
    failure, cancellation, and incomplete evidence. Missing unattended CLI
    prerequisites fail explicitly. The invoking shell owns launch and liveness.
    """
    ...
