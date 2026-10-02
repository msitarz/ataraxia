# Trial preparation

Make the current workflow ready for an observable live trial. The review found
gaps in acceptance evidence, handoff recovery, guidance consistency, acceptance
tool scope, and CI feedback. Address them before starting the
[Live trial](../live-trial/README.md).

At review time, the acceptance checker validated declarations rather than
completed outcomes, and completion deleted the contract its tools required.
Handoffs had no defined return or recovery procedure. Decision statuses and
entry-point instructions disagreed. Acceptance tools omitted example tests, and
CI delayed the main tests behind the network audit and repeated preparation
across jobs. The live trial lacked acceptance declarations and measurable
success criteria.

## Works

- **DONE** Completion evidence: verified per-criterion outcomes are recorded
  with the retained Work commit; removal and parent update are separate.
- **DONE** Handoff recovery: added return evidence, interrupted-session
  recovery, and scope-growth and stalled-correction stopping rules to
  [orchestrator guidance](../../../orchestrator.md); rationale is recorded in
  [WDR 10](../../../wdr/0010-recover-delegated-handoffs.md).
- **TODO** [Guidance consistency](guidance-consistency/README.md): reconcile
  decision status, contract authority, and contributor examples.
- **DONE** Acceptance tool scope: added support for
  Work tests under both `test/` and `example/` consistently.
- **DONE** CI scheduling: made the main test job independent of static checks
  and the network audit while preserving the full CI gate.
- **TODO** [CI preparation](ci-preparation/README.md): restore criterion tracing
  for automated Make regressions and record the selected-test evidence.
- **TODO** [Trial contract](trial-contract/README.md): define the trial's
  acceptance, total effort measurements, and parallel-feature preparation.
- **TODO** [Workflow efficiency](workflow-efficiency/README.md): use a bounded
  comparison to refine handoffs, PR evidence, and workspace preparation.

Each child owns a separate review outcome. Complete the trial contract after
completion evidence and handoff recovery so it exercises the delivered rules.
CI scheduling and CI preparation share files; deliver scheduling first to keep
their changes independently reviewable.

## Acceptance

Acceptance criteria remain `TODO` until their outcomes are verified. The
Verification annotations below describe planned checks; passing a declaration
check does not establish completion. Record actual results in the delivery PR.

- **AC-1 TODO** Every child outcome is integrated into `master`, with its
  acceptance results available in its delivery PR and lasting contracts in
  their owners.
  Verification: review the integrated child outcomes and their delivery PRs
  against the map above before closing this parent Work.
- **AC-2 TODO** The live trial has a usable acceptance contract and explicitly
  depends on this preparation; it has not started before preparation completes.
  Verification: inspect the live-trial contract, run its declaration check,
  and verify the dependency against integrated parent status.
- **AC-3 TODO** The preparation addresses all review findings: trial acceptance,
  completion evidence, recovery, decision status, contract authority, CI
  scheduling and setup, example-test tracing, delegation cost, total maintainer
  effort, and misleading contributor instructions.
  Verification: map each finding to the delivered child outcome or to an
  explicit measurement and decision in the live-trial contract.

This Work prepares the trial; it does not implement parallel shard execution or
claim that the workflow's efficiency has already been demonstrated. Preserve
independent agent review, maintainer approval and merge control, full CI gates,
and the existing approval requirement for delegation changes. Consequential
policy changes belong in [WDRs](../../../wdr-workflow.md), with proposed choices
distinguished from accepted ones.
