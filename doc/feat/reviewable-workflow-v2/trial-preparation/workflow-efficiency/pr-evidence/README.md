# PR evidence

Clarify completion evidence in the owning Work and validation guidance, with
the [completion-evidence Work](../../completion-evidence/README.md) and
[WDR lifecycle](../../../../../wdr-workflow.md) as applicable. Work owns
requirements; CI owns automated results. A PR adds the problem, result,
review attention, and evidence beyond CI. Do not impose fixed headings,
templates, or inventories of CI jobs, commands, and hooks.

Account for every acceptance criterion. Link to the original Work by a stable
PR diff or revision reference that remains usable after its directory is
removed; include a short result where needed instead of copying each full
criterion. Report material failures, pending or unrun checks, and manual
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
