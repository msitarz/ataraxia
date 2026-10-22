# 34. Bound focused review corrections

Date: 2026-10-22

## Status

Accepted

Amends
[5. Review completed handoffs once](0005-review-completed-handoffs-once.md).

## Context

WDR 5 establishes consolidated review of completed handoffs and corrections.
Focused engineering findings also need enough rule-specific context to support
the responsible owner's judgment, and the correction loop needs an explicit
fallback cap and earlier stopping conditions. The
[focused review Work](../feat/outcome-driven-guidance/focused-review/README.md)
delivers the current guidance.

## Decision

Use optional focused judgments to support the responsible owner's substantive
review of the whole change:

- Judge a named engineering rule against one immutable revision and state
  `PASS`, `VIOLATION`, `NOT_APPLICABLE`, or `UNCERTAIN`.
- Use concrete evidence and explain each finding's consequence; keep
  suggestions separate from findings.
- Limit each autonomous repair round to at most five correction requests; five
  is a fallback cap, not a target. Count requests across revisions, session
  recovery, and ordinary orchestrator steering without resetting the count.
- Stop earlier for an unresolved or recurring finding, oscillation, conflicting
  rules, no progress, a needed architectural decision, or a session that cannot
  continue.
- Review changed revisions and rerun applicable checks; earlier judgments do
  not cover changed code.
- Ordinary orchestrator steering may resume an earlier-stopped round within its
  remaining budget and existing gates. Generic direction to continue does not
  authorize a new round, reset the count, or permit unlimited retries. Explicit
  maintainer direction may authorize one additional bounded round.
- Keep responsible-owner review, session recovery, whole-tree pause, planning,
  maintainer review and merge authority, and final-head CI gates in force.

## Consequences

[Engineering review](../engineering-review.md) owns focused judgments and
finding quality. [Orchestrator guidance](../orchestrator.md) owns correction
coordination and stopping. [Executor guidance](../executor.md) routes
corrections to that procedure. [WDR 10](0010-recover-delegated-handoffs.md)'s
recovery requirements remain in force; an architectural decision or new split
follows the existing whole-tree pause and planning gates.
