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
applicable subordinate reviews finished for its named owner's review. Handoffs
identify the artifact and scope, reviewer, and stopping point. The owner waits
for that completed return, reviews its finished artifact even within an
unfinished Work, and does not inspect unfinished edits or interrupt subordinate
review. A bounded architecture or wiring review return awaits applicable owner
review before implementation continues.

An assignment return may be an intermediate artifact within one Work; it does
not mark Work criteria complete or mean that the Work is complete. Preserve
proportional optional progression, the Work's existing acceptance and planning
gates, and the maintainer's review, merge, and CI authority. This decision does
not add mandatory phase Works, agents, or maintainer gates.

## Consequences

Current assignment and review rules belong in
[executor guidance](../executor.md),
[orchestrator guidance](../orchestrator.md),
[architecture exploration](../architecture-exploration.md), and
[engineering guidance](../engineering.md#progressive-implementation). Work
acceptance remains owned by
[Work acceptance](../acceptance-tracing.md#criterion-status).
