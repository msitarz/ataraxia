# Reviewable workflow

Build a delivery workflow around bounded Works that the maintainer can inspect,
discuss, and steer. See
[Work lifecycle and contracts](../../workflow.md) for Work directories, local
contracts, child discovery, status, and lifecycle.

## Works

- **DONE** Guidance and routing — moved rules to their owners and routed
  agents by task.
- **DONE** Work structure and review — established permanent Work contracts,
  lifecycle, prototype, and PR review rules.
- **DONE** Focused guidance — established focused owners and direct routes for
  change and validation rules.
- **DONE** Validation — focused preparation and full-CI merge gates live in
  the [validation policy](../../validation.md); Work acceptance coverage is
  owned by [acceptance tracing](../../acceptance-tracing.md).
- **TODO** [Live trial](live-trial/README.md): use this workflow during its own
  delivery, then apply it to a familiar feature.
- **DONE** Retire the feat-slice workflow — removed unused legacy routes and
  session roles after confirming no legacy slices remained outside this Work;
  retained ADR/WDR history and the distinct trading Feature term.
- **DONE** Workflow Decision Records — established eligibility and shared
  record policy, with an initial retrospective set in the
  [WDR index](../../wdr/README.md).
- **DONE** Orchestrator handoffs — established role-triggered Luna change
  delegation, review corrections, and maintainer gates in
  [orchestrator guidance](../../orchestrator.md).
- **DONE** Handoff scope growth — added a stop-and-split rule for delegated
  scope in [orchestrator guidance](../../orchestrator.md).
- **DONE** Human review effort — sized Works around the complete change and
  added expected-scope and actual-diff review checkpoints for orchestrators.
- **DONE** Function-size guardrails — added advisory and blocking Ruff
  statement-count checks to the existing Make lint workflows.
