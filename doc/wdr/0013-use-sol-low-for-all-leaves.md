# 13. Use Sol-low for all leaves

Date: 2026-10-03

## Status

Accepted

Amends
[4. Delegate repository changes for independent review](0004-delegate-repository-changes-for-independent-review.md)
for model choice,
[12. Orchestrate Work trees by responsibility](0012-orchestrate-work-trees-by-responsibility.md)
for leaf identity, and
[5. Review completed handoffs once](0005-review-completed-handoffs-once.md)
for executor naming only. Low effort, direct execution, ownership, independent
review, consolidated same-session corrections, and maintainer approval rules
remain in force.

Amended by
[20. Route agents by responsibility](0020-route-agents-by-responsibility.md).

## Context

The bounded leaf-agent comparison in
[PR 122](https://github.com/msitarz/ataraxia/pull/122) recorded 18 final
artifacts passing their required gates. Sol-low had three initial accepts per
fixture and no corrections; its median dispatch-to-final-review times were 77
seconds for documentation and 201 seconds for code, versus Luna-low's 90 and 375
seconds. Documentation missed the declared improvement thresholds. Code
qualified numerically, but indexed reference exposure and a prompt/rubric
mismatch made comparative effectiveness uncertain. Three runs per condition and
task, sequential ordering, an unblinded reviewer, and unavailable active effort,
human-review time, tokens, and cost further limit interpretation. The
[immutable results](https://github.com/msitarz/ataraxia/blob/d79a39c45961fd3d58519572a45ccbeae707d443/doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/leaf-agent-selection/controlled-comparison/results.md)
recommend retaining Luna-low and a repaired, broader coding comparison.

The maintainer explicitly overrides that recommendation and selects Sol-low
for every leaf as a policy judgment. This decision does not claim conclusive
global superiority or revise the original measurements and conclusions.

## Decision

Use the leaf model and effort defined in
[orchestrator guidance](../orchestrator.md): GPT-6.1 Sol at low reasoning
effort. This applies to all leaves, including Investigations and empirical
evaluations. Each leaf executes its bounded changes directly in an isolated
worktree; its owning parent independently reviews the artifact and evidence. Any
other model or effort needs explicit maintainer approval. If Sol is unavailable,
report and wait without silent substitution or orchestrator implementation as
fallback.

Keep the direct parent-to-leaf topology, context recovery, consolidated
corrections in the same executor session, scope and human-review gates,
maintainer merge control, and full CI requirement. This changes no orchestrator
model selection. Frozen experimental protocols retain their declared conditions
and require review/alignment or explicit authorization before execution.

## Consequences

All leaves use one selected executor instead of retaining
Luna-low or varying models by task class. Retaining Luna-low would follow the
comparison's recommendation; task-specific selection or another comparison
would seek more evidence but add selection or evaluation work. The maintainer
chooses a uniform executor while retaining independent review to assess each
actual result. Cost and broad comparative effectiveness remain unknown.

Current procedure remains with orchestrator guidance. The
[WDR workflow](../wdr-workflow.md) and
[decision-record format](../decision-records.md) retain eligibility, status,
and lifecycle ownership. The delivery has its own
[Work contract](https://github.com/msitarz/ataraxia/blob/744e205907c10eab38997fcda40c38a815b1cea8/doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/leaf-agent-policy/README.md);
the existing trial evidence and cleanup commits remain preserved.
