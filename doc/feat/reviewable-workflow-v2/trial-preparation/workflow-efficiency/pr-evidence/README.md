# PR evidence

Clarify completion evidence in the
[completion-evidence owner](../../../../../acceptance-tracing.md) and
[contributor PR guidance](../../../../../../CONTRIBUTING.md#work-branches-review-and-merge).
The [workflow-efficiency parent map](../README.md#works) tracks the outcome;
[PR 108](https://github.com/msitarz/ataraxia/pull/108) is the integration
prerequisite before changing the owner. Work owns requirements; CI owns
automated results. A PR adds the problem, result, review attention, and evidence
beyond CI. The owning orchestrator prepares or updates the PR description from
the reviewed result and Luna's concise local evidence, following permanent
[orchestrator guidance](../../../../../orchestrator.md) and the mapped
[handoffs outcome](../README.md#works). Publish the description after review;
there is no separate Luna PR-writing phase. Consolidate publication, while
allowing later material corrections or accurate pending/failure updates. Avoid
fixed headings, templates, and inventories of CI jobs, commands, or hooks.

Account for every acceptance criterion. Link to the original Work by a stable
PR diff or revision reference that remains usable after its directory is
removed; include short result context where needed instead of copying each
full criterion. Avoid routine successful-check inventories; retain concise
material diagnostics and report failures, pending or unrun checks, and manual
limitations accurately. Do not remove evidence as a blanket rule.

Clarify WDR status guidance in the
[WDR workflow](../../../../../wdr-workflow.md) and
[shared decision-record format](../../../../../decision-records.md). For a PR
that adopts a workflow decision, specify `Accepted` as the intended merged
state. Readiness alone does not assert prior maintainer approval; acceptance
occurs through merge. Ship the matching index entry and any reciprocal amendment
or supersession metadata in that same PR. Use `Proposed` for an unsettled
proposal or an Investigation recommendation when its merge does not adopt the
decision. Work type alone does not determine status; a ready Investigation PR
adopts a decision only if it explicitly does so.

Define how evidence works when all criteria are covered by CI, when a criterion
requires manual judgment, and when the Work contract has been removed. This
Work depends on completion-evidence PR108 integration before changing an
evidence owner. Reconcile applicable WDR proposals through their lifecycle and
preserve accepted records without rewriting them.

## Acceptance

- **AC-1 TODO** Evidence guidance accounts for all criteria, reports failures,
  pending, unrun, and manual limitations, and gives the three cases above
  usable treatment without fixed formats or redundant inventories.
  Verification: walk through a CI-only Work, a manual criterion, and a
  removed Work contract using a completed PR.
- **AC-2 TODO** Original criteria remain reviewable through stable PR or
  revision references after Work removal, with concise result context where
  necessary and no wholesale copying requirement.
  Verification: remove a
  sample Work directory in a review scenario and follow its references.
- **AC-3 TODO** The owner change follows integrated completion-evidence PR108
  and reconciles applicable WDRs through their lifecycle, preserving accepted
  history.
  Verification: check `master` integration and inspect the
  resulting owner and decision-record history.
- **AC-4 TODO** The WDR and shared-record owners distinguish an adoption-ready
  decision PR from a proposal-only or Investigation case, including intended
  `Accepted` state on merge, maintainer acceptance through merge, and the rule
  that Work type alone does not set status. The index and reciprocal amendment
  or supersession metadata are consistent in the same PR, without follow-up.
  Verification: review an adoption-ready PR after merge and a proposal-only or
  Investigation case, checking record status, index, reciprocal metadata, and
  the relevant owner guidance.
- **AC-5 TODO** PR-description ownership stays with the owning orchestrator
  after review for both a new PR and an existing-PR amendment, with no separate
  executor PR-writing phase. It uses Luna's concise evidence without
  duplicating routine check inventories, permits material corrections and
  truthful pending/failure updates, and publishes a consolidated description.
  Verification: walk through a new PR and an amendment from Luna's local
  return to the reviewed description, checking evidence reuse and truthful
  pending/failure reporting.
