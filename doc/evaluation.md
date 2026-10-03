# Empirical evaluations

Read when designing, running, or interpreting an empirical evaluation, whether
it is an independent Evaluation Work, supports an Investigation, or is a small
comparison kept inline. [Work workflow](workflow.md#evaluations) owns Work kinds
and lifecycle; a specific Work README and linked protocol own the experiment.

## Declare the protocol before execution

State the bounded question, conditions, budget, common quality and preservation
rubric, metrics and checks, decision thresholds, and completion conditions.
Define severity levels and how failed quality or preservation checks affect the
comparison. Declare thresholds for success, reconsideration, and inconclusive
results before seeing outcomes; do not select a winner from timing alone.

Identify frozen fixtures and revisions, guidance, tools and versions, prompts,
and permitted resource and reference access for each condition. Match tasks
across conditions; state intended differences and hold other inputs constant
where possible. Verify required isolation rather than assuming a Worktree is a
security boundary. Check reachable history, indexes, reference answers, caches,
and prior session context for unintended exposure.

Define repetitions, execution order, freshness of sessions and inputs, bounded
dispatch and correction limits, and stop handling. Specify how timeouts,
failures, interrupted runs, exhausted budgets, and contaminated runs are
retained, excluded, or rerun. Record deviations rather than silently replacing
failed observations. Use [orchestrator guidance](orchestrator.md) when
delegating; an evaluation itself does not require agents or nesting.

## Retain inspectable observations

Keep initial and final artifacts, severity findings, executor checks, parent
checks, and the provenance of reused evidence. Identify artifact revisions and
which checks apply to each. Apply [checks and evidence](validation.md) and
[acceptance tracing](acceptance-tracing.md#planned-validation-and-evidence);
planned checks and reported assertions do not establish observed outcomes.

Record timestamps and timing boundaries, including preparation, dispatch,
executor start, completed artifact, and review or PR readiness where relevant.
Distinguish elapsed time from available active time and separate preparation,
execution, correction, reporting, and review effort. State units and measurement
methods for source and test change sizes, derived sizes, and test counts; they
are different measures, not interchangeable estimates of quality or effort.
Record token use and cost when available. Leave unknown measurements unknown,
rather than estimating them from elapsed time or change size.

Disclose deviations, contamination, confounds, reviewer identity, and whether
review was blinded. For example, indexed access to a reference answer is
exposure even without a reported file read; preserve the affected observation
and limit its interpretation according to the declared stop handling. A derived
change-size measure must identify its source artifacts and calculation. Missing
cost data permits a bounded timing or quality conclusion, not a cost claim.

## Interpret and preserve evidence

Compare matched tasks; do not pool unlike workloads into a claimed speedup.
Report observations against the declared thresholds, including inconclusive
results and the limits of quality, timing, and resource measurements. Separate
empirical observations from an Investigation's recommendation and from policy
adoption through the applicable maintainer decision process. Neither a plan
merge nor Evaluation completion adopts policy or authorizes another trial.

Preserve artifacts and protocol through the existing
[Work delivery commits](acceptance-tracing.md#work-delivery-commits) and
[PR evidence procedure](pull-requests.md), promoting lasting guidance to its
owner before cleanup. Git retains removed contracts and artifacts; PR and
linked execution records retain evidence. Do not add routine per-revision
bookkeeping, mandatory templates, or a second lifecycle.
