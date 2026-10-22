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

Executor and engineering guidance support conditional typed architecture
exploration, typed wiring, an executable thin walking skeleton, progressive
behavioral tests and implementation, and engineering review within one outcome.
Typed wiring contains real sequencing and effect ownership while leaf operations
may be stubbed. The walking skeleton executes a representative thin path, using
fake adapters when appropriate. Review inspects actual data flow as well as
ownership and contract meaning, including dynamic graph mappings that static
checks can miss. These are useful progression choices, not mandatory separate
Works or agent assignments. Shared architecture evolves under
[architecture maturity guidance](../architecture-exploration/README.md#ac-2-done-typed-architecture-communicates-its-current-maturity-and-evolution).

### **AC-2 TODO** Test intentions and delivered tests receive the right review

Testing guidance lets early review assess intended behaviors, observation
boundaries, failure cases, inherited constraints, and the kind of evidence
needed. Scenario names and one-sentence expected observations may progressively
become the same executable tests without a new suite for each step. Once tests
exist, review assesses whether their real assertions detect the named defects
through the appropriate boundary, preserve prior outcomes, and avoid replacing
the behavior under test. Acceptance continues to require observed results at the
level claimed; reviewing test intentions alone cannot complete it, and pending
placeholder tests cannot pass completion. Implementation preserves reviewed
behavioral expectations rather than weakening them to match faulty code;
justified changes return to contract and intent review.

### **AC-3 TODO** Evidence establishes only the confidence it supports

Delivery and acceptance guidance distinguish static contract checks, executable
wiring evidence, and evidence of completed behavior. Stubs, placeholders, and
unrun tests cannot establish passing acceptance evidence. Type checking cannot
establish runtime validation or purity.

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
