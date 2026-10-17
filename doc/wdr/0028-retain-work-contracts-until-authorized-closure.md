# 28. Retain Work contracts until authorized closure

Date: 2026-10-17

## Status

Accepted

Amended by
[29. Publish authorized Work closure on the reviewed PR](0029-publish-authorized-work-closure-on-the-reviewed-pr.md)
for incomplete closure and publication boundaries.

Amends
[2. Let parent maps track Work lifecycle](0002-let-parent-maps-track-work-lifecycle.md)
for contract-removal timing,
[9. Require verified evidence for Work completion](0009-require-verified-work-completion.md)
for the pre-publication cleanup sequence,
[21. Publish after local Work acceptance](0021-publish-after-local-work-acceptance.md)
and
[22. Deliver requested Work trees in one PR](0022-deliver-requested-work-trees-in-one-pr.md)
for requested and descendant contract retention,
[15. Use CI results as evidence of mechanical checks](0015-use-ci-results-as-evidence-of-mechanical-checks.md)
for pre-publication cleanup timing. Their requirements for observed acceptance,
independent review, latest-head CI, and maintainer merge remain in force.

## Context

Removing contracts before publication makes review corrections require
restoration and repeated deletion, while requested-tree delivery repeats those
operations across leaves and parents. Retention should continue through review
until the maintainer explicitly authorizes selected completed Works for closure
at a reviewed open PR head. The
[Work closure lifecycle](../feat/post-merge-work-closure/README.md) defines the
remaining deterministic reference and publication requirements separately; no
closure command or automatic closure is delivered by this decision.

## Decision

Retain requested Work and descendant contracts through implementation review,
corrections, and integration review until an explicit maintainer instruction in
the session authorizes closure of selected completed Works for a reviewed open
PR head. `DONE`, passing checks, ready-for-review status, and implementation or
PR-revision requests do not authorize closure. The instruction covers
mechanical closure changes on the same PR branch. Full CI must pass on the
final closure head before maintainer merge; maintainer acceptance, independent
review, and merge remain distinct responsibilities.

Substantive implementation corrections after approval invalidate authorization
for affected Works. If already closed, restore affected contracts and evidence,
refresh statuses and independent review, and obtain renewed closure instruction.
Before closure, update retained contracts and evidence directly; do not add
routine verification/removal pairs or a manual closure procedure. For a Work
abandoned with unsatisfied outcomes, record `ABORT` with the reason and do not
describe it as completed. This decision grants no direct-to-master or separate
closure PR authority and does not change post-merge branch/worktree cleanup
duties.

Current rules belong in [Work acceptance](../acceptance-tracing.md),
[Work workflow](../workflow.md), [orchestrator guidance](../orchestrator.md),
[contributor guidance](../../CONTRIBUTING.md), and
[pull-request guidance](../pull-requests.md). The
[authorized closure lifecycle Work](../feat/post-merge-work-closure/lifecycle/README.md)
carries the contract and remaining implementation criteria.

## Consequences

Contracts remain available through review until closure is explicitly
authorized, preserving their scope beside current acceptance evidence. The
closure tool, reference rules, and detailed publication authority require
their own reviewed acceptance and delivery; maintainer review, merge, and full
CI on the final closure head remain required.
