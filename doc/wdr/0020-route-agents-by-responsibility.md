# 20. Route agents by responsibility

Date: 2026-10-10

## Status

Accepted

Amends [13. Use Sol-low for all leaves](0013-use-sol-low-for-all-leaves.md).

## Context

The maintainer selects separate contract-definition and implementation roles in
[the policy Work](https://github.com/msitarz/ataraxia/blob/bfaa3ce48a87d7e015c06cb56729f9ec94911c80/doc/feat/agent-responsibilities/policy/README.md),
replacing WDR 13's uniform leaf-model selection. Independent review of actual
contracts and artifacts remains the quality gate. This is maintainer judgment,
not a new comparison: WDR 13's historical observations, limitations, and
original recommendation remain intact. Cost and comparative superiority remain
unknown.

## Decision

Route by responsibility under [orchestrator guidance](../orchestrator.md):
Definer uses GPT-6.1 Sol at medium effort for Work contract definition;
Executor, Cleaner, and Publisher use GPT-6 Luna at medium effort for their
bounded roles. Explicit maintainer task-specific overrides remain permitted.
Definition and execution in Investigations and Evaluations follow these same
responsibilities. Keep definition handoffs at the orchestrator owner and
operational procedures at [cleanup](../branch-cleanup.md) and
[publication](../publisher.md) owners.

Only role/model routing changes. Preserve orchestrator model selection,
agent-creation authorization, direct parent-to-leaf topology and Work-tree
ownership, isolated worktrees, consolidated corrections, independent review,
acceptance evidence, latest-head full CI, and maintainer review and merge
control. Frozen empirical protocols retain their declared conditions and
require alignment or explicit authorization before execution.

## Consequences

Contract definition and bounded implementation have explicit independent-review
boundaries instead of one uniform leaf default. Keeping Sol-low uniformly would
avoid responsibility-based selection; the maintainer chooses this routing
without claiming a measured advantage. Shared routing stays at one owner,
while operational owners retain their checks, stops, and authority limits.
