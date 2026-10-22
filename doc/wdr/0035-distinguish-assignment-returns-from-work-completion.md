# 35. Distinguish assignment returns from Work completion

Date: 2026-10-22

## Status

Accepted

Amends
[5. Review completed handoffs once](0005-review-completed-handoffs-once.md).

## Context

The phrase “completed artifact” can describe either a finished delegated scope
or a completed Work. These are different boundaries. A Work may benefit from
reviewed contract, architecture, or wiring artifacts before implementation is
complete, while its acceptance criteria and delivery remain governed by the
Work contract.

## Decision

Treat a completed delegated assignment return as the assigned scope and any
applicable subordinate reviews finished for its named reviewer's review.
Handoffs identify the artifact and scope, reviewer, and stopping point. The
owner waits for that completed return, reviews its finished artifact even
within an unfinished Work, and does not inspect unfinished edits or interrupt
subordinate review. An assignment to produce typed architecture or typed
wiring for selected review returns the artifact to its named reviewer; the
assignment does not conduct or complete that review. Implementation waits for
the named reviewer to complete the review when that is the stopping point.

An assignment return may be an intermediate artifact within one Work; it does
not by itself establish Work criterion status or mean that the Work is complete.
The owner marks a criterion `DONE` only after independent review verifies its
full condition from the artifact and evidence; the owner may do so even if the
Work continues. Preserve proportional optional progression, the Work's existing
acceptance and planning gates, and the maintainer's review, merge, and CI
authority. This decision does not add mandatory phase Works, agents, or
maintainer gates.

## Consequences

Current assignment and review rules belong in
[executor guidance](../executor.md),
[orchestrator guidance](../orchestrator.md),
[architecture exploration](../architecture-exploration.md), and
[engineering guidance](../engineering.md#progressive-implementation). Work
acceptance remains owned by
[Work acceptance](../acceptance-tracing.md#criterion-status). The
[Guide progressive delivery Work](../feat/outcome-driven-guidance/progressive-delivery/README.md)
and
[Guide architecture exploration Work](../feat/outcome-driven-guidance/architecture-exploration/README.md)
carry related context.
