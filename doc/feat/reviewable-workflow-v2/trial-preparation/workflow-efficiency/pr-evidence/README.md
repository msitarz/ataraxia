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

Define how evidence works when all criteria are covered by CI, when a criterion
requires manual judgment, and when the Work contract has been removed. This
Work depends on completion-evidence PR108 integration before changing an
evidence owner. Reconcile Proposed WDR9 through its applicable lifecycle;
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
  and Proposed WDR9's applicable lifecycle without rewriting accepted
  records.
  Verification: check `master` integration and inspect the
  resulting owner and decision-record history.
