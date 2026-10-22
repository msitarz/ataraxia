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

- Judge a named engineering rule against one immutable revision and state
  `PASS`, `VIOLATION`, `NOT_APPLICABLE`, or `UNCERTAIN`.
- Use concrete evidence and explain each finding's consequence; keep
  suggestions separate from findings.
- Bound correction work to five requests for a reviewed change, with earlier
  stops for recurrence, oscillation, conflicting rules, no progress, or a
  needed architectural decision.
- Review changed revisions and rerun applicable checks; earlier judgments do
  not cover changed code.
- Keep responsible-owner review, session recovery, whole-tree pause, planning,
  maintainer review and merge authority, and final-head CI gates in force.

## Consequences

[Engineering review](../engineering-review.md) owns focused judgments and
finding quality. [Orchestrator guidance](../orchestrator.md) owns correction
coordination and stopping. [Executor guidance](../executor.md) routes
corrections to that procedure. WDR 10's recovery requirements remain in force;
an architectural decision or new split follows the existing whole-tree pause
and planning gates.
