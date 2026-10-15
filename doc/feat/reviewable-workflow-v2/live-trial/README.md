# Live trial

## Purpose

Determine whether the delivered reviewable workflow supports useful delivery
with acceptable total maintainer effort.

## Goals

- Observe bounded delivery, fresh-agent context discovery, and delegated
  handoffs under a reviewed protocol.
- Support an explicit adoption or revision decision and a familiar-feature
  exercise after adoption.

## Non-Goals

- Replace workflow guidance as an ongoing trial activity.
- Approve parallel shard behavior or adopt the experimental branch by
  comparison alone.

## Acceptance criteria

### **AC-1 TODO** Delivered-workflow observations support assessment

Delivery through this Work hierarchy and small PRs to `master` produces
observations against the trial's reviewed scope, protocol, and thresholds.
Observations cover complete artifact review effort, fresh agents finding the
context they need, delegated implementation, independent agent review, and
maintainer review. Short individual reviews alone do not establish acceptable
total maintainer effort. The protocol and frozen conditions follow
[empirical evaluation guidance](../../../evaluation.md); deviations remain
visible rather than silently changing the trial conditions.

### **AC-2 TODO** The maintainer can decide adoption or revision

Trial findings assess success, overhead, drift, and inconclusive results against
the declared thresholds and support a maintainer adoption or revision decision.
Recommended workflow changes follow the existing review and decision gates;
evaluation completion does not itself adopt policy.

### **AC-3 TODO** Adoption is exercised on a familiar feature

After adoption and approval of its own behavioral and performance contract,
parallel shard execution exercises the workflow from a `master`-based branch.
Delivered behavior is compared with the experimental parallel branch as
comparison evidence, without assuming that branch's implementation is approved.
The feature's implementation and performance outcomes belong to its own
reviewed contract, separately from this workflow evaluation.

## Dependencies

- [Trial preparation](../trial-preparation/README.md): must be delivered and
  integrated into `master` before the trial starts, including the reviewed trial
  definition and measurement protocol owned by its
  [Trial contract](../trial-preparation/trial-contract/README.md) child.

## Additional context

Execution is **BLOCKED**: the trial definition, bounded observation set,
measurement methods, thresholds, and parallel-feature prerequisites remain
pending under Trial contract. Execution waits for the reviewed trial definition
and preparation integrated into `master`.
