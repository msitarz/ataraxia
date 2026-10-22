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

### **AC-2 DONE** Repair has a clear stopping rule

Review and handoff guidance bound correction work and reassess findings after
changes. A five-correction cap is a fallback limit rather than a requirement to
attempt five fixes. Recurrence, oscillation, conflicting rules, lack of
progress, or a needed architectural change stops the loop earlier and returns
concrete evidence and the decision needed to the owner. Changed revisions
receive applicable fresh checks and review; earlier passing judgments do not
silently cover new code.

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
