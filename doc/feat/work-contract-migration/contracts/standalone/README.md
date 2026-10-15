# Rewrite standalone guidance contracts

## Purpose

Make the standalone guidance and investigation contracts readable through the
new template without changing what their Works are authorized to deliver.

## Goals

- Give each criterion one coherent outcome and each contract a clear overview.
- Preserve local requirements, parent maps, and cross-Work dependencies.

## Non-Goals

- Implement the listed Works or resolve their pending decisions.
- Change historical evidence, approvals, or execution conditions.

## Acceptance criteria

### **AC-1 DONE** Readable contracts with preserved outcomes

Every scoped contract uses the template with focused outcomes and only useful
optional sections. Comparison with its pre-migration version accounts for all
required behavior, boundaries, and meaningful context. Substantive conditions
from Validation clauses become outcomes; generic execution instructions and
repetition are removed. Known uncertainty stays explicit rather than becoming
an invented contract or completion claim.

Preserve the distinction between validated-core guidance adoption and the ADT
Investigation recommendation. Validated-core is already converted; review its
fit rather than rework it unnecessarily. Preserve representation candidates,
validation/resource-safety boundaries, and unresolved checker observations.

### **AC-2 DONE** Consistent dependencies and ownership

Parent maps, linked supporting artifacts, and active criterion/anchor references
agree with the rewritten contracts. Dependencies explain what is consumed and
when, separately from immediate children. References to retired acceptance tools
are removed from current instructions without rewriting historical records.

## Dependencies

- [Work contract template](../../../../work-contract-template.md):
  supplies the delivered authoring rules.
- **DONE** The completed
  [tooling simplification outcome](../../README.md#children) removed marker
  coupling and the declaration checker.

## Links

- [Algebraic data type investigation](../../../../feat/algebraic-data-types/README.md).
- [Validated models and pure core guidance](../../../../feat/validated-core/README.md).
