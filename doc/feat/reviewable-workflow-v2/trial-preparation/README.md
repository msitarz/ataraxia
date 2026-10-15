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
- **DONE** Guidance consistency: aligned WDR status and index, clarified
  accepted-contract authority, and corrected Make and contributor guidance.
- **DONE** Acceptance tool scope: added support for
  Work tests under both `test/` and `example/` consistently.
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

Each child owns a separate review outcome. Complete the trial contract after
completion evidence, handoff recovery, and Make Work reminders so it exercises
the delivered rules. Complete executor guidance and handoffs and definer
guidance before the live trial begins. CI scheduling and CI preparation share
files; deliver scheduling first to keep their changes independently reviewable.

## Acceptance

Acceptance criteria remain `TODO` until their outcomes are verified. The
Validation annotations below describe planned checks; passing a declaration
check does not establish completion. Record observed evidence in the delivery
PR.

- **AC-1 TODO** Every child is integrated into `master` or explicitly abandoned
  at maintainer request, with delivered acceptance evidence in its PR and
  lasting contracts in their owners. Abandonment does not establish the
  unfinished outcome.
  Validation: review integrated outcomes, their delivery PRs and explicit
  abandonment records against the map above before closing this parent Work.
- **AC-2 TODO** The live trial has a usable acceptance contract and explicitly
  depends on this preparation; it has not started before preparation completes.
  Review the live-trial contract against the Work contract template and verify
  the dependency against integrated parent status.
- **AC-3 TODO** The preparation addresses all review findings: trial acceptance,
  completion evidence, recovery, decision status, contract authority, CI
  scheduling and setup, example-test tracing, delegation cost, total maintainer
  effort, and misleading contributor instructions.
  Validation: map each finding to the delivered child outcome or to an
  explicit measurement and decision in the live-trial contract, including the
  scope-sizing and handoff reminder gap identified during delivery.

This Work prepares the trial; it does not implement parallel shard execution or
claim that the workflow's efficiency has already been demonstrated. Preserve
independent agent review, maintainer approval and merge control, full CI gates,
and the existing approval requirement for delegation changes. Consequential
policy changes belong in [WDRs](../../../wdr-workflow.md), following the shared
[decision-record lifecycle](../../../decision-records.md#record-format).
