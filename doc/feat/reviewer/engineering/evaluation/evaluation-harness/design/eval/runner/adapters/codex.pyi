# SPDX-License-Identifier: Apache-2.0
"""Historical Codex adapter signature sketch; runtime code is authoritative.

The signatures remain a record of the reviewed public port shape. See
``script/eval/runner/adapters/codex.py`` for the current typed wiring skeleton;
its external-operation leaves and Codex behavior are not implemented yet.
"""

from ...model import (  # ruff: ignore[relative-imports]
    AttemptEvidence,
    FrozenPlan,
    HarnessConfig,
    PlannedCall,
    PreparedEvidence,
    RetryAssessment,
)
from ..ports import (  # ruff: ignore[relative-imports]
    AttemptRequestBuilder,
    CliBinding,
    CliBindingResolver,
    EffectiveCall,
    OutcomeClassifier,
)

class CodexCliBindingResolver(CliBindingResolver):
    """Resolve CLI identity and a quota scope only when its identity is verified."""

    def resolve(self, config: HarnessConfig, /) -> CliBinding: ...

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
