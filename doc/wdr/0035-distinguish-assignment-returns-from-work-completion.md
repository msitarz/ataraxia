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

- A completed assignment return means the assigned scope and applicable
  subordinate reviews are finished for the named reviewer's review.
- Handoffs identify the artifact and scope, reviewer, and stopping point.
- The owner waits for the completed return and reviews its finished artifact,
  including within an unfinished Work.
- The owner does not inspect unfinished edits or interrupt subordinate review.
- An assignment to produce typed architecture or typed wiring for selected
  review returns the artifact to its named reviewer; the assignment does not
  conduct or complete that review.
- Implementation waits for the named reviewer to complete the review when that
  is the stopping point.
- An assignment return may be an intermediate artifact within one Work. It
  does not by itself establish criterion status or Work completion.
- The owner marks a criterion `DONE` only after independent review verifies its
  full condition from the artifact and evidence. The owner may do so while the
  Work continues.
- Preserve proportional optional progression, the Work's existing acceptance
  and planning gates, and the maintainer's review, merge, and CI authority.
- This decision adds no mandatory phase Works, agents, or maintainer gates.

## Consequences

Current assignment and review rules belong in
[executor guidance](../executor.md),
[orchestrator guidance](../orchestrator.md),
[architecture exploration](../architecture-exploration.md), and
[engineering guidance](../engineering.md#progressive-implementation). Work
acceptance remains owned by
[Work acceptance](../acceptance-tracing.md#criterion-status). The
[Guide progressive delivery Work](https://github.com/msitarz/ataraxia/blob/b703fa815a28f338fc2e69918a8351a455afb39e/doc/feat/outcome-driven-guidance/progressive-delivery/README.md)
and
[Guide architecture exploration Work](https://github.com/msitarz/ataraxia/blob/b703fa815a28f338fc2e69918a8351a455afb39e/doc/feat/outcome-driven-guidance/architecture-exploration/README.md)
carry related context.
