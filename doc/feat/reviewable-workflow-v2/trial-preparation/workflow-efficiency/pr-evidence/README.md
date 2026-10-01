# PR evidence

Clarify completion evidence in the
[completion-evidence owner](../../../../../acceptance-tracing.md) and
[contributor PR guidance](../../../../../../CONTRIBUTING.md#work-branches-review-and-merge).
The trial-preparation map tracks the outcome;
[PR 108](https://github.com/msitarz/ataraxia/pull/108) is the integration
prerequisite before changing the owner. Work owns requirements; CI owns
automated results. A PR adds the problem, result, review attention, and evidence
beyond CI. Avoid fixed headings, templates, and inventories of CI jobs,
commands, or hooks.

Account for every acceptance criterion. Link to the original Work by a stable
PR diff or revision reference that remains usable after its directory is
removed; include short result context where needed instead of copying each
full criterion. Avoid routine successful-check inventories; retain concise
material diagnostics and report failures, pending or unrun checks, and manual
limitations accurately. Do not remove evidence as a blanket rule.

Update WDR status guidance in the [WDR workflow](../../../../../wdr-workflow.md)
and [shared decision-record format](../../../../../decision-records.md), not
in this Work. For a PR that adopts a workflow decision, specify `Accepted` as
the intended merged state. Readiness alone does not assert prior maintainer
approval; acceptance occurs through merge. Ship the matching index entry and
any reciprocal amendment or supersession metadata in that same PR. Use
`Proposed` for an unsettled proposal or an Investigation recommendation when
its merge does not adopt the decision. Work type alone does not determine
status; a ready Investigation PR adopts a decision only if it explicitly does
so.

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
  and applies the WDR lifecycle status distinction above: an adoption-ready
  PR targets `Accepted` on merge, while proposal-only and Investigation cases
  remain `Proposed` when merge does not adopt the decision. The matching index
  and reciprocal amendment or supersession metadata ship in that PR; accepted
  history is preserved.
  Verification: check `master` integration and inspect the
  resulting owner and decision-record history.
- **AC-4 TODO** The WDR and shared-record owners distinguish an adoption-ready
  decision PR from an unsettled proposal or Investigation recommendation, and
  explain that Work type alone does not set status.
  Verification: inspect both updated owners and walk through an adoption PR
  and a proposal-only or Investigation case.
- **AC-5 TODO** Adoption-ready delivery includes matching index and reciprocal
  amendment or supersession metadata in the same PR, with the intended
  post-merge state consistent and no follow-up PR required.
  Verification: review a merged decision PR, its index, and reciprocal record
  metadata together.
