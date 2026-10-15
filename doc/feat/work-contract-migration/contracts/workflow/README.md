# Rewrite workflow contracts

## Purpose

Make the workflow planning and trial contracts readable through the new template
without changing what their Works are authorized to deliver.

## Goals

- Give each criterion one coherent outcome and each contract a clear overview.
- Preserve local requirements, parent maps, and cross-Work dependencies.

## Non-Goals

- Implement the listed Works or resolve their pending decisions.
- Change historical evidence, approvals, or execution conditions.

## Acceptance criteria

### **AC-1 TODO** Readable contracts with preserved outcomes

Every scoped contract uses the template with focused outcomes and only useful
optional sections. Comparison with its pre-migration version accounts for all
required behavior, boundaries, and meaningful context. Substantive conditions
from Validation clauses become outcomes; generic execution instructions and
repetition are removed. Known uncertainty stays explicit rather than becoming
an invented contract or completion claim.

Preserve preparation-before-trial gates, frozen-condition requirements, and the
distinction between workflow evaluation and parallel-shard implementation.
Existing planning Works retain ownership of missing trial contracts and
thresholds; this rewrite does not supply unapproved choices.

### **AC-2 TODO** Consistent dependencies and ownership

Parent maps, linked live specifications, and active criterion/anchor references
agree with the rewritten contracts. Dependencies explain what is consumed and
when, separately from immediate children. References to retired acceptance tools
are removed from current instructions without rewriting historical records.

## Dependencies

- **TODO** [Guidance alignment](../../guidance/README.md): supplies authoring
  rules.
- **TODO** [Tooling simplification](../../tooling/README.md): removes marker
  coupling and establishes the retained declaration-check surface.

## Links

- [Reviewable workflow](../../../../feat/reviewable-workflow-v2/README.md).
- [Live trial](../../../../feat/reviewable-workflow-v2/live-trial/README.md).
- [Trial preparation](../../../../feat/reviewable-workflow-v2/trial-preparation/README.md).
- [Trial contract](../../../../feat/reviewable-workflow-v2/trial-preparation/trial-contract/README.md).
