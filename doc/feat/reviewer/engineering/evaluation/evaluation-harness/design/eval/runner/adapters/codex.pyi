# SPDX-License-Identifier: Apache-2.0
"""Codex CLI binding, request, and settled-output classification adapters."""

from dataclasses import dataclass
from pathlib import Path

from script.eval.evidence import PreparedEvidence
from script.eval.runner.ports import (
    AttemptRequestBuilder,
    CliBinding,
    CliBindingResolver,
    EffectiveCall,
    OutcomeClassifier,
)

from script.eval.model import (
    AttemptEvidence,
    FrozenPlan,
    HarnessConfig,
    PlannedCall,
    RetryAssessment,
    SettingValue,
)

@dataclass(frozen=True)
class CodexCliBinding:
    """Resolved CLI identity and settings visible to the harness."""

    executable_path: Path
    cli_version: str | None
    runner_version: str
    effective_settings: tuple[tuple[str, SettingValue], ...]

class CodexCliBindingResolver(CliBindingResolver):
    """Resolve executable, CLI version, and observable effective settings."""

    def resolve(self, config: HarnessConfig, /) -> CodexCliBinding: ...

class CodexAttemptRequestBuilder(AttemptRequestBuilder):
    """Build a fresh request from frozen plan bytes and the staged instruction."""

    def build(
        self,
        plan: FrozenPlan,
        call: PlannedCall,
        binding: CliBinding,
        evidence: PreparedEvidence,
        config: HarnessConfig,
        /,
    ) -> EffectiveCall: ...

class CodexOutcomeClassifier(OutcomeClassifier):
    """Classify only captured post-settlement stdout JSONL and raw stderr.

    No streaming assumption or answer parsing is permitted. Until a Codex
    signal and no-result basis are verified from direct evidence, ambiguous or
    unsupported observations return an unknown RetryAssessment.
    """

    def assess(self, evidence: AttemptEvidence, /) -> RetryAssessment: ...
