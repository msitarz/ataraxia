# Trial contract

Give the [Live trial](../../live-trial/README.md) observable acceptance criteria
and a bounded decision about whether the workflow is useful in practice.

Its current README describes activities, lacks acceptance declarations, and
retains wording about replacing guidance. It names parallel shard execution
without specifying its behavioral contract or performance comparison.
Five-minute individual reviews alone cannot establish that total maintainer
effort is acceptable.

Deliver [completion evidence and handoff recovery](../README.md#works) first.
Revise the live-trial contract to exercise those outcomes, fresh-agent context
discovery, delegated implementation, independent review, and maintainer review.
Separate workflow evaluation from the parallel feature's implementation contract
so each delivery has a reviewable outcome.

## Acceptance

- **AC-1 TODO** The live-trial contract defines observable acceptance criteria,
  evidence methods, scope, and a final adoption or adjustment decision. Review
  these declarations against the Work contract template before trial
  execution, distinguishing planned evidence methods from trial evidence not
  yet observed.
- **AC-2 TODO** The trial defines a bounded observation set and success or
  reconsideration thresholds before execution for review duration, total
  maintainer time, interventions, correction rounds, and delegation cost where
  usage data is available. It states how unavailable cost data is reported.
  Validation: review the measurement protocol and thresholds against example
  outcomes, including short reviews with excessive total effort. Confirm the
  evidence fits in existing PR records without per-revision journals.
- **AC-3 TODO** The trial exercises the default leaf executor from
  [orchestrator guidance](../../../../orchestrator.md) and specifies how
  observed correction cost or stalled work informs an escalation recommendation,
  while preserving maintainer approval for model or reasoning changes.
  Validation: inspect the trial scenarios against handoff recovery and walk
  through a successful handoff and a stalled correction loop.
- **AC-4 TODO** Before parallel shard implementation, its own reviewed contract
  specifies preserved results, ordering, strategy loading and isolation, error
  and cleanup behavior, sequential compatibility, and a representative workload
  with baseline, measurement method, and performance threshold. An experimental
  branch is comparison evidence rather than an approved implementation.
  Validation: inspect the trial's feature-contract prerequisite and its
  reviewable delivery boundaries; confirm it requires the contract before
  implementation without choosing those product behaviors in this Work.

The trial starts only after the preparation parent is complete and integrated.
This child defines evaluation; the trial supplies its observed evidence.

The workflow-efficiency comparison was abandoned at maintainer request;
[historical observations](https://github.com/msitarz/ataraxia/blob/ea784d4dbf02a87486842a2012ca9da852b94379/doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/README.md)
remain bounded input, without a completed comparison or topology-speedup claim.
This trial owns its own declared measurements and evidence; it cannot inherit
completion from those observations.
