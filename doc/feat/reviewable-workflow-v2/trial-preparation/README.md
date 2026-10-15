# Trial preparation

## Purpose

Make the delivered workflow ready for an observable live trial by resolving the
review's preparation gaps.

## Goals

- Integrate the preparation outcomes or record explicit maintainer abandonment.
- Give the live trial a reviewed contract and protocol before execution.
- Account for every review finding through delivered outcomes or explicit trial
  measurements and decisions.

## Non-Goals

- Implement parallel shard execution or demonstrate workflow efficiency.
- Start the live trial before preparation is complete and integrated.

## Acceptance criteria

### **AC-1 TODO** Preparation children have an integrated disposition

Every child is integrated into `master` or explicitly abandoned at maintainer
request, with delivered acceptance evidence in its PR and lasting contracts in
their owners. Abandonment records identify unfinished outcomes and do not
establish their completion.

### **AC-2 TODO** The live trial has a usable contract before execution

The [Live trial](../live-trial/README.md) has a reviewed acceptance contract and
protocol supplied by Trial contract, with an explicit dependency on this
preparation's completion and integration into `master`. The trial has not
started before that gate is met.

### **AC-3 TODO** All review findings have an explicit disposition

Delivered child outcomes or explicit trial measurements and decisions address
trial acceptance, completion evidence, handoff recovery, decision status,
contract authority, CI scheduling and setup, example-test tracing, delegation
cost, total maintainer effort, misleading contributor instructions, and the
scope-sizing and handoff reminder gap found during delivery. The disposition
distinguishes delivered repairs, retired tooling, abandoned outcomes, and
questions left for the trial; missing measurements are not claimed as results.

## Children

- **DONE** Completion evidence: verified per-criterion outcomes are recorded
  with the retained Work commit; removal and parent update are separate.
- **DONE** Handoff recovery: added return evidence, interrupted-session
  recovery, and scope-growth and stalled-correction stopping rules to
  [orchestrator guidance](../../../orchestrator.md); rationale is recorded in
  [WDR 10](../../../wdr/0010-recover-delegated-handoffs.md).
- **DONE** Guidance consistency: aligned WDR status and index, clarified
  accepted-contract authority, and corrected Make and contributor guidance.
- **DONE** Acceptance tool scope: added support for
  Work tests under both `test/` and `example/` consistently in the subsequently
  retired acceptance tooling.
- **DONE** CI scheduling: made the main test job independent of static checks
  and the network audit while preserving the full CI gate.
- **DONE** CI preparation: measured and reduced unused CI setup work, prepared
  the package job's managed Python from `.python-version` before offline smoke
  checks, and traced Make regressions to their acceptance criteria.
- **DONE** Delivered Make Work reminders for pre-dispatch review sizing and
  post-cleanup reviewed PR delivery to the maintainer.
- **DONE** Executor guidance and handoffs: added direct executor role discovery
  and contextual assignments with role-specific returns.
- **DONE** Definer guidance: added a focused role owner and direct routes while
  preserving contract-writing policy and review boundaries.
- **TODO** [Trial contract](trial-contract/README.md): define the trial's
  acceptance, total effort measurements, and parallel-feature preparation.
- **ABORT** Workflow efficiency: delivered guidance and decisions remain in
  [their owners](../../../orchestrator.md) and the
  [historical outcome map](https://github.com/msitarz/ataraxia/blob/ea784d4dbf02a87486842a2012ca9da852b94379/doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/README.md).
  Bounded isolation findings and delivery evidence are preserved as
  [managed-sandbox inputs](../../evaluation-sandboxes/isolation-input.md).
  The maintainer abandoned the remaining comparative outcomes and the entire
  residual tree; this is not completion of the unfinished comparison.

## Additional context

At review time, the acceptance checker validated declarations rather than
completed outcomes, and completion deleted the contract its tools required.
Handoffs lacked return and recovery procedures; decision statuses and entry
points disagreed. Acceptance tools omitted example tests, and CI delayed main
tests behind the network audit and repeated preparation. These are historical
findings, not assertions that those mechanisms remain current. The live trial's
measurement definition remains pending under Trial contract.

The trial preserves the review and delegation approval boundaries in
[orchestrator guidance](../../../orchestrator.md), maintainer merge control in
[contributor guidance](../../../../CONTRIBUTING.md#work-branches-review-and-merge),
and CI gates in the [check and evidence policy](../../../validation.md).
Consequential policy changes belong in [WDRs](../../../wdr-workflow.md),
following the shared
[decision-record lifecycle](../../../decision-records.md#record-format).
