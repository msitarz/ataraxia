# 17. Review local artifacts before PR publication

Date: 2026-10-03

## Status

Accepted

Amends
[5. Review completed handoffs once](0005-review-completed-handoffs-once.md).

Amended by
[21. Publish after local Work acceptance](0021-publish-after-local-work-acceptance.md).

## Context

WDR 5 uses a draft PR to signal executor completion. Current
[PR guidance](../pull-requests.md#descriptions) instead assigns local artifact
review and publication to the owning orchestrator. The
[workflow-efficiency Work](../feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/README.md)
reconciles this history with the current ownership boundary.

## Decision

Replace only WDR 5's draft-PR phase with a local executor return. The owning
orchestrator reviews the completed artifact and any corrections before
publishing a ready PR or an amendment to an existing PR. Keep publication
procedure in [PR guidance](../pull-requests.md#descriptions).

WDR 5's completed-result review, consolidated corrections, evidence reuse,
and maintainer review and merge gates remain in force, alongside its existing
model amendment.

## Consequences

Independent review happens before publication, without a draft-PR transition.
The local return retains the artifact, evidence, and blockers for review.
Ready requests maintainer review and may precede completed CI; it does not
establish approval or merge.
