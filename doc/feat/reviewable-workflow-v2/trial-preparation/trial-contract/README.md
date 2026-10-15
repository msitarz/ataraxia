# Trial contract

## Purpose

Give the live trial a reviewed definition that can determine whether the
workflow is useful in practice.

## Goals

- Define observable trial outcomes and a bounded adoption or revision decision.
- Establish measurements and thresholds for total effort before execution.
- Separate workflow evaluation from parallel shard implementation requirements.

## Non-Goals

- Execute the trial or claim workflow efficiency from existing observations.
- Choose parallel shard product behavior or approve the experimental branch.

## Acceptance criteria

### **AC-1 TODO** A usable live-trial definition supports a bounded decision

The [Live trial](../../live-trial/README.md) contract defines observable
acceptance criteria, scope, evidence methods, and a final adoption or adjustment
decision. It evaluates the delivered workflow rather than authorizing ongoing
guidance replacement. Planned methods remain distinct from trial evidence not
yet observed; workflow evaluation and the familiar feature's implementation
have separate reviewable outcomes.

### **AC-2 TODO** A declared protocol measures total effort

Before execution, the trial has a bounded observation set and success or
reconsideration thresholds for review duration, total maintainer time,
interventions, correction rounds, and delegation cost where usage data is
available. Unavailable cost data has an explicit reporting treatment without an
invented estimate or cost claim. The protocol follows
[empirical evaluation guidance](../../../../evaluation.md), including frozen
conditions and inconclusive-result handling. Its decision rules account for
short reviews with excessive total effort, and its evidence fits existing PR
records without per-revision journals.

### **AC-3 TODO** Delegated scenarios preserve escalation approval

The trial exercises the default leaf executor from
[orchestrator guidance](../../../../orchestrator.md), completion evidence,
handoff recovery, fresh-agent context discovery, independent review, and
maintainer review. Its scenarios cover a successful handoff and a stalled
correction loop, specifying how observed correction cost or stalled work informs
an escalation recommendation while preserving maintainer approval for model or
reasoning-effort changes.

### **AC-4 TODO** Parallel implementation has a reviewed prerequisite

The trial requires parallel shard execution's own reviewed contract before
implementation. That contract specifies preserved results, ordering, strategy
loading and isolation, error and cleanup behavior, sequential compatibility,
and a representative workload with baseline, measurement method, and
performance threshold. Reviewable feature-delivery boundaries are explicit;
this Work requires those definitions without choosing product behaviors. An
experimental branch remains comparison evidence rather than an approved
implementation.

## Dependencies

- Delivered [completion evidence, handoff recovery, and Make Work
  reminders](../README.md#children): the trial definition exercises these
  preparation outcomes after their delivery.

## Links

- [Live trial](../../live-trial/README.md): consumes this definition after
  preparation is complete and integrated into `master`.

## Additional context

The trial's measurement protocol, thresholds, and parallel-feature prerequisites
are still pending. Five-minute individual reviews alone cannot establish
acceptable total maintainer effort.

This child defines evaluation; the live trial supplies its observed evidence.
The workflow-efficiency comparison was abandoned at maintainer request;
[historical observations](https://github.com/msitarz/ataraxia/blob/ea784d4dbf02a87486842a2012ca9da852b94379/doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/README.md)
remain bounded input, without a completed comparison or topology-speedup claim.
This trial owns its declared measurements and evidence and cannot inherit
completion from those observations.
