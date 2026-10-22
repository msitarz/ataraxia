# Guide progressive delivery

## Purpose

Make a coherent outcome executable in small steps with honest evidence.

## Goals

- Expose orchestration and effect ownership before completing all behavior.
- Align test intentions early and assess actual test quality when tests exist.

## Inherited constraints

Apply the [parent constraints](../README.md#inherited-constraints).

## Acceptance criteria

### **AC-1 TODO** A coherent outcome can become executable progressively

Engineering guidance supports progressing behavior and tests within one outcome.

- For broader outcomes, typed composition can express real sequencing and effect
  ownership before every leaf operation is complete.
- A [walking skeleton](../../../engineering.md#progressive-implementation) can
  execute a thin path through that composition with unfinished leaves stubbed.
- Engineering review inspects actual data flow and contract ownership,
  including dynamic graph mappings that static checks can miss.
- These techniques are optional, not mandatory stages, Works, or agent
  assignments; small changes can proceed directly to implementation and
  relevant tests.
- When decomposition is uncertain, follow the shared
  [architecture exploration guidance](../../../architecture-exploration.md)
  and its existing Work gates.

### **AC-2 TODO** Test intentions and delivered tests receive the right review

- Before implementation, test review may assess intended scenarios, observation
  boundaries, failure cases, inherited constraints, and needed evidence.
- Scenario names and short expected observations may become executable tests as
  behavior is implemented; a separate suite for each step is unnecessary.
- When tests exist, review their assertions for defect detection through the
  appropriate boundary, behavior preservation, and avoidance of bypasses.
- When adding behavior, preserve prior outcomes with regression checks; do not
  weaken expectations to match faulty implementation.
- Return a justified expectation change to contract and intent review.
- Acceptance requires observed results at the level claimed; intent review and
  pending placeholders cannot complete it.

### **AC-3 TODO** Evidence establishes only the confidence it supports

- Distinguish checked static contracts, executable composition, and delivered
  behavior as separate evidence.
- Type checking cannot establish runtime validation or purity.
- Stubs, placeholders, and unrun tests cannot establish passing acceptance
  evidence.

### **AC-4 TODO** Invariants and effects retain accountable owners

Engineering guidance places validation and effects at their owning boundaries:

- Raw ingress is validated, and construction or transitions establish new
  invariants where they are owned.
- Pure decisions trust established invariants; live authorization and resource
  checks stay with effects.
- Stateful runners may orchestrate pure decisions without themselves being
  pure.

## Dependencies

- DONE [Guide architecture exploration](../architecture-exploration/README.md):
  make uncertain decomposition resolvable through minimal typed architecture
  exploration.

## Links

- [Executor](../../../executor.md), [engineering](../../../engineering.md), and
  [testing](../../../testing.md): delivery and test owners.
- [Work acceptance](../../../acceptance-tracing.md) and
  [validation](../../../validation.md): evidence meaning and check selection.
