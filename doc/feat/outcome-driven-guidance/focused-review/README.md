# Guide focused engineering review

## Purpose

Make focused review produce supported findings and bounded repair.

## Goals

- Keep individual rule judgments grounded in adequate context.
- Stop repair loops when further automatic corrections no longer help.

## Inherited constraints

Apply the [parent constraints](../README.md#inherited-constraints).

## Non-Goals

- Build an AST dispatcher, review skill, scripts, or a new review service.
- Mandate one reviewer agent per rule, phase, or function.

## Acceptance criteria

### **AC-1 DONE** A focused rule judgment has enough context

Engineering review guidance supports judgments of PASS, VIOLATION,
NOT_APPLICABLE, or UNCERTAIN for a named rule on the same immutable revision. A
reviewer receives the old and new function when relevant and enough
rule-specific caller, type, and module context to judge the change. Missing
context results in a stated uncertainty rather than an invented violation or
unsupported pass.

### **AC-2 TODO** Repair has a clear stopping rule

Review and handoff guidance make each autonomous repair round bounded and keep
its stopping conditions effective across revisions and recovery:

- Each autonomous repair round permits at most five correction requests; the
  cap is a fallback limit, not a target or a requirement to attempt five fixes.
- The correction-request count persists across changed revisions, session
  recovery, and ordinary orchestrator steering within the round.
- Recurrence, oscillation, conflicting rules, lack of progress, or a needed
  architectural change stops the round before the cap when it occurs earlier.
- When a round stops, the owner receives the attempts made, current revision,
  concrete evidence, and specific decision or help needed.
- Explicit maintainer direction may authorize another bounded repair round;
  a generic instruction to continue does not authorize unlimited retries.
- Changed revisions receive applicable fresh checks and independent review;
  earlier passing judgments do not silently cover new code.
- Bounded repair preserves scope and architecture constraints, whole-tree pause
  and planning gates, independent review, publication review, and final-head CI
  requirements.

### **AC-3 DONE** Supported findings inform whole-change judgment

Engineering review guidance makes findings usable for the responsible owner's
judgment of the broader outcome and architecture:

- Findings cite concrete evidence, explain the consequence, and remain separate
  from suggestions.
- The responsible owner deduplicates overlapping findings and judges conflicts
  and applicability.
- Architecture review assesses intent, ownership, and dependencies; engineering
  review assesses implementation quality.
- Focused rule review supports substantive whole-change judgment without a
  finding quota or mandatory refactoring.

## Dependencies

- DONE [Guide progressive delivery](../progressive-delivery/README.md): make a
  coherent outcome executable in small steps with honest evidence.

## Links

- [Engineering review](../../../engineering-review.md): focused engineering
  judgment owner.
- [Orchestrator](../../../orchestrator.md) and [executor](../../../executor.md):
  correction and escalation responsibilities.
