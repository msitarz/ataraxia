# 28. Retain Work contracts through merge

Date: 2026-10-17

## Status

Accepted

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
operations across leaves and parents. The
[post-merge Work closure lifecycle](../feat/post-merge-work-closure/README.md)
defines the future closure command separately; its command and publication
authority are not delivered by this decision.

## Decision

Retain requested Work and descendant contracts through implementation review,
corrections, integration review, and maintainer merge. Update criterion status
and source evidence directly as reviewed outcomes change. Independent review
remains the basis for `DONE`; maintainer acceptance and merge remain distinct,
and full CI on the latest reviewed PR head remains required before merge.

Until a supported post-merge closure procedure is delivered, keep merged
contracts available and do not add manual deletion or reference-update loops.
For a Work abandoned with unsatisfied outcomes, record `ABORT` with the reason,
do not describe it as completed, and retain its contract until supported closure
is available.
This decision grants no direct-to-master publication authority and does not
change post-merge branch/worktree cleanup duties.

Current rules belong in [Work acceptance](../acceptance-tracing.md),
[Work workflow](../workflow.md), [orchestrator guidance](../orchestrator.md),
[contributor guidance](../../CONTRIBUTING.md), and
[pull-request guidance](../pull-requests.md). The
[post-merge lifecycle Work](../feat/post-merge-work-closure/lifecycle/README.md)
carries the contract and remaining implementation criteria.

## Consequences

Contracts remain available throughout review and correction, preserving their
scope beside current acceptance evidence. Completed merged contracts remain in
the active tree until supported closure is available. The future closure tool
and any authority it needs require their own reviewed acceptance and delivery;
maintainer review, merge, and latest-head CI gates remain unchanged.
