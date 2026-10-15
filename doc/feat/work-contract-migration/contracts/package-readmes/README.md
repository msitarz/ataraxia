# Rewrite package documentation contracts

## Purpose

Make the package documentation contracts readable through the new template
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

Preserve package coverage, API/navigation expectations, reusable-helper versus
per-test descriptions, existing operational notes, and the
planning-before-package-edit gates. The existing child map and serial shared
README ownership remain intact.

### **AC-2 TODO** Consistent dependencies and ownership

Parent maps, linked supporting artifacts, and active criterion/anchor references
agree with the rewritten contracts. Dependencies explain what is consumed and
when, separately from immediate children. References to retired acceptance tools
are removed from current instructions without rewriting historical records.

## Dependencies

- [Work contract template](../../../../work-contract-template.md):
  supplies the delivered authoring rules.
- **TODO** [Tooling simplification](../../tooling/README.md): removes marker
  coupling and establishes the retained declaration-check surface.

## Links

- [Package README coverage](../../../../feat/package-readmes/README.md).
- [Examples and final package navigation](../../../../feat/package-readmes/examples-navigation/README.md).
- [Lasting package documentation guidance](../../../../feat/package-readmes/guidance/README.md).
- [Make test package documentation](../../../../feat/package-readmes/make-tests/README.md).
- [Product package documentation](../../../../feat/package-readmes/product/README.md).
- [Product test package documentation](../../../../feat/package-readmes/product-tests/README.md).
- [Recent script test package documentation](../../../../feat/package-readmes/script-tests/README.md).
- [Repository script documentation](../../../../feat/package-readmes/scripts/README.md).
