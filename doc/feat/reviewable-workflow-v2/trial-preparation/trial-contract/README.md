# Trial contract

Give the [Live trial](../../live-trial/README.md) observable acceptance and a
bounded decision about whether the workflow is useful in practice.

Its current README describes activities, retains wording about replacing
guidance, and fails `ac-check` because it has no acceptance declarations. It
names parallel shard execution without specifying its behavioral contract or
performance comparison. Five-minute individual reviews alone cannot establish
that total maintainer effort is acceptable.

Deliver [Completion evidence](../completion-evidence/README.md) and
[Handoff recovery](../handoff-recovery/README.md) first. Revise the live-trial
contract to exercise those outcomes, fresh-agent context discovery, delegated
implementation, independent review, and maintainer review. Separate workflow
evaluation from the parallel feature's implementation contract so each delivery
has a reviewable outcome.

## Acceptance

- **AC-1 DONE** The live-trial contract defines observable completion criteria,
  evidence methods, scope, and a final adoption or adjustment decision; its
  acceptance declarations pass `ac-check` before trial execution.
  Verification: inspect the revised contract and run its declaration check,
  distinguishing declared methods from trial results not yet observed.
- **AC-2 DONE** The trial defines a bounded observation set and success or
  reconsideration thresholds before execution for review duration, total
  maintainer time, interventions, correction rounds, and delegation cost where
  usage data is available. It states how unavailable cost data is reported.
  Verification: review the measurement protocol and thresholds against example
  outcomes, including short reviews with excessive total effort. Confirm the
  results fit in existing PR evidence without per-revision journals.
- **AC-3 DONE** The trial exercises Luna at low effort and specifies how
  observed correction cost or stalled work informs an escalation recommendation,
  while preserving maintainer approval for model or reasoning changes.
  Verification: inspect the trial scenarios against handoff recovery and walk
  through a successful handoff and a stalled correction loop.
- **AC-4 DONE** Before parallel shard implementation, its own reviewed contract
  specifies preserved results, ordering, strategy loading and isolation, error
  and cleanup behavior, sequential compatibility, and a representative workload
  with baseline, measurement method, and performance threshold. An experimental
  branch is comparison evidence rather than an approved implementation.
  Verification: inspect the trial's feature-contract prerequisite and its
  reviewable delivery boundaries; confirm it requires the contract before
  implementation without choosing those product behaviors in this Work.

The trial starts only after the preparation parent is complete and integrated.
This child defines evaluation; the trial supplies its actual results.
