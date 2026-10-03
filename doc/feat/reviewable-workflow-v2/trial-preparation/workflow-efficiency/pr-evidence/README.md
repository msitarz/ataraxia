# PR evidence

Clarify concise PR descriptions under the permanent
[PR owner](../../../../../pull-requests.md) and preserve inspectable Work
contracts under [acceptance tracing](../../../../../acceptance-tracing.md).
The [workflow-efficiency parent map](../README.md#works) tracks this outcome.

The owning orchestrator prepares new and amended descriptions after independent
review and corrections, using the reviewed artifact and the executor's concise
local result. Consolidate publication while permitting material corrections;
there is no separate executor PR-writing phase. Follow the current Purpose,
Outcome, and Limitations template. Keep evidence links, evidence prose,
acceptance criteria, and check inventories out of descriptions. Do not add PR
comments or discussion to record review or report checks. Mechanical checks are
evidenced by passing full CI on the latest reviewed PR head.

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

Preserve reviewable original criteria after Work removal. This Work depends on
completion-evidence PR108 integration before changing an evidence owner.
Reconcile applicable WDR proposals through their lifecycle and preserve accepted
records without rewriting them.

## Acceptance

- **AC-2 DONE** Original criteria remain reviewable through stable PR or
  revision references after Work removal, with concise outcome context where
  necessary and no wholesale copying requirement.
  Validation: remove a
  sample Work directory in a review scenario and follow its references.
- **AC-3 DONE** The owner change follows integrated completion-evidence PR108
  and reconciles applicable WDRs through their lifecycle, preserving accepted
  history.
  Validation: check `master` integration and inspect the
  resulting owner and decision-record history.
- **AC-4 DONE** The WDR and shared-record owners distinguish an adoption-ready
  decision PR from a proposal-only or Investigation case, including intended
  `Accepted` state on merge, maintainer acceptance through merge, and the rule
  that Work type alone does not set status. The index and reciprocal amendment
  or supersession metadata are consistent in the same PR, without follow-up.
  Validation: review an adoption-ready PR after merge and a proposal-only or
  Investigation case, checking record status, index, reciprocal metadata, and
  the relevant owner guidance.

## Abandoned scope

AC-1: ABORT. Evidence guidance accounts for all criteria, reports failures,
  pending, unrun, and manual limitations, and gives the three cases above
  usable treatment in PR records without redundant description inventories.
  Validation: walk through a CI-only Work, a manual criterion, and a
  removed Work contract using a completed PR.

Reason: the maintainer rejected diagnostic and failure-reporting obligations
and review-record prose; mechanical checks are covered by CI.

AC-5: ABORT. PR-description ownership stays with the owning orchestrator
  after review for both a new PR and an existing-PR amendment, with no separate
  executor PR-writing phase. It uses the executor's concise local result to
  prepare a consolidated description, permits material corrections and truthful
  pending/failure updates, and keeps evidence in PR commits, CI records, and
  review records without description links or copied evidence/check inventories.
  Validation: walk through a new PR and an amendment from the executor's local
  return to the reviewed description, checking template use, evidence location,
  and truthful pending/failure reporting.

Reason: the maintainer rejected review records and pending/failure reporting.
The surviving description ownership instructions remain required scope above.

AC-6: ABORT. The original requirement called for a new template with only
Change and Limitations sections, itemized content, and matching published
Work PR descriptions. The maintainer explicitly abandoned this requirement
and retained the current Purpose, Outcome, and Limitations template.
