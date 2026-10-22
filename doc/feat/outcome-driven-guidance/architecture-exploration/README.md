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

### **AC-1 DONE** Decomposition follows what is known about the outcome

Definition and orchestration guidance assess decomposition as yes, no, or
unknown, starting from one Work per coherent outcome. When decomposition is
unknown, the guidance requires the smallest typed architecture exploration that
answers the remaining question. Its findings can support:

- Retaining a leaf.
- Splitting independently deliverable outcomes.
- Investigating a stated uncertainty.

When a split occurs, preserve the exploration and its rationale. A Work
hierarchy need not match the module hierarchy. A parent composition map remains
distinct from explicit scheduling dependencies.

The guidance explains bounded exploration alongside existing split, whole-tree
pause, and planning-PR gates. It identifies permitted exploration while
decomposition is unknown, when consequential design is reviewed before
implementation, and which approved-plan and maintainer gates apply to a
discovered split or scope change. Exploration does not authorize expanded
implementation or leave competing rules in force.

A compact parallel-shard illustration stays one leaf unless an isolated worker
is an independently useful outcome. Vertical children add behavior without
restating prior acceptance conditions; regression checks preserve earlier
behavior. The example does not approve or implement a parallel-shard feature.

### **AC-2 DONE** Typed architecture communicates its current maturity and evolution

Architecture guidance distinguishes three type states:

- Exploratory types used to learn.
- Reviewed types that express agreed boundaries.
- Implemented types backed by code and observed behavior.

Architecture review asks whether intent, ownership, invariants, dependencies,
and effect limits fit the outcome. Reviewed boundaries can change with explicit
reviewed justification; private helpers and incidental signatures remain
flexible. Shared architecture is refined as vertical outcomes are delivered
rather than freezing every module and signature before implementation.

When later children change shared architecture, the current architectural view
reflects the reviewed change. Retained exploration and superseded designs carry
lightweight status or explanation that clarifies their relationship to the
current view. Retaining history does not leave competing live definitions.
Retained design may be stored or labeled separately outside active module
resolution under the [parent constraints](../README.md#inherited-constraints).

### **AC-3 DONE** Architectural context matches the affected system

Product architecture and workflow/tooling architecture keep their own context;
workflow tooling is not routed through unrelated product architecture.

### **AC-4 DONE** Stub conversion preserves reviewed design and exposes implementation

Guidance covers any `.pyi` to `.py` transition and requires it to:

- Preserve the reviewed design.
- Recheck the conversion.
- Avoid duplicate interfaces that hide an unchecked implementation.
- Follow AC-2 when retaining the prior design, without keeping a shadowing
  `.pyi` in active module resolution.

A static type check is evidence of the checked static contracts. It does not
establish runtime validation, purity, or delivered behavior.

## Dependencies

- DONE [Define outcome contracts](../outcome-contracts/README.md): let a Work
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
