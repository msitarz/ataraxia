# Architecture exploration

Read when exploring or reviewing architecture to resolve uncertain Work
decomposition, or when retaining a superseded architecture design.

## Maturity

Architecture has three useful maturity states:

- **Exploratory** types and diagrams are tools for learning. They may be
  incomplete or discarded and do not authorize implementation beyond the
  bounded question.
- **Reviewed** types and diagrams express an agreed boundary and its
  responsibilities. They guide implementation, while remaining open to a
  reviewed change when new evidence or a later outcome justifies it.
- **Implemented** architecture is supported by code and observed behavior.
  Update the current architectural view to describe implemented behavior and
  label planned or exploratory behavior clearly.

Exploration follows the existing Work gates. When decomposition is unknown,
keep it bounded to the question within the current outcome. If it reveals
independently deliverable outcomes or a material scope change, use the
[whole-tree pause and planning gates](workflow.md#decisions-and-new-splits).
Exploration can resolve uncertainty; it cannot authorize expanded feature
implementation. Consequential design is reviewed before implementation.

## Review a boundary

Review architecture for the outcome it supports. Check that the design makes
clear:

- The intent and responsibility of each boundary.
- The invariants each boundary must preserve.
- The direction of dependencies and which layer owns composition.
- The effects a boundary may perform, including I/O and resource lifecycle.
- Which properties are established by static checks and which require runtime
  or delivered-behavior evidence.

Agree on the boundary and its guarantees, not every private helper or
incidental signature. Refine shared architecture as vertical outcomes are
delivered; do not freeze every module and signature before implementation.

For example, parallel shard processing might use a strategy coordinator that
submits independent shard jobs to workers and collects their results. Keep it
one leaf when the useful outcome is parallel backtesting as a whole. Split out
an isolated worker only when it is independently useful and deliverable. This
illustration does not approve a parallel-shard feature.

## Keep one current view

The relevant current architecture document describes the reviewed current
design and implemented behavior. When a later outcome changes a shared
boundary, update that view and explain the implemented or planned status.
Retain useful exploratory findings and superseded designs with a short status
or explanation linking them to the current view. Retained history must not
create a second live definition or an interface shadowing the active one.

Product architecture belongs in [Architecture](architecture.md). Architecture
of repository workflow or development tooling belongs with its workflow or
tooling owner. Use the context whose behavior is being changed.

For `.pyi` conversion, follow the
[engineering rule](engineering.md#code-style) and keep the reviewed design
traceable without a duplicate active interface.
