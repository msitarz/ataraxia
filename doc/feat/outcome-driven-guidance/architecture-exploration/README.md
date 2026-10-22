# Guide architecture exploration

## Purpose

Make uncertain decomposition resolvable through minimal typed architecture
exploration.

## Goals

- Keep useful vertical outcomes distinct from implementation modules.
- Make reviewed boundaries explicit while leaving private implementation
  flexible.

## Inherited constraints

Apply the [parent constraints](../README.md#inherited-constraints).

## Acceptance criteria

### **AC-1 TODO** Decomposition follows what is known about the outcome

Definition and orchestration guidance begin with one Work per coherent outcome
and assess decomposition as yes, no, or unknown. Unknown calls for the smallest
typed architecture exploration that answers the remaining question. Its findings
support retaining a leaf, splitting independently deliverable outcomes, or
investigating a stated uncertainty. Splitting preserves the exploration and its
rationale. A Work hierarchy need not match the module hierarchy, and a parent
composition map remains distinct from explicit scheduling dependencies.

The resulting guidance reconciles bounded exploration with existing split,
whole-tree pause, and planning-PR gates: it makes clear what exploration is
permitted while decomposition is unknown, when consequential design is reviewed
before implementation, and which approved-plan and maintainer gates apply to a
discovered split or scope change. Exploration does not silently authorize
expanded implementation or leave competing rules in force.

A compact parallel-shard illustration stays one leaf unless an isolated worker
is an independently useful outcome. Vertical children add behavior without
restating prior acceptance conditions; regression checks preserve earlier
behavior. The example does not approve or implement a parallel-shard feature.

### **AC-2 TODO** Typed architecture communicates its maturity and change boundary

Architecture guidance distinguishes exploratory types used to learn, reviewed
types expressing agreed boundaries, and implemented types backed by code and
observed behavior. Review of architecture asks whether intent, ownership,
invariants, dependencies, and effect limits fit the outcome. Reviewed boundaries
can change with explicit reviewed justification; private helpers and incidental
signatures remain flexible. Shared architecture is refined as vertical outcomes
are delivered rather than freezing every module and signature before
implementation.

Product architecture and workflow/tooling architecture keep their own context;
workflow tooling is not routed through unrelated product architecture.

Guidance covers any `.pyi` to `.py` transition: preserve the reviewed design,
recheck the conversion, and avoid duplicate interfaces that hide an unchecked
implementation. A static type check is evidence of the checked static contracts,
not runtime validation, purity, or delivered behavior.

## Dependencies

- TODO [Define outcome contracts](../outcome-contracts/README.md): let a Work
  express one outcome with verifiable acceptance conditions and inherited
  constraints.

## Links

- [Work definition](../../../work-definition.md),
  [Work workflow](../../../workflow.md), and
  [orchestrator guidance](../../../orchestrator.md): exploration and
  decomposition owners.
- [Engineering](../../../engineering.md) and
  [architecture](../../../architecture.md): typed boundaries and current
  architectural contracts.
