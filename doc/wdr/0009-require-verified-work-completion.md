# 9. Require verified evidence for Work completion

Date: 2026-10-01

## Status

Accepted

Amends
[6. Keep delivery evidence in PRs and Git](0006-keep-delivery-evidence-in-prs-and-git.md).

Amended by
[11. Keep verification plans distinct from results](0011-keep-verification-plans-distinct-from-results.md).

## Context

Acceptance declarations describe intended coverage and verification methods,
but do not show that a criterion's outcome was observed. Work removal also
removes the contract that scopes those criteria. Existing guidance retained
evidence in PRs and Git without defining the evidence needed to mark each
criterion complete.

## Decision

Require observed, recorded outcomes for each criterion before marking it
`DONE` or removing its Work contract. For a Work PR with acceptance criteria,
keep the contract and verified outcomes in implementation/verification
commit(s), then remove the contract and update the parent map in a separate
final commit. Preserve both commits when merging so Git retains the evidence;
do not duplicate the criterion mapping in the PR description. The current
procedure belongs in [acceptance tracing](../acceptance-tracing.md); this
record preserves rationale and does not replace that guidance.

## Consequences

This requires at least two commits for a Work delivery: verified outcomes stay
with the contract before a later removal commit. Manual evidence must be
recorded beside its criterion; declarations, passing automated tests, and CI
alone do not establish a manual result. A later correction requires fresh
verification before removal. The merge must retain these commits, so the
delivery cannot be squashed. This avoids duplicate PR evidence at the cost of
preserving a separate removal boundary. See [Work lifecycle](../workflow.md),
[orchestrator handoffs](../orchestrator.md), and the
[completion-evidence Work](../feat/reviewable-workflow-v2/trial-preparation/README.md).
